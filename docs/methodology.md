# Methodology

## Pinned source

postfiatd commit `0085a1ff885d6a446369cf73a4430f75af22be55` (repo `postfiatorg/postfiatd`). A local checkout at `~/workspace/postfiatd-pin-0085a1f` was verified with `git rev-parse HEAD` before any excerpt was taken. Every line number in this pack was verified with `grep -n` on that checkout; no line number was taken from a web fetch. `scripts/extract_excerpts.py` re-derives all 61 excerpts from the checkout and records SHA-256 digests plus git blob SHAs in `fixtures/source-hashes.json` (25 source files); `scripts/probe.py` re-checks every manifest blob SHA and size against `git hash-object` and the checkout file size.

## Where the code wins over the docs

- **Fee escalation is quadratic, not exponential.** `scaleFeeLevel` returns `multiplier x current^2 / target^2` once the open ledger passes `txnsExpected` (TxQ.cpp:173-195, E09). XRPL docs describe the growth loosely as 'exponential'; the pack follows the code.
- **The dispute avalanche ladder is 50/65/70/95.** `ConsensusParms.h:146-157` (E38) gives init 50%, mid 65%, late 70%, stuck 95%. Some XRPL docs quote 50/60/...; the pack follows the code.
- **The quorum is 67% in this fork, not upstream XRPL's 80%.** `ValidatorList.cpp:1898-1900` (E44) states a 67% quorum for devnet/testnet with a comment that mainnet should revert to 80%. Whether any deployed PostFiat network actually runs 67% or 80% is a deployment fact, not a code fact, and was not verified.

## Simulator model (`src/ordering_model.py`, stdlib only, deterministic)

The engine implements rules R-01..R-33 in pipeline order: (0) exact-duplicate detection by tx id (R-23); (1) queueability, LLS >= submit seq + 2 (R-13); (2) replacement, STRICTLY greater than 1.25x (R-11, `4 * new > 5 * old`); (3) per-account sequence consecutiveness, first gap blocks later sequences, tickets bypass the chain (R-08/R-21); (4) per-account cap of 10, extras rejected (R-10); (5) queue-full eviction by per-account average fee, victim is the cheapest-average account's last transaction (R-31, applied as a batch — MODELLED, C-21); (6) closing-ledger fill by feeLevel descending then (txID XOR parentHash) ascending, stopping at the first candidate below the required level (R-01/R-02/R-07), with LLS < closing seq excluded from inclusion (R-14); (7) close: non-admitted candidates with LLS <= closing seq expire, the rest defer (R-13/R-14); (8) canonical order of the admitted set (R-15/R-35, MODELLED application).

Scenario parameters that the code cannot supply are labelled as parameters, not derived values: the required fee level, `txnsExpected`, the escalation multiplier, and the queue cap are scenario inputs (R-37: live values are unknowable from source alone). The quadratic escalation formula (R-03) is verified in code; its live inputs are not.

## What is simulated, specified, or directly observed

- **DIRECTLY OBSERVED (source-derived)** — rules R-01..R-33: each carries a cited file range and an anchor re-verified inside that range by `scripts/probe.py` (A-01), plus token-level checks (D-01), the OrderCandidates re-grep (C-01), the CanonicalTXSet order (E-01), the quadratic-escalation and avalanche checks (I-01), and the quorum/amendment checks (J-01).
- **SPECIFIED** — R-34 (validated = quorum on the same hash), stated from protocol docs (negative-unl page, XRPL intro course); the upstream 80% figure is a doc statement, not a pinned-code fact.
- **SIMULATED / MODELLED** — every scenario outcome; R-35 (canonical order is the sole application order); R-36 (queue order is never agreed directly); the batch form of R-31 eviction (C-21); the S-08 rejoin sequence (C-22); ticket-hole sizes (G-01). The simulator is a model of the cited rules, not a run of postfiatd: no live node was run, no transaction was submitted, no consensus round was observed.
- **UNTESTABLE in this pack** — live fee levels, queue depth, `txnsExpected`, escalation multiplier (R-37); per-round dispute outcomes (R-38); batch-transaction ordering (`featureBatch` unsupported, G-06); the deployed network's quorum choice (67% vs 80%).

## Two orders, not one

The queue candidate order (fee first, TxQ.h OrderCandidates) and the canonical apply order (salted account key, then SeqProxy, then txID, CanonicalTXSet.cpp:28-44) are different orders for different stages. This pack models the candidate order and reports the canonical order of each admitted set separately; the two must not be conflated (K-04, K-08).

## The LastLedgerSequence boundary, stated once

Preclaim compares against the OPEN ledger seq (`view.seq() > LLS` fails, Transactor.cpp:571-573), so LLS = N is still includable in ledger N. Queue eviction compares against the CLOSED ledger seq (`lastValid <= ledgerSeq`, TxQ.cpp:1379-1388), so the same transaction is evicted once ledger N closes if it did not get in. Admission compares against the SUBMIT ledger seq (`LLS >= submit + 2`, TxQ.cpp:384-410). Three comparisons, three ledger indices — a simulator using one comparison for all three is wrong (F-03, K-03).

## Determinism

Re-runs produce byte-identical outputs: sorted keys and rows, no timestamps, no absolute paths, no elapsed times in any deterministic output. Timing is sanity-checked (non-negative) in `probe.py` and never recorded. `scripts/compare_reproduce.py` deep-compares a fresh run against the shipped outputs ignoring only volatile fields.
