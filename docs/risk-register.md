# Risk register

Severity is a pack judgement (MODELLED), not a source fact: it rates how badly a simulator that made the stated wrong assumption would mispredict ordering behaviour.

| ID | Severity | Risk | Rules |
| --- | --- | --- | --- |
| K-01 | HIGH | Simulator assumes upstream 80% quorum, producing wrong finality/divergence predictions for this fork. | R-28 |
| K-02 | HIGH | Simulator uses exponential instead of quadratic escalation, over-pricing fee spikes and mis-timing queue drains. | R-03 |
| K-03 | MEDIUM | Simulator treats LastLedgerSequence as exclusive, causing an off-by-one on expiry races (S-04). | R-14 |
| K-04 | HIGH | Simulator assumes queue order is agreed by consensus, understating cross-node divergence. | R-01, R-36 |
| K-05 | MEDIUM | Simulator models eviction as global-lowest-fee, selecting the wrong victim under a full queue. | R-31 |
| K-06 | MEDIUM | Simulator allows exactly +25% replacement, so replacement scenarios wrongly succeed. | R-11 |
| K-07 | MEDIUM | Simulator assumes a duplicate payload is deduped by account+sequence, missing the replacement path and the first-wins race. | R-23, R-24 |
| K-08 | MEDIUM | Simulator assumes fee buys certainty; a high-fee transaction with a future sequence or a gap ahead of it still cannot apply. | R-06, R-08, R-21 |
| K-09 | LOW | Simulator treats 'memory pressure' as bytes; the real cap is a transaction count, so pressure scenarios must be re-expressed as queue-full. | R-09 |
| K-10 | LOW | Simulator assumes disputed transactions are forced in eventually; the censorship detector only warns, so exclusion can persist. | R-18, R-33 |
| K-11 | MEDIUM | Simulator assumes amendment activation at >=80%; the post-fix rule is strictly >80%, so an 80.0%-exactly vote does not activate. | R-29 |
| K-12 | MEDIUM | Simulator assumes the losing branch's open-ledger transactions are re-proposed on rejoin; only local transactions (5 ledgers) and disputed NO-vote transactions are, others must be resubmitted by their senders. | R-17, R-26 |
| K-13 | MEDIUM | Avalanche thresholds taken from docs (50/60/...) instead of code (50/65/70/95), mis-timing dispute rounds. | R-18 |
| K-14 | LOW | Simulator relies on live fee levels without a node; R-37 values are unknowable from source, so scenarios must parametrise them. | R-37 |

Counts: 14 risks (HIGH 3, MEDIUM 8, LOW 3).
