"""Structured per-outlet driver payload for the XAI layer.

Translates one row of the Outlet Intelligence table into the signed, ranked
"why" signals that the LLM narrates. Each driver carries:

  name        short label
  direction   "increases" | "decreases" | "neutral"  (effect on potential)
  weight      0..1 relative importance within this outlet's explanation
  detail      one-line technical statement (numbers, percentiles)

Grouped into: drivers (model attribution), local_signals (spatial environment),
constraints (operational limits). This mirrors the four bullet groups the brief
asks the XAI module to surface: predicted score, key model drivers, local
environment signals, and operational constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PanelStats:
    """Reference percentiles computed once across the full panel."""
    headroom_p50: float
    headroom_p90: float
    competitor_p50: float
    competitor_p90: float
    cooler_by_size: dict[str, float]
    uplift_p50: float
    uplift_p90: float


def compute_panel_stats(intel: pd.DataFrame) -> PanelStats:
    cooler_by_size = (
        intel.groupby("Outlet_Size")["Cooler_Count"].median().to_dict()
        if "Outlet_Size" in intel.columns else {}
    )
    return PanelStats(
        headroom_p50=float(intel["headroom_liters"].quantile(0.50)),
        headroom_p90=float(intel["headroom_liters"].quantile(0.90)),
        competitor_p50=float(intel["competitor_count_500m"].quantile(0.50)),
        competitor_p90=float(intel["competitor_count_500m"].quantile(0.90)),
        cooler_by_size={str(k): float(v) for k, v in cooler_by_size.items()},
        uplift_p50=float(intel["uplift_ratio"].quantile(0.50)),
        uplift_p90=float(intel["uplift_ratio"].quantile(0.90)),
    )


@dataclass
class DriverPayload:
    outlet_id: str
    outlet_type: str
    outlet_size: str
    province: str
    distributor: str
    predicted_potential_liters: float
    normal_baseline_liters: float
    best_month_liters: float
    uplift_vs_best_month: float
    uplift_vs_normal: float
    drivers: list[dict[str, Any]] = field(default_factory=list)
    local_signals: list[dict[str, Any]] = field(default_factory=list)
    constraints: list[dict[str, Any]] = field(default_factory=list)
    allocation: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _pct(value: float, p50: float, p90: float) -> str:
    if value >= p90:
        return "top-decile"
    if value >= p50:
        return "above-median"
    return "below-median"


def build_driver_payload(
    row: pd.Series,
    stats: PanelStats,
    allocation_row: pd.Series | None = None,
) -> DriverPayload:
    """Build the signed driver payload for a single outlet row."""
    potential = float(row["predicted_potential_liters"])
    normal = float(row["observed_mean_monthly_liters"])
    best = float(row["observed_max_monthly_liters"])
    headroom = float(row.get("headroom_liters", max(potential - normal, 0.0)))
    comp = float(row.get("competitor_count_500m", 0.0))
    comp_intensity = float(row.get("competitive_intensity", 0.0))
    coolers = float(row.get("Cooler_Count", 0.0))
    size = str(row.get("Outlet_Size", "Unknown"))
    active_months = int(row.get("active_months", 0))

    payload = DriverPayload(
        outlet_id=str(row["Outlet_ID"]),
        outlet_type=str(row.get("Outlet_Type", "Unknown")),
        outlet_size=size,
        province=str(row.get("province", "Unknown")),
        distributor=str(row.get("dominant_distributor", "Unknown")),
        predicted_potential_liters=round(potential, 1),
        normal_baseline_liters=round(normal, 1),
        best_month_liters=round(best, 1),
        uplift_vs_best_month=round(potential / best, 3) if best > 0 else 1.0,
        uplift_vs_normal=round(potential / normal, 3) if normal > 0 else 1.0,
    )

    # --- model drivers -----------------------------------------------------
    headroom_band = _pct(headroom, stats.headroom_p50, stats.headroom_p90)
    payload.drivers.append({
        "name": "Latent demand headroom",
        "direction": "increases",
        "weight": min(1.0, headroom / max(stats.headroom_p90, 1.0)),
        "detail": (
            f"Untapped headroom of {headroom:,.0f} L/month over the normal {normal:,.0f} L "
            f"baseline ({headroom_band} across the panel) — the model judges the outlet is "
            f"selling below what its location can support."
        ),
    })

    uplift = payload.uplift_vs_best_month
    payload.drivers.append({
        "name": "Best-month anchor",
        "direction": "increases" if uplift > 1.01 else "neutral",
        "weight": min(1.0, max(uplift - 1.0, 0.0) / max(stats.uplift_p90 - 1.0, 0.01)),
        "detail": (
            f"Potential is floored at the best observed month ({best:,.0f} L) and lifted "
            f"{(uplift - 1) * 100:,.0f}% above it, reflecting demand seen only in peak periods."
        ),
    })

    consistency_dir = "increases" if active_months >= 6 else "decreases"
    payload.drivers.append({
        "name": "Sales-history depth",
        "direction": consistency_dir,
        "weight": 0.4 if active_months >= 6 else 0.6,
        "detail": (
            f"{active_months} active months of history "
            + ("give the estimate solid support." if active_months >= 6
               else "is thin, so the estimate leans more on location signals than own sales.")
        ),
    })

    # --- local environment signals ----------------------------------------
    if comp_intensity >= 0.66:
        cdir, cdetail = "decreases", (
            f"{comp:.0f} competing outlets within 500 m (top-decile density) — a crowded "
            f"market caps how much volume any single outlet can capture."
        )
    elif comp_intensity <= 0.2:
        cdir, cdetail = "increases", (
            f"Only {comp:.0f} competitors within 500 m — a relatively untapped catchment, "
            f"so headroom is easier to convert."
        )
    else:
        cdir, cdetail = "neutral", (
            f"{comp:.0f} competitors within 500 m — a moderately contested catchment."
        )
    payload.local_signals.append({
        "name": "Competitive catchment density",
        "direction": cdir,
        "weight": comp_intensity,
        "detail": cdetail,
    })

    # --- operational constraints -------------------------------------------
    typical_coolers = stats.cooler_by_size.get(size, coolers)
    if coolers < typical_coolers:
        payload.constraints.append({
            "name": "Cooler capacity",
            "direction": "decreases",
            "weight": min(1.0, (typical_coolers - coolers) / max(typical_coolers, 1.0)),
            "detail": (
                f"{coolers:.0f} cooler(s) vs a typical {typical_coolers:.0f} for {size} outlets — "
                f"limited chilled space throttles replenishment and realisable volume."
            ),
        })
    else:
        payload.constraints.append({
            "name": "Cooler capacity",
            "direction": "neutral",
            "weight": 0.2,
            "detail": (
                f"{coolers:.0f} cooler(s), at or above the {size}-outlet norm — cold space is "
                f"not the binding constraint here."
            ),
        })

    # --- attach spend recommendation if available --------------------------
    if allocation_row is not None and float(allocation_row.get("Trade_Spend_Allocation_LKR", 0)) > 0:
        payload.allocation = {
            "trade_spend_lkr": round(float(allocation_row["Trade_Spend_Allocation_LKR"]), 2),
            "expected_incremental_liters": round(
                float(allocation_row.get("expected_incremental_liters", 0.0)), 1),
            "expected_incremental_revenue_lkr": round(
                float(allocation_row.get("expected_incremental_revenue_lkr", 0.0)), 2),
            "liters_per_1000_lkr": round(float(allocation_row.get("liters_per_1000_lkr", 0.0)), 2),
        }

    # rank drivers by weight (most important first)
    payload.drivers.sort(key=lambda d: d["weight"], reverse=True)
    return payload
