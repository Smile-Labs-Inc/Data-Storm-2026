"""Extended (non-blocking) diagnostics added in council R6 / executed in R7.

The canonical 6-item suite (`validation.run_validation_suite`) is the
release gate. This module adds three *diagnostic* checks that catch model
degradation even when V1-V5 pass:

- V4b: mean uplift >= 1.15
       Complementary to V4 (median): catches collapse where median rides the
       constrained-outlet uplift floor (1.250) but the rest of the population
       has zero lift.

- V6:  pct_at_floor < 95
       If almost every outlet sits at exactly the 1.25x constrained-uplift
       floor, the model isn't differentiating -- the constraint score is
       effectively constant.

- V7:  cs_std >= 0.05
       If the constraint score has near-zero variance, it provides no signal
       and V4 becomes a pure tautology.

These checks DO NOT block submission (they run after the canonical suite).
They write `Results/validation_extended_v6.md` + `.json` alongside the main
validation report.

Usage (called from `run_pipeline.py` after `run_validation_suite`):

    from src.reporting.validation_v6 import run_extended_diagnostics
    ext = run_extended_diagnostics(
        submission=sub,
        historical_max=historical_max,
        constraint_score=cs,
        floor_ratio=1.25,
        floor_tolerance=0.001,
        out_dir=RESULTS_DIR,
    )
    for c in ext.checks:
        print(f"    [{'OK' if c.passed else 'WARN'}] {c.name} -- {c.detail}")
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class DiagnosticResult:
    name: str
    passed: bool
    detail: str
    severity: str  # "warn" or "info" -- never "fail" (these don't block)


@dataclass
class ExtendedDiagnostics:
    all_passed: bool
    checks: list[DiagnosticResult]

    def to_markdown(self) -> str:
        lines = [
            "# Extended Diagnostics (council R6 -- NON-BLOCKING)\n",
            "These checks run after the canonical 6-item suite. They never block submission;\n",
            "they flag model degradation that V1-V5 cannot catch.\n\n",
            "| # | Check | Status | Severity | Detail |\n",
            "| ---: | --- | :---: | :---: | --- |\n",
        ]
        for i, c in enumerate(self.checks, 1):
            mark = "OK" if c.passed else "WARN"
            lines.append(f"| {i} | {c.name} | **{mark}** | {c.severity} | {c.detail} |\n")
        return "".join(lines)


def run_extended_diagnostics(
    submission: pd.DataFrame,
    historical_max: pd.Series,
    constraint_score: pd.Series | None = None,
    floor_ratio: float = 1.25,
    floor_tolerance: float = 0.001,
    mean_uplift_min: float = 1.15,
    pct_at_floor_max: float = 95.0,
    cs_std_min: float = 0.05,
    out_dir: Path | str | None = None,
) -> ExtendedDiagnostics:
    """Run V4b/V6/V7 extended diagnostics.

    `historical_max` is a pd.Series indexed by Outlet_ID.
    `constraint_score` (optional) is a pd.Series indexed by Outlet_ID. If None,
    V7 is skipped with an informational note.
    """
    checks: list[DiagnosticResult] = []

    merged = submission.merge(historical_max.rename("hist_max"), on="Outlet_ID", how="left")
    uplift = (merged["Maximum_Monthly_Liters"] / merged["hist_max"].replace(0, np.nan)).dropna()

    mean_up = float(uplift.mean()) if len(uplift) else float("nan")
    v4b_ok = mean_up >= mean_uplift_min
    checks.append(DiagnosticResult(
        name=f"V4b: mean uplift >= {mean_uplift_min}",
        passed=v4b_ok,
        severity="warn",
        detail=f"mean_uplift={mean_up:.3f}",
    ))

    floor_lo = floor_ratio - floor_tolerance
    floor_hi = floor_ratio + floor_tolerance
    at_floor = uplift.between(floor_lo, floor_hi)
    pct_at_floor = float(at_floor.mean() * 100) if len(uplift) else float("nan")
    v6_ok = pct_at_floor < pct_at_floor_max
    checks.append(DiagnosticResult(
        name=f"V6: pct at floor ({floor_ratio}x +/- {floor_tolerance}) < {pct_at_floor_max}%",
        passed=v6_ok,
        severity="warn",
        detail=f"{pct_at_floor:.2f}% of outlets sit at the floor",
    ))

    if constraint_score is not None and len(constraint_score) > 0:
        cs_std = float(np.nanstd(constraint_score.values))
        v7_ok = cs_std >= cs_std_min
        checks.append(DiagnosticResult(
            name=f"V7: constraint_score std >= {cs_std_min}",
            passed=v7_ok,
            severity="warn",
            detail=f"cs_std={cs_std:.3f}",
        ))
    else:
        checks.append(DiagnosticResult(
            name="V7: constraint_score std (skipped)",
            passed=True,
            severity="info",
            detail="constraint_score not provided -- skipped",
        ))

    result = ExtendedDiagnostics(all_passed=all(c.passed for c in checks), checks=checks)

    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "validation_extended_v6.md").write_text(result.to_markdown(), encoding="utf-8")
        (out_dir / "validation_extended_v6.json").write_text(
            json.dumps(
                {
                    "all_passed": result.all_passed,
                    "checks": [asdict(c) for c in result.checks],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    return result
