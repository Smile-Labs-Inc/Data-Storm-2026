"""Marketing-spend optimization (Final Round, Section 2.3).

Allocates a fixed promotional budget across the outlets of one province to
maximise *additional* sales volume over the normal historical baseline, under a
diminishing-returns response model solved with Lagrangian water-filling (KKT).
"""

from __future__ import annotations

from .spend_allocation import (
    AllocationConfig,
    allocate_budget,
    optimize_province_spend,
)

__all__ = [
    "AllocationConfig",
    "allocate_budget",
    "optimize_province_spend",
]
