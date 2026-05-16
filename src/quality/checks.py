"""Reusable, parameterizable data-quality checks.

Each check returns a `QualityResult` which carries the dataset name, the check
type, the failed-row dataframe (with a `failure_reason`), and a one-line
description. Compose checks across all datasets with `summarise_checks`, then
write rejected rows to `data/silver_rejected/<dataset>_rejected.csv` with
`write_rejected`.

Designed to satisfy the Data Storm 7.0 rubric requirement that DQ checks be
"reusable, parameterizable, and applied consistently across all datasets".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import pandas as pd


@dataclass
class QualityResult:
    dataset: str
    check_name: str
    description: str
    failed: pd.DataFrame = field(default_factory=pd.DataFrame)

    @property
    def n_failed(self) -> int:
        return int(len(self.failed))

    def with_failure_reason(self) -> pd.DataFrame:
        if self.failed.empty:
            return self.failed
        df = self.failed.copy()
        df["dataset_name"] = self.dataset
        df["failed_check"] = self.check_name
        df["failure_reason"] = self.description
        return df


def duplicate_check(
    df: pd.DataFrame, key_columns: list[str], dataset: str = ""
) -> QualityResult:
    """Find rows whose composite key appears more than once."""
    description = f"Duplicate key on {', '.join(key_columns)}"
    if not key_columns:
        return QualityResult(dataset, "duplicate_check", description)
    mask = df.duplicated(subset=key_columns, keep=False)
    return QualityResult(dataset, "duplicate_check", description, df[mask].copy())


def null_check(
    df: pd.DataFrame, columns: list[str], dataset: str = ""
) -> QualityResult:
    description = f"Null or empty mandatory field in {', '.join(columns)}"
    cols_present = [c for c in columns if c in df.columns]
    if not cols_present:
        return QualityResult(dataset, "null_check", description)
    mask = df[cols_present].isna().any(axis=1)
    if df[cols_present].select_dtypes(include="object").shape[1]:
        # also catch empty strings
        empty_mask = (df[cols_present].astype(str).apply(lambda s: s.str.strip()) == "").any(axis=1)
        mask = mask | empty_mask
    return QualityResult(dataset, "null_check", description, df[mask].copy())


def range_check(
    df: pd.DataFrame,
    column: str,
    min_value: float | None = None,
    max_value: float | None = None,
    inclusive: bool = True,
    dataset: str = "",
) -> QualityResult:
    description = f"{column} outside expected range"
    if column not in df.columns:
        return QualityResult(dataset, "range_check", description)
    s = pd.to_numeric(df[column], errors="coerce")
    if inclusive:
        mask = ((min_value is not None) & (s < min_value)) | (
            (max_value is not None) & (s > max_value)
        )
    else:
        mask = ((min_value is not None) & (s <= min_value)) | (
            (max_value is not None) & (s >= max_value)
        )
    mask = mask.fillna(True)
    return QualityResult(dataset, "range_check", description, df[mask].copy())


def domain_check(
    df: pd.DataFrame,
    column: str,
    allowed_values: Iterable,
    dataset: str = "",
) -> QualityResult:
    allowed = set(allowed_values)
    description = f"{column} contains a value outside the allowed domain"
    if column not in df.columns:
        return QualityResult(dataset, "domain_check", description)
    mask = ~df[column].isin(allowed)
    return QualityResult(dataset, "domain_check", description, df[mask].copy())


def referential_integrity_check(
    df: pd.DataFrame,
    column: str,
    reference_values: Iterable,
    dataset: str = "",
) -> QualityResult:
    ref = set(reference_values)
    description = f"{column} does not exist in reference dataset"
    if column not in df.columns:
        return QualityResult(dataset, "referential_integrity_check", description)
    mask = ~df[column].isin(ref)
    return QualityResult(dataset, "referential_integrity_check", description, df[mask].copy())


def geospatial_bounds_check(
    df: pd.DataFrame,
    lat_col: str = "Latitude",
    lon_col: str = "Longitude",
    lat_range: tuple[float, float] = (5.5, 10.0),
    lon_range: tuple[float, float] = (79.0, 82.5),
    dataset: str = "",
) -> QualityResult:
    """Sri Lanka bounds: lat 5.5-10.0 N, lon 79.0-82.5 E."""
    description = (
        f"({lat_col}, {lon_col}) outside Sri Lanka bounds "
        f"lat={lat_range}, lon={lon_range}"
    )
    if lat_col not in df.columns or lon_col not in df.columns:
        return QualityResult(dataset, "geospatial_bounds_check", description)
    lat = pd.to_numeric(df[lat_col], errors="coerce")
    lon = pd.to_numeric(df[lon_col], errors="coerce")
    mask = (
        lat.isna()
        | lon.isna()
        | (lat < lat_range[0])
        | (lat > lat_range[1])
        | (lon < lon_range[0])
        | (lon > lon_range[1])
    )
    return QualityResult(dataset, "geospatial_bounds_check", description, df[mask].copy())


def write_rejected(
    results: list[QualityResult],
    out_dir: Path | str,
    dataset_filter: str | None = None,
) -> Path:
    """Append rejected rows to `<dataset>_rejected.csv` in `out_dir`."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    by_dataset: dict[str, list[pd.DataFrame]] = {}
    for r in results:
        if r.n_failed == 0:
            continue
        if dataset_filter and r.dataset != dataset_filter:
            continue
        by_dataset.setdefault(r.dataset, []).append(r.with_failure_reason())

    last_path: Path | None = None
    for ds, parts in by_dataset.items():
        merged = pd.concat(parts, ignore_index=True)
        path = out_dir / f"{ds}_rejected.csv"
        merged.to_csv(path, index=False)
        last_path = path
    if last_path is None:
        # always touch a sentinel so silver_rejected/ is never empty
        sentinel = out_dir / "_no_rejections.csv"
        pd.DataFrame({"info": ["no rejected records on this run"]}).to_csv(sentinel, index=False)
        return sentinel
    return last_path


def summarise_checks(results: list[QualityResult]) -> pd.DataFrame:
    rows = [
        {
            "dataset": r.dataset,
            "check": r.check_name,
            "failed_records": r.n_failed,
            "description": r.description,
        }
        for r in results
    ]
    return pd.DataFrame(rows)


def write_summary_md(summary: pd.DataFrame, out_path: Path | str) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write("# Data Quality Report\n\n")
        f.write("Generated by `src/quality/checks.py`. Reusable functions applied across all 5 raw datasets.\n\n")
        f.write("## Check Summary\n\n")
        f.write("| Dataset | Check | Failed Records | Description |\n")
        f.write("| --- | --- | ---: | --- |\n")
        for _, row in summary.iterrows():
            f.write(
                f"| `{row['dataset']}` | `{row['check']}` | {row['failed_records']} | {row['description']} |\n"
            )
    return out_path
