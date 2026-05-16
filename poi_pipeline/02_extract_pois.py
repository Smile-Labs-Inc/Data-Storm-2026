"""Step 2: parse the PBF and write one parquet per POI category.

Uses pyrosm. For each of the 9 categories defined in config.CATEGORIES,
loads matching POIs, drops rows with no coordinates, dedupes near-duplicates
(5 decimal lat/lon snap + lowercase name), writes to data/pois/<cat>.parquet.

No CLI flags -- edit config.py.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import CATEGORIES, DATA_POIS, PBF_PATH, ensure_dirs
from src.pbf_loader import iter_category_pois


def dedupe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["_lat5"] = df["Latitude"].round(5)
    df["_lon5"] = df["Longitude"].round(5)
    df["_name"] = df["name"].fillna("").str.strip().str.lower()
    deduped = df.drop_duplicates(subset=["_lat5", "_lon5", "_name"]).drop(columns=["_lat5", "_lon5", "_name"])
    return deduped.reset_index(drop=True)


def main() -> None:
    ensure_dirs()
    if not PBF_PATH.exists():
        raise FileNotFoundError(f"{PBF_PATH} missing -- run 01_download_pbf.py first")

    summary: list[dict] = []
    for cat_name, tag_filter in CATEGORIES.items():
        t0 = time.time()
        print(f"[poi] extracting category={cat_name}  filter={tag_filter}")
        try:
            df = iter_category_pois(PBF_PATH, tag_filter)
        except Exception as e:
            print(f"[poi]   FAILED: {type(e).__name__}: {e}")
            df = pd.DataFrame(columns=["Latitude", "Longitude", "name", "category"])

        df["category"] = cat_name
        df = dedupe(df)
        out_path = DATA_POIS / f"{cat_name}.parquet"
        df.to_parquet(out_path, index=False)
        elapsed = time.time() - t0
        print(f"[poi]   wrote {out_path}  rows={len(df)}  elapsed={elapsed:.1f}s")
        summary.append({"category": cat_name, "rows": len(df), "elapsed_sec": round(elapsed, 1)})

    pd.DataFrame(summary).to_csv(DATA_POIS / "_extraction_summary.csv", index=False)
    print("\n[poi] all categories done.")


if __name__ == "__main__":
    main()
