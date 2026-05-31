"""Functional Explainable-AI layer (Final Round, Section 4.1).

Two stages:
  1. drivers.py   -- turn a model prediction into a structured, signed driver
                     payload (score, key drivers, local signals, constraints).
  2. narrative.py -- an LLM translates that payload into plain business language,
                     with a deterministic offline template fallback so the app
                     always runs (no API key / no network required).
"""

from __future__ import annotations

from .drivers import DriverPayload, PanelStats, build_driver_payload, compute_panel_stats
from .narrative import explain_outlet, render_offline_narrative

__all__ = [
    "DriverPayload",
    "PanelStats",
    "build_driver_payload",
    "compute_panel_stats",
    "explain_outlet",
    "render_offline_narrative",
]
