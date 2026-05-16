"""Step 4: POI quality audit + Sri Lanka coverage caveats for the report.

Outputs `output/poi_coverage_report.md` to be cited in the 5-page PDF.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import CATEGORIES, COVERAGE_REPORT_MD, DATA_POIS, POI_FEATURES_PARQUET
from src.qa import audit_features, audit_pois


def main() -> None:
    if not POI_FEATURES_PARQUET.exists():
        raise FileNotFoundError(f"{POI_FEATURES_PARQUET} missing -- run 03_build_features.py first")

    feats = pd.read_parquet(POI_FEATURES_PARQUET)
    feat_audit = audit_features(feats)

    poi_summary: list[dict] = []
    for cat_name in CATEGORIES.keys():
        path = DATA_POIS / f"{cat_name}.parquet"
        if path.exists():
            pois = pd.read_parquet(path)
            poi_summary.append(audit_pois(pois, cat_name))
        else:
            poi_summary.append({"category": cat_name, "n_pois": 0, "note": "extraction file missing"})

    write_coverage_report(poi_summary, feat_audit)
    print(f"[poi] wrote {COVERAGE_REPORT_MD}")


def write_coverage_report(poi_summary: list[dict], feat_audit: dict) -> None:
    lines: list[str] = []
    lines.append("# POI Coverage Report (Sri Lanka, OSM via Geofabrik PBF)")
    lines.append("")
    lines.append("Honest disclosure of what the OSM dump covers and does NOT cover for Sri Lanka.")
    lines.append("Cited verbatim in the 5-page PDF report.")
    lines.append("")
    lines.append("## Per-category POI counts")
    lines.append("")
    lines.append("| Category | POIs found | Note |")
    lines.append("| --- | ---: | --- |")
    for s in poi_summary:
        lines.append(f"| {s.get('category', '?')} | {s.get('n_pois', 0):,} | {s.get('note', '')} |")
    lines.append("")
    lines.append("## Outlet-feature coverage")
    lines.append("")
    lines.append(f"- Outlets in feature table: {feat_audit['n_outlets']:,}")
    lines.append(f"- Outlets with at least one POI within 2km: {feat_audit['outlets_with_any_poi_2km_pct']:.1f}%")
    lines.append(f"- Outlets with valid coordinates: {feat_audit['outlets_with_valid_coords']:,}")
    lines.append(f"- Outlets with NaN POI features (invalid coordinates): {feat_audit['outlets_with_nan_features']:,}")
    lines.append("")
    lines.append("## Known Sri Lanka OSM coverage caveats")
    lines.append("")
    lines.append("- **Well-mapped categories:** schools, hospitals, banks, hotels, religious places.")
    lines.append("  The OSM Sri Lanka project has high completeness for institutional POIs.")
    lines.append("- **Patchy categories:** small kades (corner shops), independent grocers,")
    lines.append("  small bakeries. These are the SAME outlets the team is predicting for, so")
    lines.append("  POI-derived demand evidence will be biased toward urban / institutional zones.")
    lines.append("- **Bus stops:** dense in Colombo + Kandy + Galle, sparse in rural North-Western.")
    lines.append("- **Restaurants vs eateries:** OSM tags `restaurant` / `cafe` / `food_court` capture")
    lines.append("  formal eateries; informal roadside food carts are usually missing.")
    lines.append("")
    lines.append("## Implications for the methodology")
    lines.append("")
    lines.append("- POI features are USED as a *demand catchment signal*, not as ground truth.")
    lines.append("- The constraint score therefore weights POI-derived signals at 20%, and")
    lines.append("  uses peer-frontier residuals + plateau detection (which depend only on internal")
    lines.append("  data) at 50% + 30% respectively.")
    lines.append("- Outlets with no POI within 2km default to `dist_nearest = 2 * max_radius` and")
    lines.append("  `count = 0` -- this is a deliberate, defensible default per Channel 4 of the")
    lines.append("  research brief.")
    lines.append("")
    COVERAGE_REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    COVERAGE_REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
