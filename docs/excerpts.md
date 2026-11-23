# Excerpts

61 verbatim pinned-source excerpts in `fixtures/source-excerpts/`, re-derived by `scripts/extract_excerpts.py` from the pinned checkout. Line numbers were verified with `grep -n` on the local checkout of commit `0085a1ff885d6a446369cf73a4430f75af22be55`; no line number was taken from a web fetch. Blob SHAs and sizes come from `git hash-object` / file size on the checkout and are re-checked by `scripts/probe.py` (H-01).

| ID | File | Lines | Anchor |
| --- | --- | --- | --- |
| E01 | src/xrpld/app/misc/TxQ.h | 60-66 | baseLevel{256} |
| E02 | src/xrpld/app/misc/TxQ.h | 78-110 | ledgersInQueue = 20 |
| E03 | src/xrpld/app/misc/TxQ.h | 128-156 | maximumTxnPerAccount = 10 |
| E04 | src/xrpld/app/misc/TxQ.h | 580-592 | retriesAllowed = 10 |
| E05 | src/xrpld/app/misc/TxQ.h | 630-660 | pseudo-randomized transaction ID |
| E06 | src/xrpld/app/misc/detail/TxQ.cpp | 37-64 | mulDiv(effectiveFeePaid |
| E07 | src/xrpld/app/misc/detail/TxQ.cpp | 67-72 | sfLastLedgerSequence |
| E08 | src/xrpld/app/misc/detail/TxQ.cpp | 88-170 | escalationMultiplier_ = |
| E09 | src/xrpld/app/misc/detail/TxQ.cpp | 173-195 | current * current |
| E10 | src/xrpld/app/misc/detail/TxQ.cpp | 234-275 | sumOfFirstSquares |
| E11 | src/xrpld/app/misc/detail/TxQ.cpp | 376-383 | isFull |
| E12 | src/xrpld/app/misc/detail/TxQ.cpp | 384-410 | telCAN_NOT_QUEUE |
| E13 | src/xrpld/app/misc/detail/TxQ.cpp | 411-451 | maximumTxnPerAccount |
| E14 | src/xrpld/app/misc/detail/TxQ.cpp | 860-915 | requiredRetryLevel |
| E15 | src/xrpld/app/misc/detail/TxQ.cpp | 1243-1260 | isFull() |
| E16 | src/xrpld/app/misc/detail/TxQ.cpp | 1366-1405 | lastValid <= ledgerSeq |
| E17 | src/xrpld/app/misc/detail/TxQ.cpp | 1455-1480 | feeLevelPaid >= requiredFeeLevel |
| E18 | src/xrpld/app/misc/detail/TxQ.cpp | 1485-1565 | retryPenalty = true |
| E19 | src/xrpld/app/misc/detail/TxQ.cpp | 1580-1600 | parentHashComp = parentHash |
| E20 | src/xrpld/app/misc/detail/TxQ.cpp | 1679-1715 | feeLevelPaid >= requiredFeeLevel |
| E21 | src/xrpld/app/misc/detail/TxQ.cpp | 1785-1800 | byFee_.rbegin()->feeLevel |
| E22 | src/xrpld/app/misc/CanonicalTXSet.h | 30-50 | Puts transactions from the same account in SeqProxy order |
| E23 | src/xrpld/app/misc/CanonicalTXSet.cpp | 28-44 | lhs.seqProxy_ < rhs.seqProxy_ |
| E24 | src/xrpld/app/misc/CanonicalTXSet.cpp | 46-56 | ret ^= salt_ |
| E25 | src/xrpld/app/misc/CanonicalTXSet.cpp | 62-93 | Prioritize transactions with Sequences over transactions with |
| E26 | src/xrpld/app/ledger/OpenLedger.h | 38-46 | LEDGER_TOTAL_PASSES 3 |
| E27 | src/xrpld/app/ledger/OpenLedger.h | 215-270 | check.txExists |
| E28 | src/xrpld/app/ledger/detail/OpenLedger.cpp | 174-196 | isTefFailure |
| E29 | src/xrpld/app/ledger/detail/OpenLedger.cpp | 80-145 | retriesFirst |
| E30 | src/xrpld/app/tx/detail/Transactor.cpp | 331-348 | signerCount * baseFee |
| E31 | src/xrpld/app/tx/detail/Transactor.cpp | 380-410 | telINSUF_FEE_P |
| E32 | src/xrpld/app/tx/detail/Transactor.cpp | 480-550 | has future sequence number |
| E33 | src/xrpld/app/tx/detail/Transactor.cpp | 552-580 | tefMAX_LEDGER |
| E34 | src/xrpld/app/tx/detail/Transactor.cpp | 582-600 | seqProx.value() + 1 |
| E35 | src/xrpld/app/tx/detail/applySteps.cpp | 190-215 | checkPriorTxAndLastLedger |
| E36 | src/xrpld/app/tx/detail/applySteps.cpp | 290-300 | isBlocker_ = (category == blocker) |
| E37 | src/xrpld/consensus/ConsensusParms.h | 75-82 | minCONSENSUS_PCT = 67 |
| E38 | src/xrpld/consensus/ConsensusParms.h | 140-170 | avalancheCutoffs |
| E39 | src/xrpld/consensus/DisputedTx.h | 88-135 | minCONSENSUS_PCT |
| E40 | src/xrpld/consensus/DisputedTx.h | 275-310 | weight = (yays_ * 100 |
| E41 | src/xrpld/consensus/LedgerTrie.h | 625-670 | preferred ledger is found by walking |
| E42 | src/xrpld/consensus/Validations.h | 837-870 | more support amongst trusted validators |
| E43 | src/xrpld/consensus/Validations.h | 1031-1050 | v.trusted() && v.full() |
| E44 | src/xrpld/app/misc/detail/ValidatorList.cpp | 1898-1935 | Use a 67% quorum |
| E45 | src/xrpld/app/ledger/detail/LedgerMaster.cpp | 900-915 | valCount >= app_.validators().quorum() |
| E46 | src/xrpld/app/ledger/detail/LedgerMaster.cpp | 950-960 | getNeededValidations |
| E47 | src/xrpld/app/consensus/RCLConsensus.cpp | 515-535 | unpredictable but deterministic order |
| E48 | src/xrpld/app/consensus/RCLConsensus.cpp | 625-660 | Test applying disputed transaction |
| E49 | src/xrpld/app/ledger/detail/BuildLedger.cpp | 100-145 | built->txExists(txid) |
| E50 | src/xrpld/app/ledger/detail/LocalTxs.cpp | 55-70 | LastLedgerSequence) + 1 |
| E51 | src/xrpld/app/ledger/LocalTxs.h | 35-45 | holdLedgers = 5 |
| E52 | src/xrpld/app/misc/LoadFeeTrack.h | 140-150 | lftNormalFee = |
| E53 | src/xrpld/app/misc/FeeEscalation.md | 50-70 | lastLedgerMedianFeeLevel |
| E54 | src/xrpld/app/misc/FeeEscalation.md | 120-135 | 25% higher fee |
| E55 | include/xrpl/protocol/detail/features.macro | 100-106 | TicketBatch |
| E56 | include/xrpl/protocol/detail/features.macro | 148-152 | RETIRE(FeeEscalation) |
| E57 | src/xrpld/app/misc/detail/AmendmentTable.cpp | 360-378 | slightly less than 80% |
| E58 | src/xrpld/app/consensus/RCLCensorshipDetector.h | 99-130 | Determine which transactions made it |
| E59 | src/xrpld/app/misc/HashRouter.h | 260-275 | shouldRelay |
| E60 | src/xrpld/app/consensus/RCLConsensus.cpp | 770-805 | processClosedLedger |
| E61 | src/xrpld/app/consensus/RCLConsensus.h | 54-56 | censorshipWarnInternal = 15 |

Digests and git blob SHAs: `fixtures/source-hashes.json` (25 source files).
