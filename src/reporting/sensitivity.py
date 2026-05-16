"""Sensitivity sweep over the free knobs in the final formula.

Free knobs:
  - frontier quantile  (0.85, 0.90, 0.95)
  - cap multiplier     (2.0, 3.0, 4.0, 5.0, 6.0)
  - constraint score weights (alt schemes)

Reports: median uplift, mean uplift, max uplift, % outlets capped.
Output table -> Reports/figures/sensitivity_table.csv +
                Reports/figures/sensitivity_summary.md
"""

from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

from .. import modeling


def sensitivity_sweep(
    features: pd.DataFrame,
    transactions: pd.DataFrame,
    lower_bounds: pd.DataFrame,
    multi_q_predictions: pd.DataFrame,
    cap_table: pd.DataFrame,
    out_dir: Path | str,
    quantile_choices: tuple[float, ...] = (0.85, 0.90, 0.95),
    cap_overrides: tuple[float, ...] = (2.0, 3.0, 4.0, 5.0, 6.0),
    score_schemes: tuple[str, ...] = ("balanced", "frontier_heavy", "plateau_heavy"),
) -> pd.DataFrame:
    """Returns the long-form sensitivity table; also writes a markdown summary."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    base_features = features.merge(lower_bounds, on="Outlet_ID", how="left")
    base_features["lower_bound"] = base_features["lower_bound"].fillna(
        base_features["observed_max_monthly_liters"]
    )

    rows: list[dict] = []
    for q in quantile_choices:
        col = f"q{int(q * 100):02d}"
        if col not in multi_q_predictions.columns:
            continue
        frontier = pd.DataFrame({
            "Outlet_ID": features["Outlet_ID"].values,
            "frontier_q90": multi_q_predictions[col].values,
        })

        for scheme in score_schemes:
            wf, wp, wc = {
                "balanced": (0.5, 0.3, 0.2),
                "frontier_heavy": (0.7, 0.2, 0.1),
                "plateau_heavy": (0.3, 0.5, 0.2),
            }[scheme]
            cs = modeling.build_constraint_score(
                features=features,
                transactions=transactions,
                weight_frontier=wf,
                weight_plateau=wp,
                weight_capacity=wc,
            )

            for cap_value in cap_overrides:
                ct = cap_table.copy()
                ct["cap_uplift"] = cap_value
                preds = modeling.latent_potential(
                    features=features,
                    constraint_scores=cs,
                    lower_bounds=lower_bounds,
                    frontier=frontier,
                    cap_table=ct,
                )
                obs_max = preds["observed_max_monthly_liters"].replace(0, np.nan)
                up = (preds["Maximum_Monthly_Liters"] / obs_max).dropna()
                pct_capped = float(
                    (preds["Maximum_Monthly_Liters"].values >= cap_value * obs_max.values - 1e-6).mean() * 100
                )
                rows.append({
                    "quantile": q,
                    "score_scheme": scheme,
                    "cap_multiplier": cap_value,
                    "median_uplift": round(float(up.median()), 4),
                    "mean_uplift": round(float(up.mean()), 4),
                    "max_uplift": round(float(up.max()), 4),
                    "pct_capped": round(pct_capped, 2),
                })

    table = pd.DataFrame(rows)
    csv_path = out_dir / "sensitivity_table.csv"
    table.to_csv(csv_path, index=False)

    md_lines = ["# Sensitivity Sweep\n"]
    md_lines.append("Knobs swept: frontier quantile, constraint-score weighting scheme, cap multiplier.\n")
    md_lines.append("Stress: how much do final predictions move when these are changed?\n")
    md_lines.append("\n| Quantile | Scheme | Cap | Median Uplift | Mean Uplift | Max Uplift | % Capped |\n")
    md_lines.append("| ---: | --- | ---: | ---: | ---: | ---: | ---: |\n")
    for _, r in table.iterrows():
        md_lines.append(
            f"| {r['quantile']:.2f} | {r['score_scheme']} | {r['cap_multiplier']:.1f}x | "
            f"{r['median_uplift']:.3f} | {r['mean_uplift']:.3f} | "
            f"{r['max_uplift']:.3f} | {r['pct_capped']:.1f}% |\n"
        )
    (out_dir / "sensitivity_summary.md").write_text("".join(md_lines), encoding="utf-8")

    return table
