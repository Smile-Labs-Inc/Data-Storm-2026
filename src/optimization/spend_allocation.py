"""LKR-budget spend optimizer with a diminishing-returns response model.

Problem (Section 2.3)
---------------------
Distribute a fixed promotional budget B across the outlets of a province so as
to maximise the *additional* sales volume gained over normal historical sales,
without exceeding B.

Response model
--------------
For outlet i, marketing converts part of its latent *headroom* (potential minus
normal baseline volume) into realised volume, with saturating (concave) returns:

    g_i(s) = H_i * (1 - exp(-s / k_i))                      [incremental litres]

  H_i = headroom_litres_i                         (max incremental volume)
  k_i = spend (LKR) at which ~63% of H_i is captured -- the responsiveness scale

k_i is tied to the *economic size* of the opportunity and the local competitive
environment, so the model spends more where there is more to win but is harder
to win it:

    k_i = alpha * (H_i * bill_per_litre_i) * (1 + beta * competitive_intensity_i)

A per-outlet cap prevents a few large outlets from absorbing the whole budget:

    s_i <= cap_frac * (H_i * bill_per_litre_i)             [revenue-anchored cap]

Optimisation
------------
g_i is concave and increasing, so maximising sum_i g_i(s_i) s.t. sum_i s_i <= B,
0 <= s_i <= s_max_i is a separable concave knapsack. At the optimum every
interior outlet shares one marginal return (shadow price) lambda:

    g_i'(s_i) = (H_i / k_i) * exp(-s_i / k_i) = lambda
    =>  s_i(lambda) = k_i * ln( H_i / (k_i * lambda) ),  clipped to [0, s_max_i]

We bisect lambda so that sum_i s_i(lambda) = B (water-filling). This yields the
provably optimal allocation for the model -- no heuristic ranking required.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "Results"


@dataclass(frozen=True)
class AllocationConfig:
    budget_lkr: float = 5_000_000.0
    province: str = "Western"
    alpha: float = 0.15           # responsiveness scale (k as fraction of headroom value)
    beta: float = 0.50            # competition penalty on marketing efficiency
    cap_frac: float = 0.35        # per-outlet spend cap as fraction of headroom value
    min_spend_lkr: float = 250.0  # drop sub-threshold dust allocations
    team_name: str = "smile_labs"


def _response(spend: np.ndarray, headroom: np.ndarray, k: np.ndarray) -> np.ndarray:
    """Incremental litres g_i(s) = H_i (1 - exp(-s/k_i))."""
    with np.errstate(over="ignore"):
        return headroom * (1.0 - np.exp(-np.divide(spend, k, out=np.zeros_like(spend), where=k > 0)))


def allocate_budget(
    headroom: np.ndarray,
    bill_per_liter: np.ndarray,
    competitive_intensity: np.ndarray,
    cfg: AllocationConfig = AllocationConfig(),
) -> dict[str, np.ndarray]:
    """Water-filling allocation. Returns spend + expected incremental litres per outlet.

    All array inputs are aligned 1-D arrays (one entry per candidate outlet).
    """
    H = np.asarray(headroom, dtype=float).clip(min=0.0)
    bpl = np.asarray(bill_per_liter, dtype=float).clip(min=0.0)
    comp = np.asarray(competitive_intensity, dtype=float).clip(0.0, 1.0)

    value = H * bpl  # economic size of the opportunity, LKR
    k = cfg.alpha * value * (1.0 + cfg.beta * comp)
    s_max = cfg.cap_frac * value

    active = (H > 0) & (k > 0) & (s_max > 0)
    spend = np.zeros_like(H)

    def total_spend(lmbda: float) -> tuple[float, np.ndarray]:
        s = np.zeros_like(H)
        if lmbda <= 0:
            s[active] = s_max[active]
        else:
            # interior solution, clipped to [0, s_max]
            raw = k[active] * np.log(
                np.divide(H[active], k[active] * lmbda, out=np.zeros(active.sum()), where=(k[active] * lmbda) > 0)
            )
            s[active] = np.clip(raw, 0.0, s_max[active])
        return float(s.sum()), s

    cap_total = float(s_max[active].sum())
    if cap_total <= cfg.budget_lkr:
        # Budget covers every outlet's cap -> fund all caps (still concave-optimal).
        spend[active] = s_max[active]
    else:
        # Bisect the shadow price lambda so that total spend == budget.
        lo, hi = 1e-12, float((H[active] / k[active]).max())  # g'(0) upper bound
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            tot, s = total_spend(mid)
            if tot > cfg.budget_lkr:
                lo = mid  # spending too much -> raise price
            else:
                hi = mid
        _, spend = total_spend(hi)

    # Drop dust allocations below the operational minimum.
    spend[spend < cfg.min_spend_lkr] = 0.0

    incremental_liters = _response(spend, H, k)
    incremental_revenue = incremental_liters * bpl
    return {
        "spend_lkr": spend,
        "incremental_liters": incremental_liters,
        "incremental_revenue_lkr": incremental_revenue,
        "headroom_value_lkr": value,
        "k_scale": k,
        "spend_cap_lkr": s_max,
    }


def optimize_province_spend(
    intelligence: pd.DataFrame,
    cfg: AllocationConfig = AllocationConfig(),
) -> tuple[pd.DataFrame, dict]:
    """Run the optimizer for one province.

    Parameters
    ----------
    intelligence : the Outlet Intelligence table (must include province, headroom_liters,
        bill_per_liter, competitive_intensity, predicted_potential_liters).

    Returns
    -------
    (allocation_df, summary_dict)
        allocation_df: one row per province outlet with spend + expected impact.
    """
    prov = intelligence[intelligence["province"] == cfg.province].copy()
    if prov.empty:
        raise ValueError(f"No outlets found for province {cfg.province!r}.")

    res = allocate_budget(
        prov["headroom_liters"].to_numpy(),
        prov["bill_per_liter"].to_numpy(),
        prov["competitive_intensity"].to_numpy(),
        cfg,
    )
    prov["Trade_Spend_Allocation_LKR"] = np.round(res["spend_lkr"], 2)
    prov["expected_incremental_liters"] = np.round(res["incremental_liters"], 2)
    prov["expected_incremental_revenue_lkr"] = np.round(res["incremental_revenue_lkr"], 2)
    prov["headroom_value_lkr"] = np.round(res["headroom_value_lkr"], 2)
    prov["spend_cap_lkr"] = np.round(res["spend_cap_lkr"], 2)
    prov["liters_per_1000_lkr"] = np.where(
        prov["Trade_Spend_Allocation_LKR"] > 0,
        prov["expected_incremental_liters"] / (prov["Trade_Spend_Allocation_LKR"] / 1000.0),
        0.0,
    ).round(2)

    funded = prov["Trade_Spend_Allocation_LKR"] > 0
    summary = {
        "province": cfg.province,
        "budget_lkr": cfg.budget_lkr,
        "outlets_in_province": int(len(prov)),
        "outlets_funded": int(funded.sum()),
        "total_allocated_lkr": float(prov["Trade_Spend_Allocation_LKR"].sum()),
        "budget_utilization": float(prov["Trade_Spend_Allocation_LKR"].sum() / cfg.budget_lkr),
        "expected_incremental_liters": float(prov["expected_incremental_liters"].sum()),
        "expected_incremental_revenue_lkr": float(prov["expected_incremental_revenue_lkr"].sum()),
        "blended_liters_per_1000_lkr": float(
            prov["expected_incremental_liters"].sum() / (cfg.budget_lkr / 1000.0)
        ),
        "roi_revenue_to_spend": float(
            prov["expected_incremental_revenue_lkr"].sum() / max(prov["Trade_Spend_Allocation_LKR"].sum(), 1.0)
        ),
        "model": {
            "response": "g(s)=H*(1-exp(-s/k))",
            "alpha": cfg.alpha, "beta": cfg.beta, "cap_frac": cfg.cap_frac,
            "min_spend_lkr": cfg.min_spend_lkr,
            "solver": "Lagrangian water-filling (KKT bisection)",
        },
    }

    out_cols = [
        "Outlet_ID", "Outlet_Type", "Outlet_Size", "dominant_distributor",
        "observed_mean_monthly_liters", "predicted_potential_liters", "headroom_liters",
        "competitive_intensity", "bill_per_liter",
        "Trade_Spend_Allocation_LKR", "expected_incremental_liters",
        "expected_incremental_revenue_lkr", "liters_per_1000_lkr",
    ]
    out_cols = [c for c in out_cols if c in prov.columns]
    allocation = prov[out_cols].sort_values(
        "Trade_Spend_Allocation_LKR", ascending=False
    ).reset_index(drop=True)
    return allocation, summary


def write_submission(
    allocation: pd.DataFrame, cfg: AllocationConfig = AllocationConfig(),
    results_dir: Path = RESULTS,
) -> Path:
    """Write the required teamname_budget_allocations.csv (Outlet_ID + spend)."""
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    out = results_dir / f"{cfg.team_name}_budget_allocations.csv"
    allocation[["Outlet_ID", "Trade_Spend_Allocation_LKR"]].to_csv(out, index=False)
    return out


if __name__ == "__main__":
    import json

    from src.intelligence import load_intelligence_table

    cfg = AllocationConfig()
    intel = load_intelligence_table()
    alloc, summary = optimize_province_spend(intel, cfg)

    detail_path = RESULTS / f"{cfg.team_name}_budget_allocations_detailed.csv"
    alloc.to_csv(detail_path, index=False)
    sub_path = write_submission(alloc, cfg)
    (RESULTS / "budget_allocation_summary.json").write_text(json.dumps(summary, indent=2))

    print(json.dumps(summary, indent=2))
    print(f"\nSubmission : {sub_path}")
    print(f"Detailed   : {detail_path}")
