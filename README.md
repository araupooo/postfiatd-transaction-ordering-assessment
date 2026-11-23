# Deterministic Transaction Ordering in postfiatd

## Verdict

**Queue candidates order by fee level first, then by a pseudo-randomised transaction-ID tie-break; sequence consecutiveness, a strictly-greater-than-1.25x replacement threshold, LastLedgerSequence queueability/inclusion/eviction boundaries, and per-account-average queue-full eviction constrain which transactions can be ordered at all. The candidate order (fee first) and the canonical apply order (salted account, sequence, txID) are different orders for different stages and must not be conflated. Where XRPL docs disagree with the code, this pack follows the code: fee escalation is quadratic (not exponential), the dispute avalanche ladder is 50/65/70/95 (not 50/60/...), and this fork validates at a 67% quorum (not upstream XRPL's 80%).**

## Key numbers (SOURCE-DERIVED from the pinned tree — no live node was run)

- Pinned source: postfiatd `0085a1ff885d6a446369cf73a4430f75af22be55`.
- 38 ordering rules catalogued (R-01..R-33 VERIFIED, R-34 SPECIFIED, R-35/R-36 MODELLED, R-37/R-38 UNTESTABLE).
- 8 scripted scenarios, 46 synthetic transactions: admitted 27, duplicate 1, not queueable 2, expired 1, replaced 1, rejected duplicate 2, blocked by sequence gap 2, cap rejected 0, evicted 4, deferred 6. (Recomputed by `run-manifest.json` from the simulator output; see `outputs/derived/ordering-results.json`.)
- Candidate order: feeLevel descending, then (txID XOR parentHash) ascending (`src/xrpld/app/misc/TxQ.h:656-658`).
- Fee escalation is quadratic: required level = multiplier x current^2 / target^2 above txnsExpected (`src/xrpld/app/misc/detail/TxQ.cpp:173-195`).
- Replacement: same-SeqProxy replacement needs fee level STRICTLY greater than old x 1.25 (`src/xrpld/app/misc/detail/TxQ.cpp:913`).
- LastLedgerSequence is inclusive at preclaim (`src/xrpld/app/tx/detail/Transactor.cpp:571-573`) but queue eviction uses <= at close and queueing needs LLS >= submit + 2.
- Per-account queue cap: 10 transactions; queue-full eviction is per-account-average with the victim the cheapest-average account's last transaction.
- Canonical apply order: salted account key, then SeqProxy, then txID (`src/xrpld/app/misc/CanonicalTXSet.cpp:28-44`).
- Quorum in this fork: 67% (`src/xrpld/app/misc/detail/ValidatorList.cpp:1898-1900`); dispute avalanche 50/65/70/95.
- Probe: 12/12 checks PASS (rule anchors, arithmetic, OrderCandidates re-grep, key tokens at recorded lines, CanonicalTXSet order, count reconciliation, determinism, excerpt + blob integrity, quadratic escalation, 67% quorum, timing sanity).
- Excerpts: 61 verbatim pinned-source excerpts, 25 source files, blob SHAs + sizes re-checked against the checkout.

## Counts

- Findings: 12 (HIGH 3, MEDIUM 5, LOW 4).
- Claims: 24 (VERIFIED 16, SPECIFIED 2, MODELLED 4, UNTESTABLE 2).
- Risks: 14 (HIGH 3, MEDIUM 8, LOW 3).
- Gaps: 8.

## Boundary

No live node was run and no transaction was submitted. The simulator models the cited rules on scripted, synthetic loads; every scenario outcome is a model output, not an observed network result. Live fee levels, queue depth, txnsExpected, and escalation values (R-37) and per-round dispute outcomes (R-38) are UNTESTABLE from source alone. Amendment activation timing, batch-transaction ordering, and the deployed network's quorum choice (67% vs 80%) are stated as limits in `docs/citations.md`. Simulated/modelled material is separated from directly-observed source facts in `docs/methodology.md`.

## Reproduce

```bash
python3 src/ordering_model.py               # simulator -> outputs/derived/ordering-results.json + scenario-matrix.json
python3 scripts/probe.py                   # 12 probe checks, exit 0 only if all pass
python3 scripts/extract_excerpts.py        # verbatim pinned-source excerpts + hashes
bash scripts/run_all.sh                    # full suite end to end
bash scripts/clean_reproduce.sh            # full fresh-environment check
bash scripts/verify_digests.sh             # sha256sum -c SHA256SUMS
```

Only deterministic source parsing and simulation runs. No live node, no submitted transactions, no votes, no live key material, no credentials anywhere in the pack.

## CI run

CI run URL: https://github.com/araupooo/postfiatd-transaction-ordering-assessment/actions/runs/45241107006 (verify workflow on final HEAD 7c0332c5d9fc329e2249e22b1f234580880da5e8, job "verify" success, all 9 steps success).

## Fresh-clone reproduction log

Fresh-clone repro log SHA-256: 3d10f77dc9ed375c8c2b767175c05de891388b4d34920320047cf65f687e5574 (`outputs/fresh-clone-run.log`, 10 lines; byte-identical to `outputs/run.log`).

## File map

- `README.md` — this file.
- `findings.json` — 12 findings with severity, status, evidence.
- `run-manifest.json` — pinned commit, counts recomputed from the tables.
- `docs/` — decision memo, scenario matrix, methodology, claim-to-evidence index, excerpts, citations, evidence index, risk register, gap register.
- `src/ordering_model.py` — stdlib-only deterministic ordering simulator (rules R-01..R-33).
- `scripts/` — simulator runner, probe, excerpts, reproduce, compare, digests.
- `configs/ordering-rules.json` — the 38-rule catalog; `configs/scenarios.json` — the 8 scripted scenarios.
- `fixtures/source-excerpts/` — 61 verbatim pinned-source excerpts with file paths and grep-verified line numbers.
- `fixtures/source-hashes.json` — SHA-256 digests and git blob SHAs for every cited source file.
- `outputs/` — unedited simulator/probe logs, derived JSONs, fresh-clone reproduction evidence.
- `SHA256SUMS` — digests of every pack file except itself and the internal-only `PACK-READY.md`.
