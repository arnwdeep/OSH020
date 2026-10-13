from typing import Set, List, Dict
from .base import BasePolicy

class ClockPolicy(BasePolicy):
    """
    Clock (Second-Chance) Page Replacement.
    Approximates LRU using a circular buffer and a use/reference bit.
    """
    def __init__(self):
        super().__init__("Clock")
        self.circular_buffer: List[int] = []
        self.ref_bits: Dict[int, int] = {}
        self.hand: int = 0

    def record_access(self, page: int, is_hit: bool) -> None:
        self.ref_bits[page] = 1
        if not is_hit and page not in self.circular_buffer:
            self.circular_buffer.append(page)

    def choose_victim(self, resident_pages: Set[int]) -> int:
        # Sync buffer with resident_pages if any discrepancy
        self.circular_buffer = [p for p in self.circular_buffer if p in resident_pages]
        if not self.circular_buffer:
            fallback = next(iter(resident_pages))
            return fallback

        if self.hand >= len(self.circular_buffer):
            self.hand = 0

        # Scan for page with ref_bit == 0
        attempts = 0
        max_attempts = len(self.circular_buffer) * 2 + 1
        while attempts < max_attempts:
            candidate = self.circular_buffer[self.hand]
            if self.ref_bits.get(candidate, 0) == 1:
                self.ref_bits[candidate] = 0
                self.hand = (self.hand + 1) % len(self.circular_buffer)
            else:
                victim = candidate
                del self.circular_buffer[self.hand]
                if victim in self.ref_bits:
                    del self.ref_bits[victim]
                if self.circular_buffer:
                    self.hand = self.hand % len(self.circular_buffer)
                else:
                    self.hand = 0
                return victim
            attempts += 1

        # Fallback if all cycled
        victim = self.circular_buffer.pop(0)
        self.ref_bits.pop(victim, None)
        self.hand = 0
        return victim

    def sync_state(self, resident_pages: Set[int]) -> None:
        new_buf = [p for p in self.circular_buffer if p in resident_pages]
        for p in resident_pages:
            if p not in new_buf:
                new_buf.append(p)
                self.ref_bits[p] = 1
        self.circular_buffer = new_buf
        if self.circular_buffer:
            self.hand = self.hand % len(self.circular_buffer)
        else:
            self.hand = 0

    def init_from_history(self, resident_pages: Set[int], history: List[int]) -> None:
        """Reconstructs clock buffer for resident pages from observed history."""
        # Order circular buffer by first arrival in history
        first_seen = {}
        for idx, p in enumerate(history):
            if p in resident_pages and p not in first_seen:
                first_seen[p] = idx
        sorted_pages = sorted(resident_pages, key=lambda p: first_seen.get(p, 999999))
        self.circular_buffer = list(sorted_pages)
        self.ref_bits = {p: 1 for p in sorted_pages}
        self.hand = 0

    def get_metadata_size(self) -> int:
        return len(self.circular_buffer) + len(self.ref_bits)

    def reset(self) -> None:
        self.circular_buffer.clear()
        self.ref_bits.clear()
        self.hand = 0

    def clone(self) -> "ClockPolicy":
        cp = ClockPolicy()
        cp.circular_buffer = list(self.circular_buffer)
        cp.ref_bits = dict(self.ref_bits)
        cp.hand = self.hand
        return cp
