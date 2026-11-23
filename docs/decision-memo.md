# Decision memo

## Decision

Adopt the 38-rule catalog (33 VERIFIED, 1 SPECIFIED, 2 MODELLED, 2 UNTESTABLE) as the pack's ordering model, follow the code wherever XRPL docs disagree with it (quadratic escalation, 50/65/70/95 avalanche, 67% quorum), and label every model-only step as MODELLED rather than presenting it as source-derived.

## Why

- The 33 verified rules are each anchored to a grep-verified source range in the pinned tree, with 61 excerpts and blob SHAs re-checked by the probe.
- The three code-vs-docs conflicts are the pack's highest-value corrections: a simulator using exponential escalation, a 50/60 avalanche, or an 80% quorum would mispredict this fork's behaviour on every scenario that touches fees, disputes, or finality (K-01, K-02, K-13).
- The LLS triple boundary (admission +2, inclusion inclusive, eviction <=) is the subtlest mechanism in the pack; S-04 exercises all three comparisons in one scenario.
- Eviction is modelled as the code specifies it (per-account average, last transaction as victim) rather than the intuitive global-lowest-fee rule, which the code does not implement (K-05).

## What was not decided

- No live-network claim is made (R-37/R-38 UNTESTABLE).
- No amendment-gated ordering change is adopted: no amendment in the tree changes the TxQ fee order or the canonical order (R-30).
- No partition-rejoin procedure beyond the verified branch-support rule is adopted; the rejoin sequence is MODELLED (G-02).
- Batch-transaction ordering is not decided at all: `featureBatch` is unsupported in this build (G-06).

## Consequences

If a live node becomes available, R-37/R-38 can be verified against `fee` RPC output and observed consensus rounds, and the scenario parameters (required fee level, txnsExpected, queue cap) can be replaced with measured values. Until then the scenarios remain parametrised models.
