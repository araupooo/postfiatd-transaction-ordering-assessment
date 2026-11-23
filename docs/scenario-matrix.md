# Scenario matrix

Scripted, synthetic transaction loads (model inputs, not observed network traffic). Each scenario is run by `src/ordering_model.py`; per-scenario outcomes live in `outputs/derived/ordering-results.json` and the count table in `outputs/derived/scenario-matrix.json`.

| ID | Title | Input txs | Question |
| --- | --- | --- | --- |
| S-01 | Fee-spike reordering | 6 | Does a late-arriving high-fee transaction jump ahead of earlier low-fee transactions, and does the queue drain halt (not skip) at the first transaction below the rising required level? |
| S-02 | Duplicate / equivocating transactions | 6 | Is an exact resubmission a no-op duplicate, is a different payload at the same sequence a replacement candidate, and does exactly +25% fail replacement (strictly greater required)? |
| S-03 | Sequence-number gaps | 5 | Does a missing sequence number block every later sequence-based transaction for that account, while a ticket-based transaction is unaffected? |
| S-04 | LastLedgerSequence expiry races | 6 | Is LastLedgerSequence inclusive (a transaction may still be included in the ledger whose seq equals its LLS), is queueing refused when LLS < submit seq + 2, and is a queued transaction evicted once its LLS has gone by? |
| S-05 | Queue eviction under memory pressure | 12 | When the queue is full, is admission decided by per-account average fee (not global lowest fee), with the victim being the cheapest-average account's last (highest-sequence) transaction? |
| S-06 | Multi-account same-sequence races | 5 | Do transactions from different accounts with the same sequence number never conflict (sequence is per-account), with cross-account application order given by the salted-account canonical order? |
| S-07 | Amendment-flagged ordering changes | 2 | Does any amendment in the pinned tree change the TxQ fee order or the canonical order, and does an 80.0%-exactly vote activate an amendment under the post-fix strictly-greater rule? |
| S-08 | Partition-rejoin ordering divergence | 4 | Can two validators with different parent hashes order the same equal-fee transactions differently, which branch does a rejoining node prefer, and which transactions are re-proposed on rejoin? |

Counts: 8 scenarios, 46 input transactions.

## Per-scenario outcomes (from the simulator run)

- S-01 fee-spike: required level 512; only the 5120-fee transaction is admitted — the fill stops at the first transaction below the required level (300), the other 5 are deferred, not skipped past.
- S-02 duplicates: the exact resubmission is a no-op duplicate; the 1.30x replacement succeeds; the exactly-+25% (512 -> 640) and below-threshold (512 -> 563) replacements are rejected and the original kept.
- S-03 gaps: sequences 13 and 14 are blocked by the missing sequence 12; the ticket-based transaction is admitted despite the gap.
- S-04 expiry: LLS 102 and 150 queueable and admitted/deferred; LLS 100 is admitted into ledger 100 (inclusive boundary); LLS 99 expires at the close; LLS 100 submitted at ledger 99 and LLS 101 submitted at ledger 100 are refused at admission (LLS < submit + 2).
- S-05 eviction: 12 transactions, queue cap 8 — the 4 evicted are the low-average account's last (highest-sequence) transactions; the high-average account loses none.
- S-06 multi-account: same-sequence transactions from three accounts never conflict; admitted order is the queue order, canonical order is reported separately.
- S-07 amendment: no amendment changes the ordering rules; the 80.0% vote does NOT activate (strictly-greater rule).
- S-08 partition: the same load under two different parent hashes produces different equal-fee orders; branch A (support 70) is preferred over B (20) with 5 uncommitted; local transactions are re-proposed, losing-branch open-ledger transactions are not.

## Scenario grounds (assume vs MODELLED)

- **S-01**: Grounding: R-03 (quadratic escalation), R-04 (median-fee multiplier), R-07 (accept halts, does not skip), R-01 (fee order). Simulator may assume a transaction priced out mid-ledger as current^2 grows. MODELLED: the exact fee at which a given transaction gets in during a spike (depends on arrival interleaving — R-37); the spike does NOT reorder already-queued transactions, it only gates their release.
- **S-02**: Grounding: R-23 (hash dedup), R-24 (same seq, different payload — first wins, later tefPAST_SEQ; queue treats it as a replacement), R-11 (strictly > +25%). Simulator may assume an exact resubmission is a no-op duplicate. MODELLED: any 'equivocation penalty' — the pinned code has none; cross-node equivocation outcomes are unobservable from source alone.
- **S-03**: Grounding: R-21 (terPRE_SEQ for a future sequence), R-08 (accept skips non-first sequences), R-10 (gap-fill exception to the cap), R-22 (sequence consumed only by applied transactions). Simulator may assume a gap blocks every later sequence-based transaction; a ticket-based transaction is unaffected. MODELLED: how long a gap persists; ticket-created hole sizes (followingSeq arithmetic, G-01).
- **S-04**: Grounding: R-14 (LLS inclusive), R-13 (queue eviction at LLS <= closed seq; queueability needs LLS >= current + 2), R-26 (LocalTxs expiry). Simulator may assume a transaction with LLS = N can still be included in ledger N and is dead from N+1; a transaction submitted when the current ledger is N-1 or N cannot be queued at all. MODELLED: the wall-clock race (whether a transaction arriving during the close of ledger N lands in N or N+1 depends on proposal timing).
- **S-05**: Grounding: R-09 (dynamic cap max(txnsExpected x 20, 2000)), R-31 (full-queue admission by per-account average fee; victim is that account's last transaction), R-12 (retry/drop penalties), R-10 (10-per-account cap). Simulator may assume eviction is fee-driven and account-averaged, not global-lowest-first. MODELLED: any byte/memory-pressure model — the cap is a transaction COUNT; 'memory pressure' is translated to 'queue-full' to be simulable; the batch form of R-31 eviction (C-21).
- **S-06**: Grounding: R-21/R-22 (sequence is per-account), R-15 (canonical order sorts by salted account first), R-36 (queue order across accounts is never agreed directly). Simulator may assume two accounts using the same sequence number never conflict. MODELLED: which account's transaction 'wins' a fee race — there is no cross-account race for the same resource unless they touch the same ledger entries.
- **S-07**: Grounding: R-30 (no amendment changes TxQ fee order or canonical order; FeeEscalation retired; TicketBatch affects tickets; Batch unsupported), R-29 (activation needs strictly >80%). Simulator may assume ordering behaviour is amendment-invariant across the pinned feature list; the only ordering-adjacent flag is featureTicketBatch. MODELLED: activation timing of any future amendment; the effect of Batch (unsupported) is UNTESTABLE here. The 80.0%-exactly vote in this scenario does NOT activate (strictly-greater rule).
- **S-08**: Grounding: R-27 (preferred-ledger branch-support rule), R-28 (67% quorum in this fork), R-34 (validated = quorum on the same hash), R-26 (LocalTxs re-apply for 5 ledgers), R-17 (disputed NO-vote transactions go first into the next open ledger). Simulator may assume a rejoining node adopts the branch with strictly greater support and discards its own unvalidated ledgers; only local transactions (5 ledgers) and disputed NO-vote transactions are re-proposed. MODELLED: the exact rejoin sequence (InboundLedgers acquisition order, G-02).

## What the matrix does not show

Retry-count behaviour (R-12), fee-averaging rescue (R-32), blocker transactions (R-25), and live fee-escalation time series (R-03/R-37) are not exercised as separate scenarios; they are cited in the rule catalog and methodology.
