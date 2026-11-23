# Evidence index

- `configs/ordering-rules.json` — 38 rules (R-01..R-33 VERIFIED, R-34 SPECIFIED, R-35/R-36 MODELLED, R-37/R-38 UNTESTABLE).
- `configs/scenarios.json` — 8 scripted scenarios, 46 synthetic transactions.
- `src/ordering_model.py` — the deterministic ordering simulator.
- `outputs/derived/ordering-results.json` — per-scenario outcomes and totals.
- `outputs/derived/scenario-matrix.json` — per-scenario count table.
- `outputs/derived/probe-results.json` — 12 probe checks, all PASS.
- `outputs/run.log`, `outputs/probe-run.log` — unedited run logs.
- `fixtures/source-excerpts/` — 61 verbatim excerpts; `fixtures/source-hashes.json` — digests + blob SHAs.
- `findings.json` — 12 findings.
- `run-manifest.json` — counts recomputed from the tables, plus result/matrix digests.
