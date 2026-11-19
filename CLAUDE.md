# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Simulation and figure code for the manuscript "Hierarchy of prediction errors shapes the learning of context-dependent sensory representations". Simulated agents (models of mouse S1 L2/3 pyramidal neurons with top-down gain from lOFC → SST interneurons) learn a go/no-go discrimination task with rule reversals. The repo also holds the mouse behavioural data and recomputes every reported statistic.

## Environment and commands

Conda env `ofcsst` (Python 3.10, pinned torch 1.13 / numpy 1.23 / matplotlib 3.7; `environment.yml` installs this package with `pip install -e .`).

```
conda env create -f environment.yml && conda activate ofcsst
python main.py plot       # plot every panel and assemble figures/figures.pdf (~2 min; also the default with no argument)
python main.py stats      # recompute and print every statistic in the manuscript (~1 min)
python main.py simulate   # rerun final simulations, overwriting results/simulation (~1 h)
python main.py scan       # rerun all hyperparameter scans (very long; see warning below)
```

There is no test suite and no linter configuration. To work on one figure, import its module and call its entry points directly, e.g.:

```
python -c "from ofcsst.figures.main import f3efg_ofc_sst as m; m.plot(save=False)"   # show interactively instead of saving
python -c "from ofcsst.figures.main import f3efg_ofc_sst as m; m.run()"              # rerun just this figure's simulations
```

## Pipeline: scan → simulate → plot → assemble

1. **Scan** (`simulation/scan.py`, `find_best_params`): iterative log-grid search over learning rates (and OFC/SST constants for OFC models), 64 seeds each (`constants.NR_SEEDS`). Job files are written to `jobs/` (gitignored, deleted on completion); results go to `results/scan/<simulation_type>/<task_id>/<stationary|non-stationary>/<scan_type>.db` with tables `data`, `scan_evaluations` and `best_params`. Round 0 (`RESET_ID`) **drops all tables** in that database, so calling any module's `scan()` discards the committed scan results; later rounds skip parameter combinations already in `scan_evaluations`. Interrupting a scan can corrupt the database.
2. **Simulate** (each figure module's `run()`): reads `best_params` from the scan DB, simulates with disjoint seed ranges per condition (blocks of `constants.NR_SIM_MICE`), and writes `results/simulation/*.db|pkl|npy` (supplementary under `results/simulation/supplementary/`).
3. **Plot** (each module's `plot(save=True)` and `panel_*` functions): reads simulation results and/or `results/experimental/perf_<MouseType>_<LearningRule>.csv` (rows = mice, columns = sessions, NaN-padded) and writes `figures/main/figN/*.pdf` plus an `svg/` copy via `helper.save_or_show`.
4. **Assemble** (`plot_all.assemble_figures`): composes panel PDFs into `figures/figures.pdf` with pypdf at hardcoded x/y offsets. Hand-drawn schematics come from `figures/schematics.pdf` (page index per figure) and a few static PDFs under `figures/`.

`stats` (`plot_all.stats`) calls specific `panel_*` functions with `verbose=True`; the tests themselves live in `figures/statistics.py` (Welch's t with Bonferroni correction; log-rank plus Cox proportional hazards for time-to-expertise).

## Figure modules

Each module in `ofcsst/figures/main` and `ofcsst/figures/supplementary` is named after the panels it produces (`f3efg_ofc_sst` = Figure 3e–g; `fs12_vip_cl_stats` = Figure S12, output dir `figs12`). A module exposes whichever of `scan()`, `run()` and `plot(save=True)` apply. The top-level drivers find them **by name string** with `getattr`, so a new or renamed module must be added to:
- the subpackage `__init__.py` imports,
- the name lists in `plot_all.plot`, `run_all.run` and/or `scan_all.scan`,
- the layout block in `plot_all.assemble_figures` if it adds panels (panel PDF filenames are hardcoded there).

Shared colours, panel sizes (cm-based, 17.8 cm figure width) and the matplotlib style live in `figures/helper.py`.

## Simulation model

- `utils/ids.py`: `SimulationType` string literals identify each model variant and are the dispatch key everywhere (scan DB paths, DB table names, constructor choice). Group lists such as `TD_LR_SIMULATIONS`, `OFC_SST_SIMULATIONS` and `FAKE_OFC_SIMULATIONS` change behaviour (logging sizes, DB columns, a mid-run `fake_ofc()` call), so membership matters.
- `simulation/simulate.py`: `init_simulation` builds agent + task + logger from a **positional list of parameter strings**; the first four are always distractor amplitude, signal amplitude, number of distractors and number of signals (older code calls distractor amplitude `noise_std`). `run_simulation` seeds `random`/numpy/torch, then runs trial blocks, reversing the rule on every odd block. The per-trial loop is `task.init_stimuli → agent.get_action → task.get_outcome → agent.update`.
- `simulation/network.py`: building blocks. Actors (`PGActor`, `QActor` and their control variants), gain modulators (`GainModulatorV` = top-down apical gain driven by value-prediction credit; `GainModulatorOFCSST` adds the lOFC → SST pathway that suppresses that gain when the context prediction error crosses threshold; `GainModulatorRW` is the Rescorla–Wagner control), and `OFC` (per-action outcome predictors, an outcome-variance estimator and the context prediction error). The module docstring summarises these families.
- `simulation/agents.py`: composes actors and gain modulators. `ConvexAgent*` mix a habitual PG actor with a goal-directed Q actor; `ConvexAgentOFC` is the full lOFC–SST model.

**Adding or changing a model's hyperparameters requires keeping four places in the same order**: `simulate.init_simulation` (positional parsing), `databases.get_param_keys` (DB column order), `parameters.job_to_sim_params` (job row → DB row), and the grid writers in `scan.py` (`write_lr_jobs`, `write_scan_jobs_td`, `write_scan_jobs_ofc_all`).

## Conventions and gotchas

- Expertise differs between models and mice: simulations use a 100-trial moving-average performance > 85 % (`EXPERT_PERFORMANCE`, 0-based trial index); mice use d′ ≥ 1.5 (`EXPERT_D`, 1-based session index). Use `process.get_expert_t(..., simulation=...)` and `process.get_events` rather than re-deriving these.
- Global constants (trials per rule = 600, task sizes, learning-rate caps, OFC thresholds) are in `utils/constants.py`; string keys for DB columns are in `utils/keys.py`; filesystem layout is in `utils/paths.py` (all paths resolve from the repo root).
- `.gitignore` lists `/figures/` and `/results/`, yet the scan DBs, simulation outputs, experimental CSVs and static schematic PDFs are tracked (force-added). Regenerated outputs show up as modifications, while a newly created output file stays untracked unless added with `git add -f`.
- `main.py` sets logging to CRITICAL; progress is reported with `print` and carriage returns.
