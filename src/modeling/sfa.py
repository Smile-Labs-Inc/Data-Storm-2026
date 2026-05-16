"""Stochastic Frontier Analysis (Aigner-Lovell-Schmidt 1977).

Model:
    y_i = x_i' beta + v_i - u_i
    v_i ~ Normal(0, sigma_v)            # symmetric noise
    u_i ~ |Normal(0, sigma_u)|           # one-sided inefficiency >= 0

Closed-form log-likelihood (Aigner et al. 1977):
    f(eps) = (2 / sigma) * phi(eps/sigma) * Phi(-lambda * eps / sigma)
    where sigma^2 = sigma_v^2 + sigma_u^2  and lambda = sigma_u / sigma_v

Technical efficiency (Jondrow-Lovell-Materov-Schmidt 1982):
    TE_i = exp(-E[u_i | eps_i])
    E[u | eps] = sigma_star * (phi(z) / (1 - Phi(z)) - z)
    where sigma_star^2 = sigma_v^2 * sigma_u^2 / sigma^2,
          z = -lambda * eps / sigma

We fit by direct numerical MLE with `scipy.optimize.minimize`.
No external SFA library needed.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm
from sklearn.preprocessing import StandardScaler


@dataclass
class SFAResult:
    beta: np.ndarray
    sigma_v: float
    sigma_u: float
    feature_names: list[str]
    log_likelihood: float
    converged: bool
    scaler: StandardScaler

    @property
    def sigma(self) -> float:
        return float(np.sqrt(self.sigma_v ** 2 + self.sigma_u ** 2))

    @property
    def lambda_(self) -> float:
        return float(self.sigma_u / max(self.sigma_v, 1e-9))


def _neg_log_lik(params: np.ndarray, X: np.ndarray, y: np.ndarray) -> float:
    k = X.shape[1]
    beta = params[:k]
    log_sigma_v = params[k]
    log_sigma_u = params[k + 1]
    sigma_v = np.exp(log_sigma_v)
    sigma_u = np.exp(log_sigma_u)
    sigma = np.sqrt(sigma_v ** 2 + sigma_u ** 2)
    lambda_ = sigma_u / max(sigma_v, 1e-9)

    eps = y - X @ beta
    z = eps / max(sigma, 1e-9)
    log_phi = -0.5 * np.log(2 * np.pi) - 0.5 * z ** 2
    log_Phi = norm.logcdf(-lambda_ * z)
    ll = np.log(2.0) - np.log(max(sigma, 1e-9)) + log_phi + log_Phi
    return -float(np.sum(ll))


def fit_sfa(
    X: pd.DataFrame,
    y: pd.Series,
    log_target: bool = True,
    max_iter: int = 1000,
    n_restarts: int = 3,
) -> SFAResult:
    """Fit y = X beta + v - u. Pass `log_target=True` if y is volume on the natural scale."""
    feature_names = ["__const__"] + list(X.columns)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X.fillna(X.median(numeric_only=True)).values)
    X_arr = np.column_stack([np.ones(len(X)), X_scaled])

    y_arr = np.log1p(y.values) if log_target else y.values

    k = X_arr.shape[1]
    ols_beta, *_ = np.linalg.lstsq(X_arr, y_arr, rcond=None)
    resid = y_arr - X_arr @ ols_beta
    sigma_init = float(np.std(resid))

    p0 = np.concatenate([ols_beta, [np.log(max(sigma_init * 0.7, 1e-3)), np.log(max(sigma_init * 0.7, 1e-3))]])

    # Bounds: betas unbounded; log_sigma_v, log_sigma_u ∈ [-5, 3] → sigma ∈ [0.007, 20]
    bounds = [(-np.inf, np.inf)] * k + [(-5.0, 3.0), (-5.0, 3.0)]

    best_res = None
    rng = np.random.default_rng(42)
    for trial in range(n_restarts):
        p = p0 if trial == 0 else p0 + rng.normal(0, 0.2, size=p0.shape)
        res = minimize(
            _neg_log_lik,
            p,
            args=(X_arr, y_arr),
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": max_iter, "disp": False, "ftol": 1e-9, "gtol": 1e-3},
        )
        if best_res is None or res.fun < best_res.fun:
            best_res = res

    res = best_res
    beta = res.x[:k]
    sigma_v = float(np.exp(res.x[k]))
    sigma_u = float(np.exp(res.x[k + 1]))
    return SFAResult(
        beta=beta,
        sigma_v=sigma_v,
        sigma_u=sigma_u,
        feature_names=feature_names,
        log_likelihood=-float(res.fun),
        converged=bool(res.success),
        scaler=scaler,
    )


def technical_efficiency(
    fit: SFAResult,
    X: pd.DataFrame,
    y: pd.Series,
    log_target: bool = True,
) -> pd.Series:
    """Per-row TE in (0, 1]. 1 = on the frontier; <1 = below frontier."""
    X_scaled = fit.scaler.transform(X.fillna(X.median(numeric_only=True)).values)
    X_arr = np.column_stack([np.ones(len(X)), X_scaled])
    y_arr = np.log1p(y.values) if log_target else y.values
    eps = y_arr - X_arr @ fit.beta
    sigma = fit.sigma
    sigma_star_sq = (fit.sigma_v ** 2 * fit.sigma_u ** 2) / max(sigma ** 2, 1e-12)
    sigma_star = np.sqrt(sigma_star_sq)
    z = -fit.lambda_ * eps / max(sigma, 1e-9)
    pdf = norm.pdf(z)
    sf = 1.0 - norm.cdf(z)
    sf = np.clip(sf, 1e-12, 1.0)
    e_u_given_eps = sigma_star * (pdf / sf - z)
    e_u_given_eps = np.clip(e_u_given_eps, 0.0, None)
    te = np.exp(-e_u_given_eps)
    return pd.Series(te, index=X.index, name="technical_efficiency")


def predict_frontier(
    fit: SFAResult,
    X: pd.DataFrame,
    log_target: bool = True,
) -> pd.Series:
    X_scaled = fit.scaler.transform(X.fillna(X.median(numeric_only=True)).values)
    X_arr = np.column_stack([np.ones(len(X)), X_scaled])
    yhat = X_arr @ fit.beta
    if log_target:
        yhat = np.expm1(yhat)
    return pd.Series(yhat, index=X.index, name="sfa_frontier")
