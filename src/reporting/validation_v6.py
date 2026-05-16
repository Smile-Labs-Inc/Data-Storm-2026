"""Extended validation diagnostics v6.

Adds three complementary checks that run AFTER the existing 6-item suite:
  V4b: mean_uplift >= 1.15 — catches model collapse when median passes at 1.25
  V6:  pct_at_floor < 95% — flags if >95% of outlets are at exactly 1.25×
  V7:  cs_std >= 0.05 — flags zero-variance constraint score

These are documented as "extended diagnostics" — they don't block submission
but flag degradation that the primary 6 checks might miss.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class ExtendedCheckResult:
    name: str
    passed: bool
    detail: str
    severity: str  # "warning" or "info"


@dataclass
class ExtendedValidationResult:
    all_passed: bool
    checks: list[ExtendedCheckResult]

    def to_markdown(self) -> str:
        lines = [
            "# Extended Validation Diagnostics (v6)\n",
            "| # | Check | Pass? | Severity | Detail |\n",
            "| ---: | --- | :---: | :---: | --- |\n",
        ]
        for i, c in enumerate(self.checks, 1):
            mark = "OK" if c.passed else "WARN"
            lines.append(
                f"| {i} | {c.name} | **{mark}** | {c.severity} | {c.detail} |\n"
            )
        return "".join(lines)


def run_extended_validation(
    submission: pd.DataFrame,
    historical_max: pd.Series,
    constraint_scores: pd.DataFrame | None = None,
    mean_uplift_min: float = 1.15,
    pct_at_floor_max: float = 95.0,
    cs_std_min: float = 0.05,
    out_dir: Path | str | None = None,
) -> ExtendedValidationResult:
    """Run extended diagnostics on submission + constraint scores.

    Args:
        submission: DataFrame with Outlet_ID + Maximum_Monthly_Liters
        historical_max: Series indexed by Outlet_ID
        constraint_scores: DataFrame with Outlet_ID + constraint_score (or constraint_score_v6)
        mean_uplift_min: minimum acceptable mean uplift
        pct_at_floor_max: maximum acceptable % of outlets at exactly 1.25×
        cs_std_min: minimum acceptable constraint_score standard deviation
        out_dir: if provided, write markdown + json reports
    """
    checks: list[ExtendedCheckResult] = []

    merged = submission.merge(
        historical_max.rename("hist_max"), on="Outlet_ID", how="left"
    )
    uplift = (
        merged["Maximum_Monthly_Liters"] / merged["hist_max"].replace(0, np.nan)
    ).dropna()

    mean_up = float(uplift.mean())
    v4b_ok = mean_up >= mean_uplift_min
    checks.append(
        ExtendedCheckResult(
            name=f"V4b: mean uplift >= {mean_uplift_min}",
            passed=v4b_ok,
            detail=f"mean_uplift={mean_up:.3f}",
            severity="warning" if not v4b_ok else "info",
        )
    )

    pct_at_floor = float((np.abs(uplift - 1.25) < 0.001).mean() * 100)
    v6_ok = pct_at_floor < pct_at_floor_max
    checks.append(
        ExtendedCheckResult(
            name=f"V6: pct at uplift floor < {pct_at_floor_max}%",
            passed=v6_ok,
            detail=f"{pct_at_floor:.1f}% at exactly 1.250×",
            severity="warning" if not v6_ok else "info",
        )
    )

    if constraint_scores is not None:
        cs_col = (
            "constraint_score_v6"
            if "constraint_score_v6" in constraint_scores.columns
            else "constraint_score"
        )
        if cs_col in constraint_scores.columns:
            cs_std = float(constraint_scores[cs_col].std())
            v7_ok = cs_std >= cs_std_min
            checks.append(
                ExtendedCheckResult(
                    name=f"V7: constraint_score std >= {cs_std_min}",
                    passed=v7_ok,
                    detail=f"cs_std={cs_std:.4f}",
                    severity="warning" if not v7_ok else "info",
                )
            )
        else:
            checks.append(
                ExtendedCheckResult(
                    name=f"V7: constraint_score std >= {cs_std_min}",
                    passed=False,
                    detail="constraint_score column not found",
                    severity="warning",
                )
            )
    else:
        checks.append(
            ExtendedCheckResult(
                name=f"V7: constraint_score std >= {cs_std_min}",
                passed=False,
                detail="no constraint_scores provided",
                severity="info",
            )
        )

    result = ExtendedValidationResult(
        all_passed=all(c.passed for c in checks), checks=checks
    )

    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "validation_extended_v6.md").write_text(
            result.to_markdown(), encoding="utf-8"
        )
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
