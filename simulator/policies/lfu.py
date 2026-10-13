from collections import defaultdict
from typing import Set, Dict
from .base import BasePolicy

class LFUPolicy(BasePolicy):
    """
    Least Frequently Used (LFU) Page Replacement.
    Replaces the page with the lowest reference frequency count.
    """
    def __init__(self):
        super().__init__("LFU")
        self.freq: Dict[int, int] = defaultdict(int)
        self.entry_time: Dict[int, int] = {}
        self.time_counter: int = 0

    def record_access(self, page: int, is_hit: bool) -> None:
        self.time_counter += 1
        self.freq[page] += 1
        if page not in self.entry_time:
            self.entry_time[page] = self.time_counter

    def choose_victim(self, resident_pages: Set[int]) -> int:
        min_freq = float('inf')
        oldest_time = float('inf')
        victim = None

        for p in resident_pages:
            f = self.freq[p]
            t = self.entry_time.get(p, 0)
            if f < min_freq or (f == min_freq and t < oldest_time):
                min_freq = f
                oldest_time = t
                victim = p

        if victim is not None:
            self.freq.pop(victim, None)
            self.entry_time.pop(victim, None)
            return victim

        return next(iter(resident_pages))

    def sync_state(self, resident_pages: Set[int]) -> None:
        to_del = [p for p in self.freq if p not in resident_pages]
        for p in to_del:
            self.freq.pop(p, None)
            self.entry_time.pop(p, None)
        for p in resident_pages:
            if p not in self.freq:
                self.freq[p] = 1
                self.entry_time[p] = self.time_counter

    def get_metadata_size(self) -> int:
        return len(self.freq) + len(self.entry_time)

    def reset(self) -> None:
        self.freq.clear()
        self.entry_time.clear()
        self.time_counter = 0

    def clone(self) -> "LFUPolicy":
        cp = LFUPolicy()
        cp.freq = defaultdict(int, self.freq)
        cp.entry_time = dict(self.entry_time)
        cp.time_counter = self.time_counter
        return cp
