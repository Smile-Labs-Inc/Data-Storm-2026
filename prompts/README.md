# AI Council + Research Prompts

Reusable prompts for the AI council methodology used to build the v2 stack.
Drop any of these into Claude Code, Cursor agent, or any LLM with a Task /
subagent tool. Each is self-contained.

## File index

| File | Purpose | When to use |
|---|---|---|
| `00_council_cycle_master.md` | Full 5-critic council cycle (read priors -> launch 5 in parallel -> synthesize -> apply fixes -> re-execute notebooks -> verify) | Every full audit + fix iteration |
| `01_critic_gap_analyzer.md` | Maps current state vs 40/40/20 rubric; ROI-ranks fixes | Inside cycle, or solo for "where am I losing points?" |
| `02_critic_data_engineer.md` | DE rubric scorecard + file hygiene + reproducibility | Inside cycle, or solo after big refactor |
| `03_critic_eda_specialist.md` | Writes + executes EDA notebook cells with real plots | Inside cycle, or once when EDA is thin |
| `04_critic_modeling_diagnostician.md` | Live diagnostics on predictions; surgical fix proposal | Inside cycle, or solo when validation fails |
| `05_critic_business_viva.md` | 3-slide pitch + hostile-judge Q&A + report polish | Inside cycle, or solo before viva day |
| `06_iteration_fast.md` | Emergency single-fix prompt | When you know what's broken but want LLM to patch it |
| `07_research_swarm_10_channels.md` | Parallel 10-channel research swarm (Round 0 pattern) | New competition / new methodology landscape scan |

## How the cycle works (1-page mental model)

```
Read R1..Rn synthesis files
        |
        v
Launch 5 critics in ONE parallel batch (Task tool)
        |
        v  each critic reads code + runs live diagnostics + writes review
        v
Synthesize -> council_round<N+1>/council_review_v<N+1>.md
        |
        v
Apply fixes (StrReplace for .py, EditNotebook for .ipynb cells)
        |
        v
Re-execute affected notebooks via venv kernel
        |
        v
Read Results/validation_report.md
        |
        +-- if 6/6 PASS: report numbers + ship readiness
        +-- if any FAIL: mini-iterate ONCE (single targeted patch)
```

## Defaults baked into the prompts

- 5 parallel subagents (one Task batch -- never serialise)
- Premium thinking models for Statistician / Modeling / EDA roles
- Mid-tier for DE / Business
- Validation thresholds: V3b 99%, V4 [1.25, 2.2], V5 < 25%
- Submission policy: notebook 22 always overwrites
  `Results/smil_labs_predictions.csv` with v2 (canonical release gate)
- Banned: any git command (commit / push / amend); team owns commit timing
- Banned: editing v1 notebooks (01, 03, 04, 10, 11) or v1 archived docs

## Venv (Windows)

```powershell
D:\projects\Data-Storm-2026\.venv\Scripts\python.exe
```

Registered jupyter kernel: `datastorm-venv`

Execute notebook command:

```powershell
D:\projects\Data-Storm-2026\.venv\Scripts\python.exe -m nbconvert ^
  --to notebook --execute --inplace ^
  --ExecutePreprocessor.timeout=900 ^
  --ExecutePreprocessor.kernel_name=datastorm-venv ^
  Notebooks\<file>.ipynb
```

## Cost reality

Per full council cycle (5 critics + 1 synth + 1 fix + 2 notebook re-runs):
~$15-35 in subagent calls. Notebook executions are local CPU time only.

Per emergency single-fix (prompt 06): ~$2-5.

Per research swarm (prompt 07): ~$30-60 -- only run once per new comp.

## Adapt for another competition

These prompts are Data-Storm-specific in the file-path and rubric-weight
sections. To reuse for another comp, search-and-replace:

- `D:/projects/Data-Storm-2026` -> your repo path
- `40 / 40 / 20` -> your rubric weights
- `V3b 99% / V4 [1.25, 2.2]` -> your validation thresholds
- `Smil Labs` / `Data Storm 7.0` -> your team / comp names
- Notebook numbers (`20_v2_*`, `21_v2_*`, etc.) -> your notebook scheme
