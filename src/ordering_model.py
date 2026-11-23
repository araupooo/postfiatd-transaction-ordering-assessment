#!/usr/bin/env python3
"""ordering_model.py — deterministic transaction-ordering simulator.

Usage:
    python3 src/ordering_model.py [--out PATH] [--matrix-out PATH] [--help]
    PINNED_CHECKOUT=<path>  (default ~/workspace/postfiatd-pin-0085a1f)

The engine implements the pack's ordering model, rules R-01..R-33 from
configs/ordering-rules.json (each VERIFIED against the pinned checkout;
see docs/methodology.md for the simulated-vs-observed separation), in
this pipeline order per scenario:

  0  duplicate detection (R-23): an exact resubmission (same tx id)
     is a no-op duplicate; a different payload at the same sequence
     is NOT a duplicate.
  1  queueability (R-13): a transaction is refused at admission unless
     LastLedgerSequence >= submit ledger seq + 2 (minimumLastLedgerBuffer).
  2  replacement (R-11): same-account same-sequence replacement succeeds
     only when the new fee level is STRICTLY greater than 1.25x the old
     (integer arithmetic: 4 * new > 5 * old). Exactly +25% is rejected.
  3  sequence consecutiveness (R-08/R-21): only the consecutive run from
     the account's start sequence is eligible; the first gap blocks every
     later sequence-based transaction for that account. Ticket
     transactions bypass the sequence chain.
  4  per-account cap (R-10): at most 10 queued per account; extras (the
     highest sequences) are rejected at admission (gap-fill exception
     not exercised — see docs/gap-register.md G-01).
  5  queue-full eviction (R-31, batch approximation — MODELLED): while
     the queue exceeds the scenario's max_queue_size, the victim is the
     cheapest-average-fee account's LAST (highest-sequence) transaction.
     Eviction is per-account-average, NOT global-lowest-fee.
  6  closing-ledger fill (R-01/R-02/R-07): candidates sort by feeLevel
     descending, then (txID XOR parentHash) ascending; the fill STOPS at
     the first candidate below the scenario's required_fee_level
     (break, not skip), and at the scenario's max_txns_per_ledger.
     A transaction whose LastLedgerSequence < the closing ledger seq
     cannot be included (R-14: inclusion needs view.seq() <= LLS).
  7  close (R-13/R-14): non-admitted candidates with LLS <= closing seq
     are expired (evicted); the rest are deferred. Note the boundary:
     LLS == closing seq is still includable (R-14 inclusive) but is
     expired if it does not get in.
  8  canonical order (R-15/R-35, MODELLED application): admitted
     transactions in salted-account, then SeqProxy, then txID order.

Rules R-34 (SPECIFIED), R-35/R-36 (MODELLED) and R-37/R-38 (UNTESTABLE)
are not engine rules; S-07/S-08 record their model outputs and label
them. The escalation multiplier, txnsExpected and live fee levels are
scenario parameters (R-37: unknowable from source alone), NOT computed
by the engine — the quadratic escalation formula itself (R-03) is
verified in code but its live inputs are not.

Inputs: configs/scenarios.json (scripted, synthetic transaction loads —
model inputs, not observed network traffic). Outputs are deterministic:
sorted keys, no timestamps, no absolute paths, no measured timings.
Exit 0 only if every scenario reconciles
(input == duplicate + not_queueable + replaced + rejected_duplicate +
blocked_by_gap + cap_rejected + evicted + expired + deferred + admitted).

The script refuses to run if the pinned checkout exists and its HEAD
differs from the pinned commit; if no checkout is present it runs on
the recorded model alone and says so (the probe re-checks the checkout
when it is available).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parent.parent
PINNED_COMMIT = "0085a1ff885d6a446369cf73a4430f75af22be55"
PINNED_CHECKOUT = Path(os.environ.get(
    "PINNED_CHECKOUT", str(Path.home() / "workspace" / "postfiatd-pin-0085a1f")))
PARENT_SEED = "postfiatd-ordering-pack-parent"
PER_ACCOUNT_CAP = 10
MIN_LAST_LEDGER_BUFFER = 2


def parent_hash(seed=PARENT_SEED):
    return hashlib.sha256(seed.encode()).hexdigest()


def tie_key(tx_id, ph):
    return int(tx_id, 16) ^ int(ph, 16)


def canonical_order(admitted_txs, ph):
    """R-15/R-35: salted account key, then SeqProxy, then txID.
    Salt = sha256 of the agreed tx-set hash (here: the sorted admitted
    ids); account key = sha256(account + salt). MODELLED application of
    the verified Key order."""
    salt = hashlib.sha256(",".join(sorted(t["id"] for t in admitted_txs)).encode()).hexdigest()
    def key(t):
        acct = int(hashlib.sha256((t["account"] + ":" + salt).encode()).hexdigest(), 16)
        proxy = t.get("ticket", t["sequence"])
        return (acct, proxy, int(t["id"], 16))
    return [t["id"] for t in sorted(admitted_txs, key=key)]


def run_scenario(sc, ph, _top=True):
    ledger_seq = sc["ledger_seq"]
    required = sc["required_fee_level"]
    cap = sc["max_txns_per_ledger"]
    max_queue = sc["max_queue_size"]
    starts = sc["account_start_sequence"]
    txs = [dict(t) for t in sc["transactions"]]
    n_in = len(txs)
    duplicate, not_queueable = [], []
    replaced, rejected = [], []
    blocked, cap_rejected, evicted = [], [], []
    expired, deferred, admitted = [], [], []

    # --- 0: exact duplicates (R-23) ---------------------------------------
    seen, live = set(), []
    for t in txs:
        if t["id"] in seen:
            duplicate.append(t["id"])
        else:
            seen.add(t["id"])
            live.append(t)
    # --- 1: queueability (R-13) -------------------------------------------
    q = []
    for t in live:
        lls = t.get("last_ledger_sequence")
        submit = t.get("submit_ledger_seq", ledger_seq)
        if lls is not None and lls < submit + MIN_LAST_LEDGER_BUFFER:
            not_queueable.append(t["id"])
        else:
            q.append(t)
    # --- 2: replacement, STRICTLY > 1.25x (R-11) ---------------------------
    by_seq = {}
    for t in q:
        key = (t["account"], t["sequence"])
        if key in by_seq:
            old = by_seq[key]
            if 4 * t["fee_level"] > 5 * old["fee_level"]:
                replaced.append(old["id"])
                by_seq[key] = t
            else:
                rejected.append(t["id"])
        else:
            by_seq[key] = t
    live = list(by_seq.values())
    # --- 3: sequence consecutiveness (R-08/R-21) ---------------------------
    eligible = []
    per_acct = {}
    for t in live:
        per_acct.setdefault(t["account"], []).append(t)
    for acct, ats in per_acct.items():
        seq_txs = sorted((t for t in ats if "ticket" not in t),
                         key=lambda t: t["sequence"])
        expect = starts[acct]
        for t in seq_txs:
            if t["sequence"] == expect:
                eligible.append(t)
                expect += 1
            elif t["sequence"] > expect:
                blocked.append(t["id"])
        eligible.extend(t for t in ats if "ticket" in t)
    # --- 4: per-account cap 10 (R-10) --------------------------------------
    per_acct_el = {}
    for t in eligible:
        per_acct_el.setdefault(t["account"], []).append(t)
    kept = []
    for acct, ats in per_acct_el.items():
        if len(ats) > PER_ACCOUNT_CAP:
            ranked = sorted(ats, key=lambda t: t["sequence"])
            cap_rejected.extend(t["id"] for t in ranked[PER_ACCOUNT_CAP:])
            kept.extend(ranked[:PER_ACCOUNT_CAP])
        else:
            kept.extend(ats)
    # --- 5: queue-full eviction, per-account average (R-31, MODELLED batch) -
    while len(kept) > max_queue:
        avgs = {}
        for t in kept:
            avgs.setdefault(t["account"], []).append(t["fee_level"])
        victim_acct = min(avgs, key=lambda a: (sum(avgs[a]) / len(avgs[a]), a))
        victims = [t for t in kept if t["account"] == victim_acct]
        victim = max(victims, key=lambda t: (t["sequence"], t["id"]))
        evicted.append(victim["id"])
        kept.remove(victim)
    # --- 6: closing-ledger fill (R-01/R-02/R-07/R-14) ----------------------
    ordered = sorted(kept, key=lambda t: (-t["fee_level"], tie_key(t["id"], ph)))
    admitted_txs = []
    for t in ordered:
        if len(admitted_txs) >= cap:
            break
        lls = t.get("last_ledger_sequence")
        if lls is not None and lls < ledger_seq:
            expired.append(t["id"])
            continue
        if t["fee_level"] < required:
            break  # R-07: stop, do not skip
        admitted_txs.append(t)
    admitted = [t["id"] for t in admitted_txs]
    # --- 7: close (R-13/R-14) ----------------------------------------------
    for t in ordered:
        if t["id"] in admitted or t["id"] in expired:
            continue
        lls = t.get("last_ledger_sequence")
        if lls is not None and lls <= ledger_seq:
            expired.append(t["id"])
        else:
            deferred.append(t["id"])
    # direct-apply eligibility (R-06, informational): fee >= required and
    # SeqProxy is the account sequence (or a ticket).
    direct = [t["id"] for t in admitted_txs
              if t["fee_level"] >= required and
              ("ticket" in t or t["sequence"] == starts[t["account"]])]
    assert len(duplicate) + len(not_queueable) + len(replaced) + len(rejected) \
        + len(blocked) + len(cap_rejected) + len(evicted) + len(expired) \
        + len(deferred) + len(admitted) == n_in, "scenario arithmetic broke"
    res = {
        "id": sc["id"], "title": sc["title"],
        "input": n_in, "duplicate": sorted(duplicate),
        "not_queueable": sorted(not_queueable),
        "replaced": sorted(replaced), "rejected_duplicate": sorted(rejected),
        "blocked_by_gap": sorted(blocked), "cap_rejected": sorted(cap_rejected),
        "evicted": sorted(evicted), "expired": sorted(expired),
        "deferred": sorted(deferred), "admitted_order": admitted,
        "canonical_order": canonical_order(admitted_txs, ph),
        "direct_apply_eligible": sorted(direct),
    }
    if sc["id"] == "S-07" and _top:
        vote = sc["amendment_vote_pct"]
        res["amendment_check"] = {
            "vote_pct": vote, "threshold": "strictly greater than 80%",
            "activates": vote > 80.0,
            "amendments": sc["amendments"],
            "modelled_note": ("R-30: no amendment in the pinned tree changes "
                              "the TxQ fee order or the canonical order."),
        }
    if sc["id"] == "S-08" and _top:
        alt = {}
        for label in sc["partition_parent_hashes"]:
            alt_ph = hashlib.sha256(label.encode()).hexdigest()
            alt[label] = run_scenario(sc, alt_ph, _top=False)["admitted_order"]
        br = sc["branches"]
        pref = None
        for name, b in br.items():
            if name == "uncommitted":
                continue
            rival = sum(v["support"] for k, v in br.items()
                        if k not in ("uncommitted", name))
            if b["support"] > rival + br["uncommitted"]:
                pref = name
        res["partition_orders"] = alt
        res["partition_diverges"] = len({tuple(v) for v in alt.values()}) > 1
        res["rejoin"] = {
            "preferred_branch": pref,
            "rule": ("R-27: a branch is preferred only if its support exceeds "
                     "the rival branch support PLUS all uncommitted support."),
            "local_tx_reproposed": sorted(
                t["id"] for t in sc["transactions"] if t.get("local")),
            "losing_branch_open_tx_reproposed": [],
            "modelled_note": ("S-08 rejoin sequence is MODELLED: InboundLedgers "
                              "acquisition order was not traced (G-02)."),
        }
    return res


def main():
    ap = argparse.ArgumentParser(description="Deterministic transaction-ordering simulator.")
    ap.add_argument("--out", default=str(PACK_ROOT / "outputs" / "derived" / "ordering-results.json"))
    ap.add_argument("--matrix-out", default=str(PACK_ROOT / "outputs" / "derived" / "scenario-matrix.json"))
    args = ap.parse_args()
    checkout_ok = False
    if PINNED_CHECKOUT.is_dir():
        head = subprocess.run(["git", "-C", str(PINNED_CHECKOUT), "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        if head != PINNED_COMMIT:
            print(f"ordering_model: ERROR: pinned checkout HEAD {head} != {PINNED_COMMIT}",
                  file=sys.stderr)
            return 1
        checkout_ok = True
    else:
        print("ordering_model: no pinned checkout found; running on the recorded model alone")
    ph = parent_hash()
    scenarios = json.load(open(PACK_ROOT / "configs" / "scenarios.json"))["scenarios"]
    results = [run_scenario(sc, ph) for sc in scenarios]
    keys = ["duplicate", "not_queueable", "replaced", "rejected_duplicate",
            "blocked_by_gap", "cap_rejected", "evicted", "expired", "deferred"]
    totals = {"scenarios": len(results),
              "input": sum(r["input"] for r in results),
              "admitted": sum(len(r["admitted_order"]) for r in results)}
    for k in keys:
        totals[k] = sum(len(r[k]) for r in results)
    doc = {"pack": "Deterministic Transaction Ordering in postfiatd",
           "pinned_commit": PINNED_COMMIT,
           "pinned_checkout_verified": checkout_ok,
           "parent_hash": ph, "parent_hash_seed": PARENT_SEED,
           "per_account_cap": PER_ACCOUNT_CAP,
           "minimum_last_ledger_buffer": MIN_LAST_LEDGER_BUFFER,
           "replacement_minimum": "strictly greater than 1.25x fee level",
           "scenarios": results, "totals": totals}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
        fh.write("\n")
    matrix = {"pack": "Deterministic Transaction Ordering in postfiatd",
              "pinned_commit": PINNED_COMMIT,
              "scenario_count": len(results),
              "rows": [{"id": r["id"], "title": r["title"], "input": r["input"],
                        "duplicate": len(r["duplicate"]),
                        "not_queueable": len(r["not_queueable"]),
                        "replaced": len(r["replaced"]),
                        "rejected_duplicate": len(r["rejected_duplicate"]),
                        "blocked_by_gap": len(r["blocked_by_gap"]),
                        "cap_rejected": len(r["cap_rejected"]),
                        "evicted": len(r["evicted"]),
                        "expired": len(r["expired"]),
                        "deferred": len(r["deferred"]),
                        "admitted": len(r["admitted_order"])} for r in results],
              "totals": totals}
    mout = Path(args.matrix_out)
    mout.parent.mkdir(parents=True, exist_ok=True)
    with open(mout, "w") as fh:
        json.dump(matrix, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(f"ordering_model: {len(results)} scenarios, "
          f"input={totals['input']} admitted={totals['admitted']} "
          f"expired={totals['expired']} blocked={totals['blocked_by_gap']} "
          f"evicted={totals['evicted']} (parent_hash={ph})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
