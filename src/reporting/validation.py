"""6-item automatic validation suite for the final predictions table.

Reflects the council Architect's recommendation. All 6 checks must pass before
the team submits.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


@dataclass
class ValidationResult:
    all_passed: bool
    checks: list[CheckResult]

    def to_markdown(self) -> str:
        lines = ["# Submission Pre-flight Validation\n", "| # | Check | Pass? | Detail |\n", "| ---: | --- | :---: | --- |\n"]
        for i, c in enumerate(self.checks, 1):
            mark = "OK" if c.passed else "FAIL"
            lines.append(f"| {i} | {c.name} | **{mark}** | {c.detail} |\n")
        return "".join(lines)


def run_validation_suite(
    submission: pd.DataFrame,
    outlet_master: pd.DataFrame,
    historical_max: pd.Series,
    cap_table: pd.DataFrame | None = None,
    bucket_keys: pd.DataFrame | None = None,
    expected_rows: int = 20_000,
    # FIX R3 (council round 3): tighten the range so V4 actually catches if
    # the M1 quadruple-throttle fix didn't land. Old range [1.05, 2.5] was so
    # wide it passed even when median uplift was 1.18x (the broken value).
    median_uplift_min: float = 1.25,
    median_uplift_max: float = 2.2,
    cap_binding_max_pct: float = 25.0,
    out_dir: Path | str | None = None,
) -> ValidationResult:
    """`historical_max`: pd.Series indexed by Outlet_ID giving each outlet's observed_max."""
    checks: list[CheckResult] = []

    expected_cols = {"Outlet_ID", "Maximum_Monthly_Liters"}
    actual_cols = set(submission.columns)
    schema_ok = expected_cols.issubset(actual_cols) and len(submission) == expected_rows
    checks.append(CheckResult(
        name="V1: schema + row count",
        passed=schema_ok,
        detail=f"cols={sorted(actual_cols)}, rows={len(submission)} (expected {expected_rows})",
    ))

    no_nan = not submission["Maximum_Monthly_Liters"].isna().any()
    no_negative = (submission["Maximum_Monthly_Liters"] >= 0).all()
    no_dups = submission["Outlet_ID"].is_unique
    v2_ok = bool(no_nan and no_negative and no_dups)
    checks.append(CheckResult(
        name="V2: no NaN, no negatives, unique IDs",
        passed=v2_ok,
        detail=f"NaN={int(submission['Maximum_Monthly_Liters'].isna().sum())}, "
               f"neg={int((submission['Maximum_Monthly_Liters'] < 0).sum())}, "
               f"unique={no_dups}",
    ))

    valid_ids = set(outlet_master["Outlet_ID"].astype(str))
    in_master = submission["Outlet_ID"].astype(str).isin(valid_ids)
    v_ref_ok = bool(in_master.all())
    checks.append(CheckResult(
        name="V3a: every Outlet_ID exists in outlet_master",
        passed=v_ref_ok,
        detail=f"missing={int((~in_master).sum())}",
    ))

    merged = submission.merge(historical_max.rename("hist_max"), on="Outlet_ID", how="left")
    pct_below = float(((merged["Maximum_Monthly_Liters"] < merged["hist_max"]).fillna(False)).mean() * 100)
    v3_ok = pct_below < 1.0
    checks.append(CheckResult(
        name="V3b: predicted >= historical max for >= 99% of outlets",
        passed=v3_ok,
        detail=f"{pct_below:.2f}% below historical max",
    ))

    uplift = (merged["Maximum_Monthly_Liters"] / merged["hist_max"].replace(0, np.nan)).dropna()
    median_up = float(uplift.median())
    v4_ok = median_uplift_min <= median_up <= median_uplift_max
    checks.append(CheckResult(
        name=f"V4: median uplift in [{median_uplift_min}, {median_uplift_max}]",
        passed=v4_ok,
        detail=f"median_uplift={median_up:.3f}",
    ))

    # FIX O1 (council round 2): use the actual bucket cap_uplift from cap_table
    # instead of a hardcoded 5.9x. Falls back to 5.9x only if cap_table missing.
    if cap_table is not None and bucket_keys is not None:
        bucket_keys = bucket_keys.merge(
            cap_table[["Outlet_Type", "Outlet_Size", "cap_uplift"]],
            on=["Outlet_Type", "Outlet_Size"],
            how="left",
        )
        merged_caps = merged.merge(
            bucket_keys[["Outlet_ID", "cap_uplift"]], on="Outlet_ID", how="left"
        )
        merged_caps["cap_uplift"] = merged_caps["cap_uplift"].fillna(5.9)
        cap_threshold = (merged_caps["hist_max"] * merged_caps["cap_uplift"]).round(2)
        cap_label = "bucket-specific cap"
    else:
        cap_threshold = (merged["hist_max"] * 5.9).round(2)
        cap_label = "fallback 5.9x"
    capped = (merged["Maximum_Monthly_Liters"] >= (cap_threshold * 0.999)).fillna(False)
    pct_capped = float(capped.mean() * 100)
    v5_ok = pct_capped < cap_binding_max_pct
    checks.append(CheckResult(
        name=f"V5: cap-binding rate < {cap_binding_max_pct}% ({cap_label})",
        passed=v5_ok,
        detail=f"{pct_capped:.2f}% appear at the cap",
    ))

    result = ValidationResult(all_passed=all(c.passed for c in checks), checks=checks)

    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "validation_report.md").write_text(result.to_markdown(), encoding="utf-8")
        (out_dir / "validation_report.json").write_text(
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
