"""Conformalised Quantile Regression (Romano-Patterson-Candes NeurIPS 2019).

Wraps a multi-quantile regressor and gives a calibrated [q_lo, q_hi] interval
with empirical coverage >= 1 - alpha on a held-out outlet calibration set.

Why outlet-level holdout (not random rows): preserves outlet identity so
calibration mirrors the deployment distribution.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit


@dataclass
class CQRResult:
    q_lo_calibrated: np.ndarray
    q_hi_calibrated: np.ndarray
    coverage_target: float
    empirical_coverage: float
    quantile_correction: float


def _conformity_scores(y: np.ndarray, q_lo: np.ndarray, q_hi: np.ndarray) -> np.ndarray:
    return np.maximum(q_lo - y, y - q_hi)


def conformalised_qr(
    y_calib: np.ndarray,
    q_lo_calib: np.ndarray,
    q_hi_calib: np.ndarray,
    q_lo_test: np.ndarray,
    q_hi_test: np.ndarray,
    alpha: float = 0.10,
) -> CQRResult:
    """Inputs are arrays. Returns the calibrated test interval."""
    scores = _conformity_scores(y_calib, q_lo_calib, q_hi_calib)
    n = len(scores)
    k = int(np.ceil((n + 1) * (1 - alpha)))
    k = min(max(k, 1), n)
    qhat = float(np.sort(scores)[k - 1])

    cov_calib = float(np.mean((y_calib >= q_lo_calib - qhat) & (y_calib <= q_hi_calib + qhat)))

    return CQRResult(
        q_lo_calibrated=q_lo_test - qhat,
        q_hi_calibrated=q_hi_test + qhat,
        coverage_target=1 - alpha,
        empirical_coverage=cov_calib,
        quantile_correction=qhat,
    )


def split_by_outlet(
    df: pd.DataFrame,
    outlet_col: str = "Outlet_ID",
    test_size: float = 0.20,
    random_state: int = 42,
) -> tuple[pd.Index, pd.Index]:
    """Outlet-level holdout. Returns (train_idx, calib_idx)."""
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=random_state)
    train_idx, calib_idx = next(splitter.split(df, groups=df[outlet_col]))
    return df.index[train_idx], df.index[calib_idx]
