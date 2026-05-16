"""End-to-end orchestrator. Single entry point for the whole pipeline.

Usage (no CLI flags -- edit CONFIG block):
    python run_pipeline.py

What it does (in order):
  1. Bronze: copy raw CSVs to data/bronze/ + audit hash log
  2. Silver: apply reusable DQ checks, normalise, write rejected store
  3. Gold:   build outlet-level feature table (merges POI features if present)
  4. Modeling:
       - robust lower bound
       - XGBoost 2.0 multi-quantile frontier
       - SFA fit (parallel methodology track)
       - PCA + frontier-residual + plateau constraint score
       - Bootstrap size x type caps
       - Final latent_potential
       - Manski bands
  5. Reporting: DAG, sensitivity sweep, 6-item validation
  6. Submission: writes Results/teamname_predictions.csv with Outlet_ID + Maximum_Monthly_Liters
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.cleaning import (  # noqa: E402
    clean_outlet_coordinates,
    clean_transactions,
    dedupe_holidays,
    normalize_outlet_master,
    score_seasonality,
    write_silver,
)
from src.features import build_gold_features  # noqa: E402
from src.modeling import (  # noqa: E402
    bootstrap_size_type_caps,
    build_constraint_score,
    chernozhukov_hong_correction,
    fit_multi_quantile,
    fit_sfa,
    latent_potential,
    predict_quantiles,
    robust_lower_bound,
    technical_efficiency,
)
from src.modeling.censored_qr import build_censoring_proxy  # noqa: E402
from src.modeling.conformal import conformalised_qr, split_by_outlet  # noqa: E402
from src.modeling.sfa import predict_frontier as sfa_predict_frontier  # noqa: E402
from src.quality import (  # noqa: E402
    domain_check,
    duplicate_check,
    geospatial_bounds_check,
    null_check,
    range_check,
    referential_integrity_check,
    summarise_checks,
    write_rejected,
)
from src.quality.checks import write_summary_md  # noqa: E402
from src.reporting import (  # noqa: E402
    build_dag,
    compute_manski_bands,
    run_validation_suite,
    sensitivity_sweep,
)

# ============================ CONFIG ============================
RAW_DIR = ROOT.parent / "datastorm-7-0-rotaract"
BRONZE_DIR = ROOT / "data" / "bronze"
SILVER_DIR = ROOT / "data" / "silver"
SILVER_REJECTED_DIR = ROOT / "data" / "silver_rejected"
GOLD_DIR = ROOT / "data" / "gold"
RESULTS_DIR = ROOT / "Results"
DOCS_DIR = ROOT / "Docs"
REPORTS_DIR = ROOT / "Reports"
POI_FEATURES_PARQUET = ROOT / "poi_pipeline" / "output" / "poi_features.parquet"

USE_CENSORING_CORRECTION = True
USE_SFA = True
TEAM_NAME = "teamname"
# ================================================================


VALID_DISTRIBUTORS = {
    "DIST_W_01", "DIST_W_02", "DIST_W_03",
    "DIST_C_01", "DIST_C_02", "DIST_C_03",
    "DIST_NW_01", "DIST_NW_02",
    "DIST_S_01", "DIST_S_02",
}


def _ensure_dirs() -> None:
    for d in (BRONZE_DIR, SILVER_DIR, SILVER_REJECTED_DIR, GOLD_DIR, RESULTS_DIR, DOCS_DIR, REPORTS_DIR / "figures"):
        d.mkdir(parents=True, exist_ok=True)


def bronze_ingest() -> dict[str, Path]:
    print("\n== Bronze: ingesting raw files ==")
    files = [
        "outlet_master.csv",
        "outlet_coordinates.csv",
        "transactions_history_final.csv",
        "distributor_seasonality_details.csv",
        "holiday_list.csv",
    ]
    audit: list[dict] = []
    out: dict[str, Path] = {}
    for name in files:
        src = RAW_DIR / name
        if not src.exists():
            raise FileNotFoundError(f"raw file missing: {src}")
        dst = BRONZE_DIR / name
        shutil.copy2(src, dst)
        sha = hashlib.sha256(dst.read_bytes()).hexdigest()[:12]
        audit.append({"file": name, "size_bytes": dst.stat().st_size, "sha256_12": sha})
        out[name.replace(".csv", "")] = dst
        print(f"  {name}  size={dst.stat().st_size:,}  sha={sha}")

    pd.DataFrame(audit).to_csv(BRONZE_DIR / "_ingestion_audit.csv", index=False)
    return out


def silver_clean(bronze: dict[str, Path]) -> dict[str, pd.DataFrame]:
    print("\n== Silver: DQ checks + cleaning + rejected records ==")

    outlet_master = pd.read_csv(bronze["outlet_master"])
    outlet_coords = pd.read_csv(bronze["outlet_coordinates"])
    transactions = pd.read_csv(bronze["transactions_history_final"])
    seasonality = pd.read_csv(bronze["distributor_seasonality_details"])
    holidays = pd.read_csv(bronze["holiday_list"])

    valid_outlet_ids = set(outlet_master["Outlet_ID"].astype(str))

    qc = []
    qc.append(duplicate_check(outlet_master, ["Outlet_ID"], dataset="outlet_master"))
    qc.append(null_check(outlet_master, ["Outlet_ID"], dataset="outlet_master"))
    qc.append(range_check(outlet_master, "Cooler_Count", min_value=0, max_value=200, dataset="outlet_master"))

    qc.append(duplicate_check(outlet_coords, ["Outlet_ID"], dataset="outlet_coordinates"))
    qc.append(null_check(outlet_coords, ["Outlet_ID", "Latitude", "Longitude"], dataset="outlet_coordinates"))
    qc.append(referential_integrity_check(outlet_coords, "Outlet_ID", valid_outlet_ids, dataset="outlet_coordinates"))
    qc.append(geospatial_bounds_check(outlet_coords, dataset="outlet_coordinates"))

    qc.append(null_check(transactions, ["Outlet_ID", "Year", "Month", "Distributor_ID", "SKU_ID"], dataset="transactions_history"))
    qc.append(referential_integrity_check(transactions, "Outlet_ID", valid_outlet_ids, dataset="transactions_history"))
    qc.append(domain_check(transactions, "Distributor_ID", VALID_DISTRIBUTORS, dataset="transactions_history"))
    qc.append(range_check(transactions, "Year", min_value=2023, max_value=2026, dataset="transactions_history"))
    qc.append(range_check(transactions, "Month", min_value=1, max_value=12, dataset="transactions_history"))
    qc.append(range_check(transactions, "Volume_Liters", min_value=0, inclusive=False, dataset="transactions_history"))
    qc.append(range_check(transactions, "Total_Bill_Value", min_value=0, inclusive=False, dataset="transactions_history"))

    qc.append(duplicate_check(seasonality, ["Distributor_ID", "Year", "Month"], dataset="distributor_seasonality"))
    qc.append(domain_check(seasonality, "Distributor_ID", VALID_DISTRIBUTORS, dataset="distributor_seasonality"))

    qc.append(null_check(holidays, ["Date", "Holiday_Name", "Holiday_Type"], dataset="holiday_list"))

    summary = summarise_checks(qc)
    write_summary_md(summary, DOCS_DIR / "data_quality_report.md")
    write_rejected(qc, SILVER_REJECTED_DIR)

    om_silver = normalize_outlet_master(outlet_master)
    coords_valid, coords_rej = clean_outlet_coordinates(outlet_coords)
    txn_valid, txn_rej = clean_transactions(transactions, valid_outlet_ids, VALID_DISTRIBUTORS)
    hol_silver, hol_rej = dedupe_holidays(holidays)
    seas_silver = score_seasonality(seasonality)

    write_silver(om_silver, "outlet_master", SILVER_DIR)
    write_silver(coords_valid, "outlet_coordinates", SILVER_DIR, SILVER_REJECTED_DIR, coords_rej)
    write_silver(txn_valid, "transactions_history", SILVER_DIR, SILVER_REJECTED_DIR, txn_rej)
    write_silver(hol_silver, "holiday_list", SILVER_DIR, SILVER_REJECTED_DIR, hol_rej)
    write_silver(seas_silver, "distributor_seasonality", SILVER_DIR)

    print(f"  rejected files in {SILVER_REJECTED_DIR}: {[p.name for p in SILVER_REJECTED_DIR.glob('*.csv')]}")
    print(f"  DQ summary written to {DOCS_DIR / 'data_quality_report.md'}")

    return {
        "outlet_master": om_silver,
        "outlet_coordinates_valid": coords_valid,
        "transactions": txn_valid,
        "distributor_seasonality": seas_silver,
        "holidays": hol_silver,
    }


def gold_features(silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    print("\n== Gold: outlet x feature table ==")
    poi_features: pd.DataFrame | None = None
    if POI_FEATURES_PARQUET.exists():
        poi_features = pd.read_parquet(POI_FEATURES_PARQUET)
        print(f"  loaded POI features: {poi_features.shape}")
    else:
        print(f"  no POI features at {POI_FEATURES_PARQUET}; proceeding without external POI")

    gold = build_gold_features(
        outlet_master=silver["outlet_master"],
        coords_valid=silver["outlet_coordinates_valid"],
        transactions=silver["transactions"],
        distributor_seasonality=silver["distributor_seasonality"],
        holidays=silver["holidays"],
        poi_features=poi_features,
        out_path=GOLD_DIR / "outlet_features.parquet",
    )
    print(f"  Gold table shape: {gold.shape}")
    return gold


def model_and_predict(gold: pd.DataFrame, silver: dict[str, pd.DataFrame]) -> pd.DataFrame:
    print("\n== Modeling ==")
    transactions = silver["transactions"]
    monthly = (
        transactions.groupby(["Outlet_ID", "Year", "Month"], as_index=False)
        .agg(monthly_volume=("Volume_Liters", "sum"))
    )

    print("  -> robust lower bound")
    lb = robust_lower_bound(transactions)

    feature_cols_numeric = [c for c in [
        "Cooler_Count",
        "observed_mean_monthly_liters",
        "observed_median_monthly_liters",
        "observed_p90_monthly_liters",
        "observed_p95_monthly_liters",
        "active_months",
        "sku_breadth",
        "transaction_count",
        "bill_per_liter_mean",
        "january_seasonality_score",
        "january_holiday_count",
        "outlet_count_1km",
        "outlet_count_2km",
        "outlet_count_5km",
        "same_distributor_outlet_count_5km",
        "nearest_outlet_distance_km",
        "catchment_density_score",
        "cannibalisation_count_200m",
    ] if c in gold.columns]

    poi_decay_cols = [c for c in gold.columns if c.endswith("_decay_score") and c != "catchment_density_score"]
    feature_cols_numeric.extend(poi_decay_cols)

    X = gold[feature_cols_numeric].copy()
    X = X.fillna(X.median(numeric_only=True)).fillna(0.0)
    y = gold["observed_max_monthly_liters"].fillna(0.0)

    if USE_CENSORING_CORRECTION:
        print("  -> Chernozhukov-Hong censoring correction")
        delta_per_month = build_censoring_proxy(monthly)
        is_censored_outlet = (
            delta_per_month.groupby("Outlet_ID")["delta"].mean() > 0.3
        ).astype(int)
        delta = pd.Series(0, index=gold.index)
        delta_map = is_censored_outlet.reindex(gold["Outlet_ID"]).fillna(0).astype(int).values
        delta = pd.Series(delta_map, index=gold.index)
        X_train, y_train, corr = chernozhukov_hong_correction(X, y, delta)
        print(f"     kept {corr.n_uncensored_kept}/{corr.n_total} for q90 fit")
    else:
        X_train, y_train = X, y

    print("  -> XGBoost multi-quantile fit")
    model_bundle = fit_multi_quantile(X_train, y_train)
    quantile_preds = predict_quantiles(model_bundle, X)
    quantile_preds["Outlet_ID"] = gold["Outlet_ID"].values
    quantile_preds.to_parquet(GOLD_DIR / "quantile_predictions.parquet", index=False)

    # FIX N4 (council round 2): wire Conformalised QR for calibrated coverage.
    # Uses an outlet-level holdout (not random rows) to avoid leakage.
    print("  -> Conformalised QR (calibrated [q05, q95] interval)")
    try:
        cq_in = pd.DataFrame({"Outlet_ID": gold["Outlet_ID"].values}).merge(
            quantile_preds, on="Outlet_ID", how="left"
        )
        cq_in["y"] = y.values
        train_idx, calib_idx = split_by_outlet(cq_in, "Outlet_ID", test_size=0.20)
        q_lo_col = "q05" if "q05" in cq_in.columns else "q50"
        q_hi_col = "q95" if "q95" in cq_in.columns else "q90"
        cqr = conformalised_qr(
            y_calib=cq_in.loc[calib_idx, "y"].values,
            q_lo_calib=cq_in.loc[calib_idx, q_lo_col].values,
            q_hi_calib=cq_in.loc[calib_idx, q_hi_col].values,
            q_lo_test=cq_in[q_lo_col].values,
            q_hi_test=cq_in[q_hi_col].values,
            alpha=0.10,
        )
        intervals = pd.DataFrame({
            "Outlet_ID": gold["Outlet_ID"].values,
            "cqr_lower": cqr.q_lo_calibrated,
            "cqr_upper": cqr.q_hi_calibrated,
        })
        intervals.to_csv(RESULTS_DIR / "conformal_intervals.csv", index=False)
        print(f"     CQR done: target_coverage={cqr.coverage_target:.0%} empirical={cqr.empirical_coverage:.1%} adj={cqr.quantile_correction:.2f}")
    except Exception as e:
        print(f"     CQR skipped: {type(e).__name__}: {e}")

    if USE_SFA:
        print("  -> SFA fit (truncated-normal u)")
        try:
            # FIX N3 (council round 2): drop observed_* columns from SFA X.
            # They are deterministic functions of the target (log(observed_max))
            # and cause sigma_u -> 0, TE -> 1 -- the SFA collapses to OLS.
            leaky_cols = {
                "observed_mean_monthly_liters",
                "observed_median_monthly_liters",
                "observed_p90_monthly_liters",
                "observed_p95_monthly_liters",
            }
            sfa_feature_cols = [c for c in feature_cols_numeric if c not in leaky_cols]
            sfa_X = X[sfa_feature_cols].copy()
            sfa_fit = fit_sfa(sfa_X, y, log_target=True)
            te = technical_efficiency(sfa_fit, sfa_X, y, log_target=True)
            sfa_frontier = sfa_predict_frontier(sfa_fit, sfa_X, log_target=True)
            # FIX O3 (council round 2): floor at zero (volume cannot be negative).
            sfa_frontier = sfa_frontier.clip(lower=0.0)
            print(f"     SFA: sigma_v={sfa_fit.sigma_v:.3f}, sigma_u={sfa_fit.sigma_u:.3f}, lambda={sfa_fit.lambda_:.3f}, converged={sfa_fit.converged}")
            sfa_out = pd.DataFrame({
                "Outlet_ID": gold["Outlet_ID"].values,
                "sfa_frontier": sfa_frontier.values,
                "technical_efficiency": te.values,
            })
            sfa_out.to_parquet(GOLD_DIR / "sfa_predictions.parquet", index=False)
        except Exception as e:
            print(f"     SFA failed: {type(e).__name__}: {e} -- continuing without SFA")
            sfa_out = None
    else:
        sfa_out = None

    print("  -> constraint score")
    cs = build_constraint_score(features=gold, transactions=transactions)

    print("  -> bootstrap size x type caps")
    cap_table = bootstrap_size_type_caps(gold)
    cap_table.to_csv(GOLD_DIR / "cap_table.csv", index=False)

    frontier = pd.DataFrame({
        "Outlet_ID": gold["Outlet_ID"].values,
        "frontier_q90": quantile_preds["q90"].values if "q90" in quantile_preds.columns else quantile_preds.iloc[:, -2].values,
    })

    if sfa_out is not None:
        frontier = frontier.merge(sfa_out[["Outlet_ID", "sfa_frontier"]], on="Outlet_ID", how="left")
        frontier["frontier_q90"] = (
            0.6 * frontier["frontier_q90"] + 0.4 * frontier["sfa_frontier"].fillna(frontier["frontier_q90"])
        )

    print("  -> final latent_potential")
    preds = latent_potential(gold, cs, lb, frontier, cap_table)
    return preds, quantile_preds, cap_table, lb


def write_submission(preds: pd.DataFrame) -> Path:
    print("\n== Submission ==")
    sub = preds[["Outlet_ID", "Maximum_Monthly_Liters"]].copy()
    sub["Maximum_Monthly_Liters"] = sub["Maximum_Monthly_Liters"].round(3)
    sub_path = RESULTS_DIR / f"{TEAM_NAME}_predictions.csv"
    sub.to_csv(sub_path, index=False)
    full_path = RESULTS_DIR / f"{TEAM_NAME}_predictions_full_20000.csv"
    sub.to_csv(full_path, index=False)
    print(f"  wrote {sub_path} ({len(sub)} rows)")
    return sub_path


def reports_and_validation(
    preds: pd.DataFrame,
    quantile_preds: pd.DataFrame,
    cap_table: pd.DataFrame,
    lower_bounds: pd.DataFrame,
    gold: pd.DataFrame,
    silver: dict[str, pd.DataFrame],
    submission_path: Path,
) -> None:
    print("\n== Reports + validation ==")

    print("  -> Manski bands")
    bands = compute_manski_bands(preds, cap_table=cap_table)
    bands.to_csv(RESULTS_DIR / "manski_bands.csv", index=False)

    print("  -> DAG figure")
    build_dag(REPORTS_DIR / "figures")

    print("  -> sensitivity sweep")
    try:
        sensitivity_sweep(
            features=gold,
            transactions=silver["transactions"],
            lower_bounds=lower_bounds,
            multi_q_predictions=quantile_preds,
            cap_table=cap_table,
            out_dir=REPORTS_DIR / "figures",
        )
    except Exception as e:
        print(f"     sensitivity sweep failed: {type(e).__name__}: {e}")

    print("  -> 6-item validation")
    sub = pd.read_csv(submission_path)
    historical_max = gold.set_index("Outlet_ID")["observed_max_monthly_liters"]
    bucket_keys = gold[["Outlet_ID", "Outlet_Type", "Outlet_Size"]].copy()
    result = run_validation_suite(
        submission=sub,
        outlet_master=silver["outlet_master"],
        historical_max=historical_max,
        cap_table=cap_table,
        bucket_keys=bucket_keys,
        out_dir=RESULTS_DIR,
    )
    print(f"  validation: all_passed={result.all_passed}")
    for c in result.checks:
        mark = "OK" if c.passed else "FAIL"
        print(f"    [{mark}] {c.name} -- {c.detail}")


def main() -> None:
    t0 = time.time()
    _ensure_dirs()

    bronze = bronze_ingest()
    silver = silver_clean(bronze)
    gold = gold_features(silver)
    preds, quantile_preds, cap_table, lb = model_and_predict(gold, silver)
    sub_path = write_submission(preds)
    reports_and_validation(preds, quantile_preds, cap_table, lb, gold, silver, sub_path)

    elapsed = time.time() - t0
    print(f"\n== END-TO-END DONE in {elapsed:.1f}s ==")
    print(f"   submission -> {sub_path}")

    summary = {
        "elapsed_sec": round(elapsed, 1),
        "submission": str(sub_path),
        "median_uplift": round(float(preds["uplift_ratio"].median()), 3),
        "mean_uplift": round(float(preds["uplift_ratio"].mean()), 3),
        "max_uplift": round(float(preds["uplift_ratio"].max()), 3),
    }
    (RESULTS_DIR / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
