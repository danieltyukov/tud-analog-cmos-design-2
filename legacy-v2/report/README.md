# report/

`main.tex` is the 8-page skeleton in the compulsory order. Build with `uv run tools/report.py build`
(runs latexmk with `latexmkrc`; output `main.pdf`), check with `report.py info`, render with `report.py pages`. Values come from `generated/results.tex` and `generated/opvals.tex`
(written by `uv run tools/evaluate.py ... --publish`); until then `placeholders.tex` renders red `??`.
D2/D3 drawings live in `circuits/` (`style.tex` defines `\Vtag`, `\Itag`, `\showI`). D4/D5 figures are
copied into `figures/` by `--publish`. Final file to upload: `main.pdf`, renamed `5714699.pdf`.
