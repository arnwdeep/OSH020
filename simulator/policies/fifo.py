from collections import deque
from typing import Set, Deque
from .base import BasePolicy

class FIFOPolicy(BasePolicy):
    """
    First-In, First-Out (FIFO) Page Replacement.
    Replaces the page that has been in memory for the longest time.
    """
    def __init__(self):
        super().__init__("FIFO")
        self.queue: Deque[int] = deque()

    def record_access(self, page: int, is_hit: bool) -> None:
        if not is_hit:
            if page not in self.queue:
                self.queue.append(page)

    def choose_victim(self, resident_pages: Set[int]) -> int:
        while self.queue:
            victim = self.queue.popleft()
            if victim in resident_pages:
                return victim
        # Fallback if queue somehow empty or desynced
        return next(iter(resident_pages))

    def sync_state(self, resident_pages: Set[int]) -> None:
        # Retain order for existing pages, remove non-resident, append newly resident
        new_queue = deque([p for p in self.queue if p in resident_pages])
        for p in resident_pages:
            if p not in new_queue:
                new_queue.append(p)
        self.queue = new_queue

    def init_from_history(self, resident_pages: Set[int], history: List[int]) -> None:
        """
        Reconstructs FIFO insertion queue for resident pages from observed history.
        Resident pages are ordered by their first arrival in the reference stream.
        """
        self.queue.clear()
        if not resident_pages:
            return

        first_seen = {}
        for idx, p in enumerate(history):
            if p in resident_pages and p not in first_seen:
                first_seen[p] = idx

        sorted_pages = sorted(
            resident_pages,
            key=lambda p: first_seen.get(p, 999999)
        )
        self.queue = deque(sorted_pages)

    def get_metadata_size(self) -> int:
        return len(self.queue)

    def reset(self) -> None:
        self.queue.clear()

    def clone(self) -> "FIFOPolicy":
        cp = FIFOPolicy()
        cp.queue = deque(self.queue)
        return cp
