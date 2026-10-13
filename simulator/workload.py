import random
from typing import List, Tuple, Optional

try:
    from .models import PatternType
except (ImportError, ValueError):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from simulator.models import PatternType


class WorkloadGenerator:
    """
    Generates reference streams for page replacement benchmarking:
    - Sequential (Scan)
    - Loop (Cyclic)
    - Random
    - Locality (Reuse-Heavy / 80-20)
    - Mixed (Phased transitions across time)
    - Belady's Anomaly benchmark trace
    """

    @staticmethod
    def generate_sequential(total_requests: int = 100, start_page: int = 0) -> List[int]:
        """Generates a pure scan stream where each page is accessed once in increasing order."""
        return [start_page + i for i in range(total_requests)]

    @staticmethod
    def generate_loop(total_requests: int = 100, loop_size: int = 5, start_page: int = 0) -> List[int]:
        """Generates a repeating loop of loop_size pages (e.g. 0, 1, 2, 3, 4, 0, 1, ...)."""
        return [start_page + (i % loop_size) for i in range(total_requests)]

    @staticmethod
    def generate_random(total_requests: int = 100, unique_pages: int = 20, seed: Optional[int] = None) -> List[int]:
        """Generates uniformly distributed random page accesses."""
        rng = random.Random(seed)
        return [rng.randint(0, unique_pages - 1) for _ in range(total_requests)]

    @staticmethod
    def generate_locality(
        total_requests: int = 100,
        working_set_size: int = 4,
        total_pages: int = 25,
        locality_prob: float = 0.85,
        seed: Optional[int] = None
    ) -> List[int]:
        """
        Generates a 80/20 style locality stream where working_set_size pages
        account for locality_prob fraction of all accesses.
        """
        rng = random.Random(seed)
        hot_pages = list(range(0, working_set_size))
        cold_pages = list(range(working_set_size, total_pages))
        stream: List[int] = []

        for _ in range(total_requests):
            if rng.random() < locality_prob or not cold_pages:
                stream.append(rng.choice(hot_pages))
            else:
                stream.append(rng.choice(cold_pages))
        return stream

    @staticmethod
    def generate_mixed(
        phase_length: int = 50,
        frame_count: int = 4,
        seed: Optional[int] = 42
    ) -> Tuple[List[int], List[Tuple[int, int, str]]]:
        """
        Generates a realistic multi-phased workload that dynamically transitions:
        Phase 1: Locality (Reuse-heavy)
        Phase 2: Sequential Scan
        Phase 3: Loop bigger than RAM (loop_size = frame_count + 1)
        Phase 4: Random
        Phase 5: Re-entry into strong Locality
        Returns:
            stream: Full list of page references
            phases: List of (start_idx, end_idx, phase_name)
        """
        rng = random.Random(seed)
        stream: List[int] = []
        phases: List[Tuple[int, int, str]] = []

        # Phase 1: Locality
        p1_start = len(stream)
        p1 = WorkloadGenerator.generate_locality(
            total_requests=phase_length,
            working_set_size=frame_count,
            total_pages=frame_count * 4,
            locality_prob=0.90,
            seed=seed
        )
        stream.extend(p1)
        phases.append((p1_start, len(stream), "Locality (Reuse-Heavy)"))

        # Phase 2: Sequential Scan
        p2_start = len(stream)
        p2 = WorkloadGenerator.generate_sequential(
            total_requests=phase_length,
            start_page=100
        )
        stream.extend(p2)
        phases.append((p2_start, len(stream), "Sequential Scan"))

        # Phase 3: Loop bigger than RAM (Pathological for pure LRU)
        p3_start = len(stream)
        p3 = WorkloadGenerator.generate_loop(
            total_requests=phase_length,
            loop_size=frame_count + 1,
            start_page=0
        )
        stream.extend(p3)
        phases.append((p3_start, len(stream), f"Cyclic Loop (Size {frame_count + 1} > Frames {frame_count})"))

        # Phase 4: Random noise
        p4_start = len(stream)
        p4 = WorkloadGenerator.generate_random(
            total_requests=phase_length,
            unique_pages=frame_count * 5,
            seed=(seed + 7) if seed else None
        )
        stream.extend(p4)
        phases.append((p4_start, len(stream), "Random Access"))

        # Phase 5: Re-converged Locality
        p5_start = len(stream)
        p5 = WorkloadGenerator.generate_locality(
            total_requests=phase_length,
            working_set_size=frame_count,
            total_pages=frame_count * 3,
            locality_prob=0.92,
            seed=(seed + 19) if seed else None
        )
        stream.extend(p5)
        phases.append((p5_start, len(stream), "Locality Recovery"))

        return stream, phases

    @staticmethod
    def get_belady_anomaly_trace() -> List[int]:
        """
        The classic 12-reference sequence demonstrating Belady's Anomaly for FIFO:
        References: 1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5
        With 3 frames: 9 page faults
        With 4 frames: 10 page faults!
        """
        return [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]

    @staticmethod
    def parse_trace_string(trace_str: str) -> List[int]:
        """Parses comma or whitespace separated integers into a page stream."""
        clean = trace_str.replace(",", " ").replace(";", " ")
        return [int(token) for token in clean.split() if token.strip().isdigit()]

if __name__ == "__main__":
    print("--- WorkloadGenerator Standalone Test ---")
    stream, phases = WorkloadGenerator.generate_mixed(phase_length=10, frame_count=4)
    print(f"Generated mixed stream of length {len(stream)}:")
    print(f"Stream: {stream[:25]} ...")
    for start, end, name in phases:
        print(f"  Range [{start:2d}..{end-1:2d}]: {name}")

