from typing import List, Dict, Optional, Tuple, Any
from collections import deque
import copy

from .models import PageAccessEvent, SimulationResult
from .memory_manager import MemoryManager
from .analyzer import WorkloadAnalyzer
from .policies.base import BasePolicy
from .policies.fifo import FIFOPolicy
from .policies.lru import LRUPolicy
from .policies.clock import ClockPolicy
from .policies.lfu import LFUPolicy
from .policies.arc import ARCPolicy
from .policies.optimal import OptimalPolicy

class AdaptiveEngine:
    """
    Workload-Adaptive Page Replacement Engine.
    Dynamically identifies workload characteristics using a sliding window analyzer
    and automatically switches the active eviction policy to maximize cache hits.
    """

    def __init__(
        self,
        num_frames: int = 4,
        window_size: int = 25,
        switch_cooldown: int = 5,
        initial_policy: str = "LRU"
    ):
        self.num_frames = num_frames
        self.window_size = window_size
        self.switch_cooldown = switch_cooldown
        self.analyzer = WorkloadAnalyzer(window_size=window_size, frame_count=num_frames)

        self.policy_catalog: Dict[str, BasePolicy] = {
            "FIFO": FIFOPolicy(),
            "LRU": LRUPolicy(),
            "Clock": ClockPolicy(),
            "LFU": LFUPolicy(),
            "ARC": ARCPolicy(capacity=num_frames),
        }

        self.active_policy_name = initial_policy if initial_policy in self.policy_catalog else "LRU"
        self.memory_manager = MemoryManager(
            num_frames=num_frames,
            policy=self.policy_catalog[self.active_policy_name]
        )

        self.window: deque = deque(maxlen=window_size)
        self.steps_since_last_switch: int = switch_cooldown
        self.history: List[PageAccessEvent] = []
        self.switch_history: List[Dict[str, Any]] = []

    def reset(self) -> None:
        """Resets engine state and all internal policy instances."""
        for pol in self.policy_catalog.values():
            pol.reset()
        self.memory_manager.reset()
        self.window.clear()
        self.steps_since_last_switch = self.switch_cooldown
        self.history.clear()
        self.switch_history.clear()
        self.active_policy_name = "LRU"
        self.memory_manager.set_policy(self.policy_catalog["LRU"])

    def _get_policy_instance(self, name: str) -> BasePolicy:
        if name not in self.policy_catalog:
            return self.policy_catalog["LRU"]
        return self.policy_catalog[name]

    def run_trace(self, reference_stream: List[int]) -> SimulationResult:
        """
        Executes a full reference stream adaptively.
        """
        self.reset()
        cumulative_hit_rates: List[float] = []
        policy_timeline: List[str] = []

        for step, page in enumerate(reference_stream):
            self.window.append(page)
            self.steps_since_last_switch += 1

            # Workload characterization
            analysis = self.analyzer.analyze_window(list(self.window))
            recommended = analysis.get("recommended_policy", self.active_policy_name)
            pattern = analysis.get("pattern", "Unknown")
            reason = analysis.get("reason", "")

            switch_occurred = False
            switch_reason = None

            # Policy switching evaluation
            if (
                recommended != self.active_policy_name
                and self.steps_since_last_switch >= self.switch_cooldown
                and len(self.window) >= min(8, self.window_size // 3)
            ):
                old_policy = self.active_policy_name
                self.active_policy_name = recommended
                new_policy = self._get_policy_instance(recommended)
                self.memory_manager.set_policy(new_policy)
                self.steps_since_last_switch = 0
                switch_occurred = True
                switch_reason = f"Switched {old_policy} -> {recommended}: {pattern} ({reason})"
                self.switch_history.append({
                    "step": step,
                    "from_policy": old_policy,
                    "to_policy": recommended,
                    "pattern": pattern,
                    "reason": reason,
                })

            # Execute memory reference
            is_hit, evicted = self.memory_manager.access(page)

            # Record event
            event = PageAccessEvent(
                step=step,
                page=page,
                is_hit=is_hit,
                evicted=evicted,
                active_policy=self.active_policy_name,
                frames=[f if f is not None else -1 for f in self.memory_manager.get_resident_frames()],
                detected_pattern=pattern,
                switch_occurred=switch_occurred,
                switch_reason=switch_reason
            )
            self.history.append(event)
            policy_timeline.append(self.active_policy_name)

            curr_hit_rate = (self.memory_manager.hits / self.memory_manager.total_accesses) * 100.0
            cumulative_hit_rates.append(round(curr_hit_rate, 2))

        total = self.memory_manager.total_accesses
        hits = self.memory_manager.hits
        faults = self.memory_manager.faults
        hit_rate = (hits / total * 100.0) if total > 0 else 0.0
        fault_rate = (faults / total * 100.0) if total > 0 else 0.0

        return SimulationResult(
            policy_name="Adaptive Engine",
            total_accesses=total,
            hits=hits,
            faults=faults,
            hit_rate=round(hit_rate, 2),
            fault_rate=round(fault_rate, 2),
            history=self.history,
            switch_history=self.switch_history,
            policy_timeline=policy_timeline,
            cumulative_hit_rates=cumulative_hit_rates,
        )

def run_single_policy(
    policy_name: str,
    stream: List[int],
    num_frames: int
) -> SimulationResult:
    """
    Simulates a baseline static policy on the given reference stream.
    """
    if policy_name == "FIFO":
        pol = FIFOPolicy()
    elif policy_name == "LRU":
        pol = LRUPolicy()
    elif policy_name == "Clock":
        pol = ClockPolicy()
    elif policy_name == "LFU":
        pol = LFUPolicy()
    elif policy_name == "ARC":
        pol = ARCPolicy(capacity=num_frames)
    elif policy_name in ("Optimal", "Optimal (MIN)", "MIN"):
        pol = OptimalPolicy(future_references=stream)
    else:
        pol = LRUPolicy()

    mm = MemoryManager(num_frames=num_frames, policy=pol)
    history: List[PageAccessEvent] = []
    cumulative_hit_rates: List[float] = []

    for step, page in enumerate(stream):
        is_hit, evicted = mm.access(page)
        event = PageAccessEvent(
            step=step,
            page=page,
            is_hit=is_hit,
            evicted=evicted,
            active_policy=policy_name,
            frames=[f if f is not None else -1 for f in mm.get_resident_frames()],
        )
        history.append(event)
        rate = (mm.hits / mm.total_accesses) * 100.0
        cumulative_hit_rates.append(round(rate, 2))

    total = mm.total_accesses
    hits = mm.hits
    faults = mm.faults
    hit_rate = (hits / total * 100.0) if total > 0 else 0.0
    fault_rate = (faults / total * 100.0) if total > 0 else 0.0

    return SimulationResult(
        policy_name=policy_name,
        total_accesses=total,
        hits=hits,
        faults=faults,
        hit_rate=round(hit_rate, 2),
        fault_rate=round(fault_rate, 2),
        history=history,
        switch_history=[],
        policy_timeline=[policy_name] * total,
        cumulative_hit_rates=cumulative_hit_rates,
    )

def run_benchmark_suite(
    stream: List[int],
    num_frames: int = 4,
    window_size: int = 25
) -> Dict[str, SimulationResult]:
    """
    Runs the reference stream across all benchmark policies and the Adaptive Engine.
    """
    policies = ["Optimal (MIN)", "FIFO", "LRU", "Clock", "LFU", "ARC"]
    results: Dict[str, SimulationResult] = {}

    # Run Adaptive Engine
    adaptive = AdaptiveEngine(num_frames=num_frames, window_size=window_size)
    results["Adaptive Engine"] = adaptive.run_trace(stream)

    # Run Static Baselines
    for pol_name in policies:
        results[pol_name] = run_single_policy(pol_name, stream, num_frames)

    return results
