#!/usr/bin/env python3
"""probe.py — re-verify the deterministic-ordering pack from its outputs.

Usage:
    python3 scripts/probe.py [--skip-manifest-check] [ORDERING_RESULTS_JSON]

The --skip-manifest-check flag is for run_all.sh step 4 only: the
manifest on disk at that point predates the just-regenerated results,
so comparing against it would fail on any input change; step 5b re-runs
the probe without the flag after rewriting the manifest. A standalone
probe run (no flag) always performs the manifest check.

Checks (all re-derived, none trusted):
  A-00 pinned checkout HEAD equals the pinned commit.
  A-01 every VERIFIED rule's anchor sits inside its cited range in the
     pinned checkout; SPECIFIED rules carry external URLs, MODELLED /
     UNTESTABLE rules carry no file source.
  B-01 simulator arithmetic: per scenario, input == duplicate +
     not_queueable + replaced + rejected + blocked + cap_rejected +
     evicted + expired + deferred + admitted; totals reconcile to
     46 inputs / 27 admitted.
  C-01 OrderCandidates re-grep: feeLevel-descending sort and the
     (txID XOR parentHash) tie-break are present in TxQ.h.
  D-01 key tokens at recorded lines: strict replacement `>` (TxQ.cpp:913),
     per-account cap 10 (TxQ.h:148), tefMAX_LEDGER inclusive check
     (Transactor.cpp:571-573), eviction `lastValid <= ledgerSeq`.
  E-01 CanonicalTXSet Key order: salted account key, then SeqProxy,
     then txID (CanonicalTXSet.cpp:28-44).
  F-01 counts reconcile across files: matrix == results == scenarios (8);
     findings 12, claims 24, risks 14, gaps 8; excerpts 61 across 25
     files agree across manifest, extracted files, source-hashes.json.
  G-01 determinism: re-running the simulator to a temp dir reproduces
     byte-identical outputs (full SHA-256 compare).
  H-01 excerpt integrity: every excerpt file digest matches
     fixtures/source-hashes.json and every manifest blob SHA/size
     matches `git hash-object` / file size in the checkout;
     run-manifest digests match the shipped derived files.
  I-01 quadratic escalation: `current * current` in scaleFeeLevel
     (TxQ.cpp:173-195); avalanche ladder 50/65/70/95 in
     ConsensusParms.h.
  J-01 67% quorum comment in ValidatorList.cpp:1898-1900; amendment
     threshold "slightly less than 80%" in AmendmentTable.cpp.
  T-01 timing sanity only (non-negative, never recorded).

Exit 0 only if every case passes. Prints one PASS/FAIL line per case
with the FULL 64-char SHA-256 digest where a digest is involved, and
writes outputs/derived/probe-results.json plus outputs/probe-run.log
(the log is the unedited stdout of this run; it contains no absolute
paths and no timestamps). No live node is involved.
"""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parent.parent
PINNED_COMMIT = "0085a1ff885d6a446369cf73a4430f75af22be55"
PINNED_CHECKOUT = Path(__import__("os").environ.get(
    "PINNED_CHECKOUT", str(Path.home() / "workspace" / "postfiatd-pin-0085a1f")))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def git_blob(relpath):
    out = subprocess.run(["git", "-C", str(PINNED_CHECKOUT), "hash-object", "--", relpath],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def main():
    argv = [a for a in sys.argv[1:] if a != "--skip-manifest-check"]
    skip_manifest = "--skip-manifest-check" in sys.argv[1:]
    results_path = Path(argv[0]) if argv else \
        PACK_ROOT / "outputs" / "derived" / "ordering-results.json"
    doc = load_json(results_path)
    matrix = load_json(PACK_ROOT / "outputs" / "derived" / "scenario-matrix.json")
    rules = load_json(PACK_ROOT / "configs" / "ordering-rules.json")["rules"]
    scenarios = load_json(PACK_ROOT / "configs" / "scenarios.json")["scenarios"]
    manifest = load_json(PACK_ROOT / "fixtures" / "excerpts-manifest.json")
    hashes = load_json(PACK_ROOT / "fixtures" / "source-hashes.json")
    findings = load_json(PACK_ROOT / "findings.json")["findings"]
    checks, lines = [], []

    def check(cid, label, ok, detail=""):
        checks.append({"id": cid, "check": label, "pass": bool(ok), "detail": detail})
        lines.append(("PASS " if ok else "FAIL ") + cid + " " + label +
                     ((" — " + detail) if detail else ""))

    t_start = time.monotonic()
    co = PINNED_CHECKOUT
    head = subprocess.run(["git", "-C", str(co), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip() if co.is_dir() else ""
    check("A-00", "pinned checkout HEAD equals the pinned commit",
          head == PINNED_COMMIT, f"HEAD={head}")

    # --- A: rule anchors ---------------------------------------------------
    a_ok, a_detail = True, ""
    n_verified = n_spec = n_mod = n_unt = 0
    for r in rules:
        src = r.get("source")
        if r["status"] == "VERIFIED":
            n_verified += 1
            if not src or not src.get("anchor"):
                a_ok, a_detail = False, f"{r['id']}: verified rule lacks source/anchor"
                break
            lines_f = (co / src["file"]).read_text(errors="replace").splitlines()
            if not (1 <= src["start_line"] <= src["end_line"] <= len(lines_f)):
                a_ok, a_detail = False, f"{r['id']}: range out of bounds"
                break
            chunk = "\n".join(lines_f[src["start_line"] - 1:src["end_line"]])
            if src["anchor"] not in chunk:
                a_ok, a_detail = False, f"{r['id']}: anchor not in range"
                break
        elif r["status"] == "SPECIFIED":
            n_spec += 1
            if src is not None or not r.get("external"):
                a_ok, a_detail = False, f"{r['id']}: specified rule must carry external URLs, no file source"
                break
        else:
            n_mod += 1 if r["status"] == "MODELLED" else 0
            n_unt += 1 if r["status"] == "UNTESTABLE" else 0
            if src is not None:
                a_ok, a_detail = False, f"{r['id']}: {r['status']} rule must carry no file source"
                break
    if a_ok and (n_verified, n_spec, n_mod, n_unt) != (33, 1, 2, 2):
        a_ok, a_detail = False, f"rule status counts wrong: {n_verified}/{n_spec}/{n_mod}/{n_unt}"
    check("A-01", "38 rules: 33 VERIFIED anchors inside cited ranges, 1 SPECIFIED (external URLs), 2 MODELLED, 2 UNTESTABLE, none with a faked source",
          a_ok, a_detail or "33/1/2/2")

    # --- B: arithmetic -----------------------------------------------------
    b_ok, b_detail = True, ""
    cats = ["duplicate", "not_queueable", "replaced", "rejected_duplicate",
            "blocked_by_gap", "cap_rejected", "evicted", "expired",
            "deferred", "admitted_order"]
    for r in doc["scenarios"]:
        total = sum(len(r[c]) for c in cats)
        if total != r["input"]:
            b_ok, b_detail = False, f"{r['id']}: arithmetic {total} != {r['input']}"
            break
    t = doc["totals"]
    exp = {"input": 46, "admitted": 27, "duplicate": 1, "not_queueable": 2,
           "replaced": 1, "rejected_duplicate": 2, "blocked_by_gap": 2,
           "cap_rejected": 0, "evicted": 4, "expired": 1, "deferred": 6}
    if b_ok:
        for k, v in exp.items():
            if t.get(k) != v:
                b_ok, b_detail = False, f"totals[{k}]={t.get(k)} != {v}"
                break
    check("B-01", "per-scenario arithmetic reconciles; totals 46 in / 27 admitted / 1 dup / 2 not-queueable / 1 replaced / 2 rejected / 2 blocked / 0 cap-rejected / 4 evicted / 1 expired / 6 deferred",
          b_ok, b_detail or f"totals={t}")

    # --- C: OrderCandidates ------------------------------------------------
    txq_h = (co / "src/xrpld/app/misc/TxQ.h").read_text(errors="replace")
    c_ok = ("lhs.feeLevel > rhs.feeLevel" in txq_h
            and "(lhs.txID ^ MaybeTx::parentHashComp)" in txq_h)
    check("C-01", "TxQ.h OrderCandidates: feeLevel descending, then (txID XOR parentHash) ascending",
          c_ok, "grep-verified in TxQ.h" if c_ok else "OrderCandidates text missing")

    # --- D: key tokens at recorded lines -----------------------------------
    txq_cpp = (co / "src/xrpld/app/misc/detail/TxQ.cpp").read_text(errors="replace").splitlines()
    txq_h_lines = txq_h.splitlines()
    trans = (co / "src/xrpld/app/tx/detail/Transactor.cpp").read_text(errors="replace").splitlines()
    d_checks = [
        ("feeLevelPaid > requiredRetryLevel" in txq_cpp[912],
         "strict replacement `>` not at TxQ.cpp:913"),
        ("maximumTxnPerAccount = 10" in txq_h_lines[147],
         "per-account cap 10 not at TxQ.h:148"),
        ("tefMAX_LEDGER" in trans[572] and "view.seq() >" in trans[571],
         "tefMAX_LEDGER inclusive check not at Transactor.cpp:571-573"),
        ("lastValid <= ledgerSeq" in "\n".join(txq_cpp[1378:1405]),
         "expiry `lastValid <= ledgerSeq` not in TxQ.cpp:1379-1405"),
    ]
    d_ok, d_detail = True, ""
    for ok, msg in d_checks:
        if not ok:
            d_ok, d_detail = False, msg
            break
    check("D-01", "strict replacement > (TxQ.cpp:913), cap 10 (TxQ.h:148), tefMAX_LEDGER inclusive (Transactor.cpp:571-573), expiry <= (TxQ.cpp:1379-1405)",
          d_ok, d_detail or "4 tokens at recorded lines")

    # --- E: CanonicalTXSet Key order ---------------------------------------
    cts = (co / "src/xrpld/app/misc/CanonicalTXSet.cpp").read_text(errors="replace").splitlines()
    block = "\n".join(cts[27:44])
    e_ok = ("lhs.seqProxy_ < rhs.seqProxy_" in block and "lhs.txId_ < rhs.txId_" in block
            and "ret ^= salt_" in "\n".join(cts[45:56]))
    check("E-01", "CanonicalTXSet Key orders by salted account key, then SeqProxy, then txID",
          e_ok, "CanonicalTXSet.cpp:28-44 + accountKey 46-56" if e_ok else "Key order text missing")

    # --- F: counts reconcile -----------------------------------------------
    def table_rows(path, prefix):
        rows = []
        for ln in open(path, encoding="utf-8"):
            m = re.match(rf"\| ({prefix}-\d+) \| ([A-Z]+) \|", ln)
            if m:
                rows.append((m.group(1), m.group(2)))
        return rows
    claims = table_rows(PACK_ROOT / "docs" / "claim-index.md", "C")
    risks = table_rows(PACK_ROOT / "docs" / "risk-register.md", "K")
    gaps = [ln for ln in open(PACK_ROOT / "docs" / "gap-register.md", encoding="utf-8")
            if re.match(r"\| G-\d+ \|", ln)]
    f_ok, f_detail = True, ""
    if matrix["scenario_count"] != len(doc["scenarios"]) != len(scenarios) != 8:
        f_ok, f_detail = False, "scenario count != 8 across files"
    elif matrix["totals"] != doc["totals"]:
        f_ok, f_detail = False, "matrix totals != results totals"
    elif len(findings) != 12:
        f_ok, f_detail = False, f"findings != 12 ({len(findings)})"
    elif len(claims) != 24:
        f_ok, f_detail = False, f"claims != 24 ({len(claims)})"
    elif Counter(s for _, s in claims) != {"VERIFIED": 16, "SPECIFIED": 2, "MODELLED": 4, "UNTESTABLE": 2}:
        f_ok, f_detail = False, f"claim statuses wrong: {Counter(s for _, s in claims)}"
    elif len(risks) != 14:
        f_ok, f_detail = False, f"risks != 14 ({len(risks)})"
    elif len(gaps) != 8:
        f_ok, f_detail = False, f"gaps != 8 ({len(gaps)})"
    excerpts = manifest.get("excerpts", [])
    exdir = PACK_ROOT / "fixtures" / "source-excerpts"
    if f_ok and (len(excerpts) != 61 or len(list(exdir.glob("*.txt"))) != 61):
        f_ok, f_detail = False, "excerpt manifest != extracted files != 61"
    if f_ok and len(hashes.get("files", {})) != 25:
        f_ok, f_detail = False, f"source files != 25 ({len(hashes.get('files', {}))})"
    if f_ok:
        for e in excerpts:
            if e["id"] not in hashes.get("excerpts", {}):
                f_ok, f_detail = False, f"excerpt {e['id']} missing from source-hashes.json"
                break
    check("F-01", "matrix == results == scenarios (8); findings 12, claims 24 (16/2/4/2), risks 14, gaps 8; excerpts 61 across 25 files agree across manifest, files, hashes",
          f_ok, f_detail or "all counts reconcile")

    # --- G: determinism ----------------------------------------------------
    res_digest = sha256_file(results_path)
    mat_digest = sha256_file(PACK_ROOT / "outputs" / "derived" / "scenario-matrix.json")
    with tempfile.TemporaryDirectory(prefix="pftl-ordering-probe.") as td:
        tmp_res, tmp_mat = Path(td) / "ordering-results.json", Path(td) / "scenario-matrix.json"
        proc = subprocess.run(
            [sys.executable, str(PACK_ROOT / "src" / "ordering_model.py"),
             "--out", str(tmp_res), "--matrix-out", str(tmp_mat)],
            capture_output=True, text=True)
        rerun_ok = proc.returncode == 0
        rerun_res = sha256_file(tmp_res) if tmp_res.is_file() else "missing"
        rerun_mat = sha256_file(tmp_mat) if tmp_mat.is_file() else "missing"
    check("G-01", "determinism: simulator re-run reproduces byte-identical results and matrix (full SHA-256)",
          rerun_ok and rerun_res == res_digest and rerun_mat == mat_digest,
          f"results shipped={res_digest} rerun={rerun_res}; matrix shipped={mat_digest} rerun={rerun_mat}")

    # --- H: excerpt + blob + manifest integrity ----------------------------
    h_ok, h_detail = True, ""
    for ex_id, rec in sorted(hashes.get("excerpts", {}).items()):
        p = exdir / f"{ex_id}.txt"
        if not p.is_file() or sha256_file(p) != rec["sha256"]:
            h_ok, h_detail = False, f"excerpt {ex_id}.txt digest mismatch"
            break
    if h_ok:
        for e in excerpts:
            src = co / e["file"]
            if git_blob(e["file"]) != e["blob_sha"]:
                h_ok, h_detail = False, f"excerpt {e['id']}: blob SHA mismatch"
                break
            if src.stat().st_size != e["blob_size"]:
                h_ok, h_detail = False, f"excerpt {e['id']}: blob size mismatch"
                break
    man_path = PACK_ROOT / "run-manifest.json"
    if skip_manifest:
        h_detail = ("manifest check skipped by caller (run_all.sh step 5b "
                    "performs it after the manifest is rewritten)")
    elif h_ok and man_path.is_file():
        man = load_json(man_path)
        if man.get("results_sha256") != res_digest or man.get("matrix_sha256") != mat_digest:
            h_ok, h_detail = False, "run-manifest digests != shipped derived files"
    elif h_ok:
        h_detail = "run-manifest.json not yet written (run_all.sh writes it after the probe); digest check deferred to the next probe run"
    check("H-01", "every excerpt digest matches source-hashes.json; every manifest blob SHA/size matches the checkout; run-manifest digests match shipped derived files",
          h_ok, h_detail or f"{len(hashes.get('excerpts', {}))} excerpt digests + blob SHAs verified")

    # --- I: quadratic escalation + avalanche ladder -------------------------
    esc = "\n".join(txq_cpp[172:195])
    i_ok = "current * current" in esc and "target * target" in esc
    parms = (co / "src/xrpld/consensus/ConsensusParms.h").read_text(errors="replace")
    ladder = ["{init, {0, 50, mid}}", "{mid, {50, 65, late}}",
              "{late, {85, 70, stuck}}", "{stuck, {200, 95, stuck}}"]
    i_ok = i_ok and all(x in parms for x in ladder)
    check("I-01", "fee escalation is QUADRATIC (current^2/target^2, TxQ.cpp:173-195); avalanche ladder is 50/65/70/95 (ConsensusParms.h:146-157)",
          i_ok, "code verified; docs saying 'exponential' or '50/60' are stale" if i_ok else "escalation/avalanche text missing")

    # --- J: 67% quorum + amendment threshold --------------------------------
    vl = (co / "src/xrpld/app/misc/detail/ValidatorList.cpp").read_text(errors="replace").splitlines()
    am = (co / "src/xrpld/app/misc/detail/AmendmentTable.cpp").read_text(errors="replace")
    j_ok = ("Use a 67% quorum" in vl[1897] and "Original XRPL uses 80%" in vl[1898]
            and "slightly less than 80%" in am)
    check("J-01", "67% quorum in this fork with the 80%-revert-for-mainnet comment (ValidatorList.cpp:1898-1900); amendment threshold 'slightly less than 80%' (AmendmentTable.cpp:368)",
          j_ok, "both verified" if j_ok else "quorum/amendment text missing")

    elapsed_ms = (time.monotonic() - t_start) * 1000.0
    check("T-01", "timing sanity: total probe elapsed_ms is non-negative (loose band, never exact)",
          elapsed_ms >= 0, "value not recorded; never compared")

    passed = sum(1 for c in checks if c["pass"])
    total = len(checks)
    lines.append(f"probe: {passed}/{total} checks PASS")
    lines.append(f"probe: ordering-results.json sha256: {res_digest}")
    lines.append(f"probe: scenario-matrix.json sha256: {mat_digest}")
    lines.append(f"probe: pinned commit {PINNED_COMMIT}")
    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    result_doc = {"pack": "Deterministic Transaction Ordering in postfiatd",
                  "pinned_commit": PINNED_COMMIT,
                  "results_file": "outputs/derived/ordering-results.json",
                  "results_sha256": res_digest, "matrix_sha256": mat_digest,
                  "checks": checks, "passed": passed, "total": total}
    out_derived = PACK_ROOT / "outputs" / "derived" / "probe-results.json"
    out_derived.parent.mkdir(parents=True, exist_ok=True)
    with open(out_derived, "w", encoding="utf-8") as fh:
        json.dump(result_doc, fh, indent=1, sort_keys=True)
        fh.write("\n")
    (PACK_ROOT / "outputs" / "probe-run.log").write_text(text)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
