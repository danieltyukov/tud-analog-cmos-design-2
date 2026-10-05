# tools/ (run from the repo root with `uv run`)

| Script | Does |
|---|---|
| `lt.py` | LTspice XVII batch runner (Wine + shared Xvfb), `.meas` and `.op` parsing, parallel `.param` sweeps |
| `metrics.py` | settling (A, Aβ, τ, floors, ringing, power), noise integration, loop gain, kT/C/SNR/FoM budget, D4/D5 plots |
| `evaluate.py` | the judge: lint + tran + noise + op, 22-row table, PASS/FAIL, `results/history.csv`, `--publish` for the report |
| `robust.py` | settling under polarity / edge-rate / reltol variants |
| `optimize.py` | Optuna constrained power minimisation over `.param` knobs |
| `gmid.py` | gm/ID tables from LTspice itself (`build`, `table`, `size`); tables in `gmid/` |
| `asc_lint.py` | assignment rules and schematic hygiene |
| `opvals.py` | `.op` node voltages and branch currents as LaTeX macros (`\opV`, `\opI`) |
| `report.py` | build / check / render the report at fixed paths |
| `check_done.py` | definition of done (used by the Stop hook) |
| `selftest.py` | regression against the passing example; run first in every session |

All verified on 5 Oct 2026 against `example/` (see `example/README.md`). Every tool confines file
access to the repo and the Claude scratch dir (`lt.guard`) because the harness auto-approves `uv run tools/*`.
