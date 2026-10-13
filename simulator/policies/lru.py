from collections import OrderedDict
from typing import Set
from .base import BasePolicy

class LRUPolicy(BasePolicy):
    """
    Least Recently Used (LRU) Page Replacement.
    Replaces the page that has not been accessed for the longest period of time.
    """
    def __init__(self):
        super().__init__("LRU")
        # Keys in OrderedDict: least recent at front, most recent at back
        self.access_order: OrderedDict[int, None] = OrderedDict()

    def record_access(self, page: int, is_hit: bool) -> None:
        if page in self.access_order:
            self.access_order.move_to_end(page)
        else:
            self.access_order[page] = None

    def choose_victim(self, resident_pages: Set[int]) -> int:
        for p in self.access_order:
            if p in resident_pages:
                del self.access_order[p]
                return p
        victim = next(iter(resident_pages))
        if victim in self.access_order:
            del self.access_order[victim]
        return victim

    def sync_state(self, resident_pages: Set[int]) -> None:
        new_order = OrderedDict()
        for p in self.access_order:
            if p in resident_pages:
                new_order[p] = None
        for p in resident_pages:
            if p not in new_order:
                new_order[p] = None
        self.access_order = new_order

    def init_from_history(self, resident_pages: Set[int], history: List[int]) -> None:
        """
        Reconstructs LRU access order for resident pages from observed history.
        Resident pages are ordered from least recently accessed to most recently accessed.
        """
        self.access_order.clear()
        if not resident_pages:
            return

        last_seen = {}
        for idx, p in enumerate(history):
            if p in resident_pages:
                last_seen[p] = idx

        sorted_pages = sorted(
            resident_pages,
            key=lambda p: last_seen.get(p, -1)
        )
        for p in sorted_pages:
            self.access_order[p] = None

    def get_metadata_size(self) -> int:
        return len(self.access_order)

    def reset(self) -> None:
        self.access_order.clear()

    def clone(self) -> "LRUPolicy":
        cp = LRUPolicy()
        cp.access_order = OrderedDict((k, None) for k in self.access_order)
        return cp
