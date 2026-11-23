# Claim index

Every claim carries one status: VERIFIED (re-checked against the pinned checkout by `scripts/probe.py`), SPECIFIED (stated from a protocol doc, not from pinned code), MODELLED (an output or inference of the pack's simulator, not a source observation), UNTESTABLE (cannot be established from source alone).

| ID | Status | Claim | Rule | Evidence |
| --- | --- | --- | --- | --- |
| C-01 | VERIFIED | Queue candidates sort by feeLevel descending, ties by (txID XOR parentHash) ascending (TxQ.h:630-660). | R-01 | fixtures/source-excerpts/E05.txt |
| C-02 | VERIFIED | Reference fee level is 256 (baseLevel); a reference transaction paying the base fee has fee level 256. | R-02 | fixtures/source-excerpts/E01.txt |
| C-03 | VERIFIED | Open-ledger required fee level is flat 256 up to txnsExpected, then quadratic: multiplier x current^2 / target^2 (TxQ.cpp:173-195). | R-03 | fixtures/source-excerpts/E09.txt |
| C-04 | VERIFIED | Escalation multiplier is the median fee level of the last closed ledger, floored at baseLevel x 500 = 128,000. | R-04 | fixtures/source-excerpts/E08.txt |
| C-05 | VERIFIED | A transaction whose fee level >= required level direct-applies, bypassing the queue — only if its SeqProxy equals the account sequence or it uses a ticket. | R-06 | fixtures/source-excerpts/E20.txt |
| C-06 | VERIFIED | TxQ::accept drains the queue highest-fee-first and STOPS at the first candidate below the required level (break, not skip). | R-07 | fixtures/source-excerpts/E17.txt, fixtures/source-excerpts/E18.txt |
| C-07 | VERIFIED | Per-account sequence order is enforced inside accept: a non-first sequence is skipped until the earlier one applies; ticket transactions may apply in any order. | R-08 | fixtures/source-excerpts/E17.txt, fixtures/source-excerpts/E18.txt |
| C-08 | VERIFIED | Maximum queue size is dynamic: max(txnsExpected x 20, 2000) transactions, recomputed on each closed ledger. | R-09 | fixtures/source-excerpts/E16.txt |
| C-09 | VERIFIED | One account may queue at most 10 transactions; the only exception fills the first expiration-based sequence gap. | R-10 | fixtures/source-excerpts/E03.txt |
| C-10 | VERIFIED | Replacing a queued transaction requires fee level STRICTLY greater than old level x 1.25; exactly +25% is rejected. | R-11 | fixtures/source-excerpts/E14.txt |
| C-11 | VERIFIED | Queueability requires LastLedgerSequence >= current ledger seq + 2; queued transactions with LLS <= closed ledger seq are evicted. | R-13 | fixtures/source-excerpts/E12.txt |
| C-12 | VERIFIED | LastLedgerSequence is INCLUSIVE: preclaim fails with tefMAX_LEDGER only when view.seq() > LastLedgerSequence (Transactor.cpp:571-573). | R-14 | fixtures/source-excerpts/E33.txt |
| C-13 | VERIFIED | Canonical application order: salted account key first, then SeqProxy ascending, then txID ascending (CanonicalTXSet.cpp:28-44). | R-15 | fixtures/source-excerpts/E23.txt |
| C-14 | VERIFIED | A ledger is fully validated at a 67% quorum in this fork (ValidatorList.cpp:1898-1900), not upstream XRPL's 80%. | R-28 | fixtures/source-excerpts/E44.txt |
| C-15 | VERIFIED | Consensus dispute resolution is an avalanche with required YES weight 50% -> 65% -> 70% -> 95% (ConsensusParms.h:146-157). | R-18 | fixtures/source-excerpts/E38.txt |
| C-16 | VERIFIED | When the queue is full, admission is decided by per-account average fee and the victim is the cheapest-average account's last transaction (TxQ.cpp:1243-1260). | R-31 | fixtures/source-excerpts/E15.txt |
| C-17 | SPECIFIED | A ledger is validated only when a quorum of trusted validators sign the SAME ledger hash (hence the same tx set and the same canonical order). | R-34 | outputs/derived/ordering-results.json (model) |
| C-18 | SPECIFIED | Upstream XRPL validates at 80% (protocol docs); this fork validates at 67% (R-28, VERIFIED). The 80% figure is a protocol-doc statement, not a pinned-code fact. | R-34 | outputs/derived/ordering-results.json (model) |
| C-19 | MODELLED | Within a validated ledger, transaction application order is the canonical order, so two honest nodes that agree on the tx set necessarily agree on the order. | R-35 | outputs/derived/ordering-results.json (model) |
| C-20 | MODELLED | Two nodes with different parent hashes order same-fee queued transactions differently; consensus resolves the SET and the canonical order then resolves the ORDER — queue order itself is never agreed directly. | R-36 | outputs/derived/ordering-results.json (model) |
| C-21 | MODELLED | S-05 applies R-31 as a batch eviction (cheapest-average account, last transaction, repeated); the code evicts one transaction per admission decision, so batch order is a model choice. | R-31 | outputs/derived/ordering-results.json (model) |
| C-22 | MODELLED | S-08's rejoin sequence (fetch order, which ledgers are acquired first) is modelled; InboundLedgers acquisition order was not traced. | R-27 | outputs/derived/ordering-results.json (model) |
| C-23 | UNTESTABLE | Exact live fee levels, queue depth, txnsExpected, and escalation multiplier at any wall-clock time cannot be derived from source alone. | R-37 | outputs/derived/ordering-results.json (model) |
| C-24 | UNTESTABLE | Whether a given disputed transaction is included in a given round cannot be predicted from source alone. | R-38 | outputs/derived/ordering-results.json (model) |

Counts: 24 claims (VERIFIED 16, SPECIFIED 2, MODELLED 4, UNTESTABLE 2).
