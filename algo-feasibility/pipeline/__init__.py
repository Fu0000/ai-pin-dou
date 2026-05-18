"""Algorithm feasibility pipeline (ADR-014).

Each module exposes a single pure function returning timing-friendly outputs.
Once M0 passes, these modules become seeds for backend/algo/* (ADR-028).
"""
from .pipeline import run_pipeline

__all__ = ["run_pipeline"]
