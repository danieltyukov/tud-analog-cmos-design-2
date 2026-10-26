#!/usr/bin/env python3
"""Constrained power minimisation over .param knobs with Optuna, LTspice in the loop.

  uv run tools/optimize.py --tran design/amp_tran.net --noise design/amp_noise.net \\
      --space design/space.json --study s1 [--trials 150] [-j 8]

space.json maps .param names to ranges; integer knobs (M) use "int":
  {"Wn": ["log", 20e-6, 80e-6], "Cc": ["log", 300e-15, 1.2e-12], "Mout": ["int", 1, 8]}
Objective: minimise reported power. Constraints (all must hold, with evaluate.py margins):
  A(25ns) >= 78.3, Abeta(25ns) >= 66.3, floors after 25 ns >= 78/66, settled <= 24.8 ns,
  first ringing peak after 25 ns, SNR >= 66.05 dB, FoM <= 177 dB (TA plausibility ceiling).
--extra-snr / --extra-ab add margin on top (dB) so the winner is not knife-edge.
The study is stored in results/opt/<study>.db, so it resumes after an interruption.
Use it only once the topology works and hand sizing is close (it tunes, it does not invent).
Always re-verify the winner with tools/evaluate.py on the drawn .asc.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lt  # noqa: E402
import metrics as M  # noqa: E402


def trial_eval(tran_text: str, noise_text: str, params: dict, d: Path) -> dict:
    d.mkdir(parents=True, exist_ok=True)
    vals = {k: f"{v:.6g}" for k, v in params.items()}
    nt, nn = d / "tran.net", d / "noise.net"
    nt.write_text(lt.set_params(tran_text, vals))
    nn.write_text(lt.set_params(noise_text, vals))
    rt = lt.run(nt)
    rn = lt.run(nn)
    if not (rt["ok"] and rt["raw"] and rn["ok"] and rn["raw"]):
        return {"failed": True}
    tm = M.tran_metrics(rt["raw"], nt)
    nm = M.noise_metrics(rn["raw"])
    p = M.net_params(nt)
    snr = M.snr_db(tm["VoutStep_V"], math.hypot(M.ktc_uV(p["cin"]), nm["Vn_amp_uVrms"]))
    shutil.rmtree(d, ignore_errors=True)
    P = tm.get("P_report_mW", math.nan)
    return {
        "FoM": M.fom(P, tm["tau_ns"], snr)[1],
        "P_mW": tm.get("P_report_mW", math.nan), "SNR": snr, "A25": tm["A_at_25ns_dB"],
        "Ab25": tm["Abeta_at_25ns_dB"], "Afloor": tm["A_floor_dB"], "Abfloor": tm["Abeta_floor_dB"],
        "Ts": max(tm["Tsettle_A_ns"], tm["Tsettle_Abeta_ns"]),
        "peak": min(tm["first_peak_A_ns"], tm["first_peak_Abeta_ns"]), "tau": tm["tau_ns"],
    }


CONSTRAINTS = ("A25", "Ab25", "Afloor", "Abfloor", "Tsettle", "first_peak", "SNR", "FoM_TA")
EXTRA = {"snr": 0.0, "ab": 0.0}


def violations(r: dict) -> list[float]:
    """Optuna convention: each value <= 0 means satisfied."""
    if r.get("failed"):
        return [100.0] * len(CONSTRAINTS)
    xs, xa = EXTRA["snr"], EXTRA["ab"]
    c = [78.3 - r["A25"], 66.3 + xa - r["Ab25"], 78.0 - r["Afloor"], 66.0 + xa - r["Abfloor"], r["Ts"] - 24.8,
         25.0 - r["peak"], 66.05 + xs - r["SNR"], r["FoM"] - 177.0]
    # -inf means satisfied by infinite margin (no ringing peak at all: first peak = inf, as in
    # evaluate.py); NaN or +inf stay violations.
    return [x if math.isfinite(x) else (-100.0 if x == -math.inf else 100.0) for x in c]


def main(argv=None) -> int:
    import optuna

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tran", required=True)
    ap.add_argument("--noise", required=True)
    ap.add_argument("--space", required=True)
    ap.add_argument("--study", required=True)
    ap.add_argument("--trials", type=int, default=150)
    ap.add_argument("-j", "--jobs", type=int, default=8)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--extra-snr", type=float, default=0.0, help="extra SNR margin [dB] above 66.05")
    ap.add_argument("--extra-ab", type=float, default=0.0, help="extra Abeta margin [dB] on the 25 ns value and floor")
    ap.add_argument("--seed-params", default=None, help="JSON file {param: value}: enqueue a known point first")
    a = ap.parse_args(argv)
    EXTRA.update(snr=a.extra_snr, ab=a.extra_ab)

    def text(f):
        f = lt.guard(f)
        f = lt.netlist(f) if f.suffix.lower() == ".asc" else f.resolve()
        return lt.inline_includes(lt.read_text(f), f.parent)

    tran_text, noise_text = lt.fix_netlist(text(a.tran)), lt.fix_netlist(text(a.noise))
    space = json.loads(lt.guard(a.space).read_text())
    root = lt.REPO / "results" / "opt"
    root.mkdir(parents=True, exist_ok=True)
    lt.ensure_display()
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objective(trial):
        params = {}
        for k, (kind, lo, hi) in space.items():
            if kind == "int":
                params[k] = trial.suggest_int(k, int(lo), int(hi))
            else:
                params[k] = trial.suggest_float(k, lo, hi, log=(kind == "log"))
        # unique directory per evaluation: parallel workers can pick up the same enqueued trial
        (root / a.study).mkdir(parents=True, exist_ok=True)
        d = Path(tempfile.mkdtemp(prefix=f"t{trial.number:05d}_", dir=root / a.study))
        try:
            r = trial_eval(tran_text, noise_text, params, d)
        except Exception as e:  # a crashed simulation is an infeasible point, not the end of the study
            r = {"failed": True, "error": str(e)[:200]}
            shutil.rmtree(d, ignore_errors=True)
        trial.set_user_attr("r", r)
        trial.set_user_attr("c", violations(r))
        for name, v in zip(CONSTRAINTS, violations(r)):
            trial.set_constraint(name, v)  # Optuna >= 5 constraint API (<= 0 means satisfied)
        return r.get("P_mW", 99.0) if not r.get("failed") else 99.0

    sampler = optuna.samplers.TPESampler(seed=a.seed, multivariate=True, n_startup_trials=min(20, a.trials // 4))
    study = optuna.create_study(study_name=a.study, storage=f"sqlite:///{root / (a.study + '.db')}",
                                direction="minimize", sampler=sampler, load_if_exists=True)
    if a.seed_params:
        study.enqueue_trial(json.loads(lt.guard(a.seed_params).read_text()))
    study.optimize(objective, n_trials=a.trials, n_jobs=a.jobs)

    feas = [t for t in study.trials if t.user_attrs.get("c") and all(x <= 0 for x in t.user_attrs["c"])]
    print(f"{len(study.trials)} trials, {len(feas)} feasible")
    if not feas:
        best = min(study.trials, key=lambda t: sum(max(0, x) for x in t.user_attrs.get("c", [100] * len(CONSTRAINTS))))
        print("no feasible point; least-violating:", best.params, best.user_attrs.get("r"))
        return 2
    best = min(feas, key=lambda t: t.value)
    out = root / f"{a.study}_best.json"
    out.write_text(json.dumps({"params": best.params, "result": best.user_attrs["r"]}, indent=1))
    print(f"best P = {best.value:.4f} mW  params = {best.params}")
    print(f"  {best.user_attrs['r']}")
    print(f"-> {out}  (apply to the .asc params, then run tools/evaluate.py)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
