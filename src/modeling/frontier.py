"""Frontier estimation via XGBoost 2.0 multi-quantile.

One fit produces all quantiles at once via `reg:quantileerror` with
`quantile_alpha=[...]`. Monotone constraints encode "more cooler / SKU /
catchment -> higher frontier" (per research brief Channel 3 + Channel 6).

Includes isotonic per-row post-sort to fix any quantile crossing
(Chernozhukov-Fernandez-Val-Galichon 2010).

Falls back to LightGBM if XGBoost 2.0 isn't available.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_QUANTILES = (0.50, 0.75, 0.90, 0.95)


def monotone_constraints(feature_columns: list[str]) -> dict[str, int]:
    """Encode domain-driven monotonicity on numeric features."""
    monotone_up = {
        "Cooler_Count",
        "sku_breadth",
        "catchment_density_score",
        "outlet_count_1km",
        "outlet_count_2km",
        "outlet_count_5km",
        "active_months",
        "transaction_count",
        "january_seasonality_score",
    }
    monotone_down = {
        "cannibalisation_count_200m",
        "nearest_outlet_distance_km",
    }
    out: dict[str, int] = {}
    for c in feature_columns:
        if c in monotone_up:
            out[c] = 1
        elif c in monotone_down:
            out[c] = -1
        else:
            out[c] = 0
    return out


def fit_multi_quantile(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    quantiles: tuple[float, ...] = DEFAULT_QUANTILES,
    monotone: dict[str, int] | None = None,
    n_estimators: int = 800,
    learning_rate: float = 0.05,
    max_depth: int = 6,
    random_state: int = 42,
):
    """Fit one model that predicts ALL quantiles. Returns (model, backend, quantiles)."""
    feature_columns = list(X_train.columns)
    if monotone is None:
        monotone = monotone_constraints(feature_columns)

    try:
        import xgboost as xgb

        if hasattr(xgb, "__version__") and int(xgb.__version__.split(".")[0]) >= 2:
            mc = tuple(monotone.get(c, 0) for c in feature_columns)
            model = xgb.XGBRegressor(
                objective="reg:quantileerror",
                quantile_alpha=list(quantiles),
                n_estimators=n_estimators,
                learning_rate=learning_rate,
                max_depth=max_depth,
                random_state=random_state,
                monotone_constraints=mc,
                tree_method="hist",
                n_jobs=-1,
                enable_categorical=True,
            )
            model.fit(X_train, y_train)
            return model, "xgboost2", tuple(quantiles)
    except Exception:
        pass

    # Fallback: LightGBM with one model per quantile
    import lightgbm as lgb

    models: dict[float, lgb.LGBMRegressor] = {}
    for q in quantiles:
        m = lgb.LGBMRegressor(
            objective="quantile",
            alpha=q,
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=random_state,
            monotone_constraints=[monotone.get(c, 0) for c in feature_columns],
            n_jobs=-1,
            verbose=-1,
        )
        m.fit(X_train, y_train)
        models[q] = m
    return models, "lightgbm-perq", tuple(quantiles)


def predict_quantiles(
    model_bundle: tuple,
    X: pd.DataFrame,
) -> pd.DataFrame:
    """Returns DataFrame with one column per quantile (e.g., q50, q75, q90, q95)."""
    model, backend, quantiles = model_bundle
    if backend == "xgboost2":
        preds = model.predict(X)
        if preds.ndim == 1:
            preds = preds.reshape(-1, 1)
        cols = [f"q{int(q * 100):02d}" for q in quantiles]
        df = pd.DataFrame(preds, columns=cols, index=X.index)
    else:
        cols = [f"q{int(q * 100):02d}" for q in quantiles]
        arr = np.column_stack([model[q].predict(X) for q in quantiles])
        df = pd.DataFrame(arr, columns=cols, index=X.index)

    # isotonic per-row sort fixes quantile crossing
    arr = np.sort(df.values, axis=1)
    df.loc[:, :] = arr
    return df
