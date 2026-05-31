"""Outlet Intelligence layer (Final Round).

Assembles a single decision-ready table per outlet by joining the raw challenge
CSVs with the final latent-potential predictions. This table is the shared input
for the spend optimizer, the XAI narrative layer, and the Streamlit web app.

Deliberately depends only on pandas / numpy (+ optional scikit-learn for the
competitive-density BallTree) so the Final-Round deliverables run for judges
without materialising the full Bronze/Silver/Gold parquet pipeline.
"""

from __future__ import annotations

from .build_table import (
    PROVINCE_BY_PREFIX,
    build_intelligence_table,
    load_intelligence_table,
    province_of_distributor,
)

__all__ = [
    "PROVINCE_BY_PREFIX",
    "build_intelligence_table",
    "load_intelligence_table",
    "province_of_distributor",
]
