"""
OSH020: Workload-Adaptive Page Replacement Engine
Virtual Memory Simulator
"""

from .memory_manager import MemoryManager
from .analyzer import WorkloadAnalyzer
from .workload import WorkloadGenerator
from .adaptive_engine import AdaptiveEngine, run_single_policy, run_benchmark_suite
from .models import PatternType, PageAccessEvent, SimulationResult, WorkloadConfig, ChallengeReport
from .challenges import (
    run_challenge_1,
    run_challenge_2,
    run_challenge_3,
    run_challenge_4,
    run_challenge_5,
    run_all_challenges,
)

__version__ = "1.0.0"

__all__ = [
    "MemoryManager",
    "WorkloadAnalyzer",
    "WorkloadGenerator",
    "AdaptiveEngine",
    "run_single_policy",
    "run_benchmark_suite",
    "PatternType",
    "PageAccessEvent",
    "SimulationResult",
    "WorkloadConfig",
    "ChallengeReport",
    "run_challenge_1",
    "run_challenge_2",
    "run_challenge_3",
    "run_challenge_4",
    "run_challenge_5",
    "run_all_challenges",
]
