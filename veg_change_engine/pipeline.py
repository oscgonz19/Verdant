"""
Main pipeline orchestrator for vegetation change analysis.

Note:
    This module provides backward-compatible re-exports from services/.
    For new code, prefer importing directly from services.change_orchestrator.
"""

# Re-export everything from services.change_orchestrator
from services.change_orchestrator import (
    # Main analysis functions
    analyze_vegetation_change,
    run_full_analysis,
    quick_preview,
    get_period_summary,
    # Orchestrator class (new)
    ChangeOrchestrator,
    # Job management (new)
    AnalysisJob,
    AnalysisStatus,
    JobStore,
)

__all__ = [
    # Backward-compatible functions
    "analyze_vegetation_change",
    "run_full_analysis",
    "quick_preview",
    "get_period_summary",
    # New exports
    "ChangeOrchestrator",
    "AnalysisJob",
    "AnalysisStatus",
    "JobStore",
]
