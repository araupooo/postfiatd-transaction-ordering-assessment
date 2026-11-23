# Gap register

| ID | Gap | Rules |
| --- | --- | --- |
| G-01 | TxConsequences::followingSeq arithmetic (ticket-created sequence holes) not excerpted — hole sizes for CreateTicket series are MODELLED in S-03. | R-21, S-03 |
| G-02 | InboundLedgers acquisition order on rejoin not traced — S-08 rejoin sequence is MODELLED. | R-27 |
| G-03 | No live-node verification of any fee level, queue depth, or escalation value (R-37/R-38). | R-37, R-38 |
| G-04 | Peer-propagation timing (when a transaction reaches each validator's queue) not modelled — affects which copy of an equivocating pair each node sees first. | R-24, S-02 |
| G-05 | fixAmendmentMajorityCalc threshold formula (computeThreshold) read but not excerpted — R-29's 'strictly >80%' is verified, the exact pre-fix denominator is not in the manifest. | R-29 |
| G-06 | Batch transactions (featureBatch, unsupported) ordering interaction untested — no code path exercised. | R-30 |
| G-07 | SHAMap iteration order for the consensus tx set (hash order) vs canonical order interplay not separately excerpted — R-35 rests on CanonicalTXSet being the sole application order. | R-15, R-35 |
| G-08 | Negative-UNL effect on the effective quorum floor (60% of UNL, R-28) verified only as a max() term, not exercised against a live UNL. | R-28 |

Counts: 8 gaps.
