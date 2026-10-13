from typing import Set, List, Optional
import math
from .base import BasePolicy

class OptimalPolicy(BasePolicy):
    """
    Belady's Optimal (MIN) Algorithm (Offline Benchmark).
    Replaces the resident page whose next reference is furthest in the future.
    """
    def __init__(self, future_references: Optional[List[int]] = None):
        super().__init__("Optimal (MIN)")
        self.future_references: List[int] = future_references or []
        self.current_index: int = 0

    def set_future_references(self, references: List[int]) -> None:
        self.future_references = references
        self.current_index = 0

    def record_access(self, page: int, is_hit: bool) -> None:
        self.current_index += 1

    def choose_victim(self, resident_pages: Set[int]) -> int:
        furthest_distance = -1
        victim = None

        remaining_stream = self.future_references[self.current_index + 1:]
        next_indices = {}

        for p in resident_pages:
            try:
                next_pos = remaining_stream.index(p)
            except ValueError:
                next_pos = math.inf
            next_indices[p] = next_pos

            if next_pos > furthest_distance:
                furthest_distance = next_pos
                victim = p

        return victim if victim is not None else next(iter(resident_pages))

    def sync_state(self, resident_pages: Set[int]) -> None:
        pass

    def get_metadata_size(self) -> int:
        return len(self.future_references)

    def reset(self) -> None:
        self.current_index = 0

    def clone(self) -> "OptimalPolicy":
        cp = OptimalPolicy(list(self.future_references))
        cp.current_index = self.current_index
        return cp
