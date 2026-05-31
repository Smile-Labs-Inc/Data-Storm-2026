"""Final-Round orchestrator (decision layer on top of the modeling pipeline).

Assumes `python run_pipeline.py` has already produced the predictions CSV
(Results/*predictions.csv). This script builds the Final-Round deliverables:

  1. Outlet Intelligence table      -> Results/outlet_intelligence.csv
  2. Western LKR 5M spend plan       -> Results/{team}_budget_allocations.csv (+ _detailed)
  3. XAI explanation sample (offline) -> Results/xai_samples.json
  4. Budget summary                  -> Results/budget_allocation_summary.json

Then launch the web app with:  streamlit run app/streamlit_app.py

Usage:
    python run_final_round.py            # build everything (offline XAI sample)
    python run_final_round.py --xai-live # use Anthropic API for the XAI sample
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.intelligence import build_intelligence_table  # noqa: E402
from src.optimization import AllocationConfig, optimize_province_spend  # noqa: E402
from src.optimization.spend_allocation import write_submission  # noqa: E402
from src.xai import build_driver_payload, compute_panel_stats, explain_outlet  # noqa: E402

RESULTS = ROOT / "Results"


def main(xai_live: bool = False, n_samples: int = 5) -> None:
    RESULTS.mkdir(exist_ok=True)

    print("[1/4] Building Outlet Intelligence table…")
    intel = build_intelligence_table(write_to=RESULTS / "outlet_intelligence.csv")
    print(f"      {len(intel):,} outlets · provinces: {intel['province'].value_counts().to_dict()}")

    print("[2/4] Optimizing Western Province LKR 5M spend…")
    cfg = AllocationConfig()
    alloc, summary = optimize_province_spend(intel, cfg)
    alloc.to_csv(RESULTS / f"{cfg.team_name}_budget_allocations_detailed.csv", index=False)
    sub = write_submission(alloc, cfg)
    (RESULTS / "budget_allocation_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"      funded {summary['outlets_funded']:,} outlets · "
          f"{summary['budget_utilization'] * 100:.1f}% of budget · "
          f"+{summary['expected_incremental_liters']:,.0f} L · submission -> {sub.name}")

    print(f"[3/4] Generating {n_samples} XAI explanation samples "
          f"({'live API' if xai_live else 'offline template'})…")
    stats = compute_panel_stats(intel)
    alloc_by_id = alloc.set_index("Outlet_ID")
    top = alloc.head(n_samples)["Outlet_ID"].tolist()
    samples = []
    for oid in top:
        row = intel[intel["Outlet_ID"] == oid].iloc[0]
        arow = alloc_by_id.loc[oid] if oid in alloc_by_id.index else None
        payload = build_driver_payload(row, stats, arow)
        res = explain_outlet(payload, force_offline=not xai_live)
        samples.append({"outlet_id": oid, "payload": payload.to_dict(), **res})
    (RESULTS / "xai_samples.json").write_text(json.dumps(samples, indent=2))
    print(f"      wrote {len(samples)} samples (source: {samples[0]['source']})")

    print("[4/4] Done. Launch the web app:")
    print("      streamlit run app/streamlit_app.py")


if __name__ == "__main__":
    main(xai_live="--xai-live" in sys.argv)
