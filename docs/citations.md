# Citations

## Pinned-tree citations (primary)

All ordering rules cite the pinned postfiatd tree (commit `0085a1ff885d6a446369cf73a4430f75af22be55`), verified by `grep -n` on the local checkout. The full rule-to-source mapping is `configs/ordering-rules.json`; the excerpt table is `docs/excerpts.md`. Key citations re-verified by grep in this pack:

- OrderCandidates comparator — `src/xrpld/app/misc/TxQ.h:656-658` (E05).
- Fee escalation, quadratic — `src/xrpld/app/misc/detail/TxQ.cpp:173-195` (E09).
- LastLedgerSequence inclusive — `src/xrpld/app/tx/detail/Transactor.cpp:571-573` (E33).
- 67% quorum — `src/xrpld/app/misc/detail/ValidatorList.cpp:1898-1900` (E44).
- Canonical key order — `src/xrpld/app/misc/CanonicalTXSet.cpp:28-44` (E23/E24).
- Dispute avalanche ladder 50/65/70/95 — `src/xrpld/consensus/ConsensusParms.h:146-157` (E38).
- Strict replacement — `src/xrpld/app/misc/detail/TxQ.cpp:913` (`feeLevelPaid > requiredRetryLevel`, E14).

## External citations (non-pinned-tree sources)

| # | URL | What it establishes |
| --- | --- | --- |
| C-01 | https://xrpl.build/docs/concepts/transactions/transaction-queue | TxQ purpose, queue-and-consensus steps, queuing restrictions (10/account, LLS >= current+2, fee averaging). Corroborates R-09/R-10/R-13/R-32 from the docs side. |
| C-02 | https://xrpl.org/docs/concepts/transactions/transaction-cost | Reference cost 10 drops, load cost vs open ledger cost, special costs (multi-sign x(1+N)). Corroborates R-19/R-20. |
| C-03 | https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/server-info-methods/fee | `fee` RPC fields (drops.base_fee/median_fee/minimum_fee/open_ledger_fee, levels.*, queue sizes). Basis for R-37's live-data requirement. |
| C-04 | https://xrpl.org/docs/concepts/consensus-protocol/negative-unl | Quorum is 80% of trusted validators upstream; Negative UNL adjusts the effective UNL with a 60% absolute floor. Source for R-34; contrasts with this fork's 67% (R-28). |
| C-05 | https://learn.xrpl.org/course/intro-to-the-xrpl/lesson/how-the-xrp-ledger-works/ | 'Once a supermajority (80%) of the network agrees on a proposed ledger, it is validated.' Upstream statement; see R-34 note. |
| C-06 | https://brain.ckelley.dev/concepts/XRPL-Transaction-Lifecycle | Independent lifecycle write-up: sequence consumption by tes/tec, tefPAST_SEQ finality, tefMAX_LEDGER finality once a validated ledger passes LLS. Corroborates R-14/R-22 from a non-Ripple source. |
| C-07 | https://arxiv.org/abs/1802.07242 | 'Analysis of the XRP Ledger Consensus Protocol' — Theorem 8, cited in ValidatorList.cpp as the basis for the 67% quorum's fork-safety argument (R-28). |

## Limits stated honestly

- Live fee levels, queue depth, txnsExpected, and escalation values are UNTESTABLE from source alone (R-37/R-38).
- The 67% quorum is verified in this fork's code with an explicit comment that mainnet should revert to 80%; whether any deployed PostFiat network actually runs 67% or 80% is a deployment fact, not a code fact, and was not verified.
- Amendment activation dates and live voting percentages are not in the pinned tree.
- Cross-validator behaviour (which copy of an equivocating pair each node saw first, proposal arrival order) is inherently unobservable from a single checkout.
- The `Batch` feature is unsupported in this build, so batch-transaction ordering could not be verified at all.
- XRPL docs sometimes disagree with the code (escalation 'exponential' vs quadratic; avalanche 50/60 vs 50/65/70/95). Where they disagree, this pack follows the code and says so.
