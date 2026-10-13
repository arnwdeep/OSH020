from collections import OrderedDict
from typing import Set
from .base import BasePolicy

class ARCPolicy(BasePolicy):
    """
    Adaptive Replacement Cache (ARC).
    Self-tuning algorithm dynamically balancing between recency (T1) and frequency (T2).
    """
    def __init__(self, capacity: int = 4):
        super().__init__("ARC")
        self.c = capacity
        self.p = 0.0  # Target size of T1
        self.t1: OrderedDict[int, None] = OrderedDict()  # Recent resident
        self.t2: OrderedDict[int, None] = OrderedDict()  # Frequent resident
        self.b1: OrderedDict[int, None] = OrderedDict()  # Recent ghost history
        self.b2: OrderedDict[int, None] = OrderedDict()  # Frequent ghost history

    def set_capacity(self, capacity: int) -> None:
        self.c = capacity

    def record_access(self, page: int, is_hit: bool) -> None:
        if page in self.t1:
            del self.t1[page]
            self.t2[page] = None
        elif page in self.t2:
            self.t2.move_to_end(page)
        elif page in self.b1:
            delta = 1.0 if len(self.b1) == 0 else max(1.0, len(self.b2) / len(self.b1))
            self.p = min(float(self.c), self.p + delta)
            del self.b1[page]
            self.t2[page] = None
        elif page in self.b2:
            delta = 1.0 if len(self.b2) == 0 else max(1.0, len(self.b1) / len(self.b2))
            self.p = max(0.0, self.p - delta)
            del self.b2[page]
            self.t2[page] = None
        else:
            self.t1[page] = None

    def choose_victim(self, resident_pages: Set[int]) -> int:
        victim = None
        if len(self.t1) > 0 and ((len(self.t1) > self.p) or (len(self.b2) > 0 and len(self.t1) == int(self.p))):
            for p in self.t1:
                if p in resident_pages:
                    victim = p
                    break
            if victim is not None:
                del self.t1[victim]
                self.b1[victim] = None
                return victim

        for p in self.t2:
            if p in resident_pages:
                victim = p
                break
        if victim is not None:
            del self.t2[victim]
            self.b2[victim] = None
            return victim

        # Fallback to T1
        for p in self.t1:
            if p in resident_pages:
                victim = p
                break
        if victim is not None:
            del self.t1[victim]
            self.b1[victim] = None
            return victim

        victim = next(iter(resident_pages))
        return victim

    def sync_state(self, resident_pages: Set[int]) -> None:
        new_t1 = OrderedDict((p, None) for p in self.t1 if p in resident_pages)
        new_t2 = OrderedDict((p, None) for p in self.t2 if p in resident_pages)
        for p in resident_pages:
            if p not in new_t1 and p not in new_t2:
                new_t1[p] = None
        self.t1 = new_t1
        self.t2 = new_t2

    def get_metadata_size(self) -> int:
        return len(self.t1) + len(self.t2) + len(self.b1) + len(self.b2)

    def reset(self) -> None:
        self.p = 0.0
        self.t1.clear()
        self.t2.clear()
        self.b1.clear()
        self.b2.clear()

    def clone(self) -> "ARCPolicy":
        cp = ARCPolicy(self.c)
        cp.p = self.p
        cp.t1 = OrderedDict((k, None) for k in self.t1)
        cp.t2 = OrderedDict((k, None) for k in self.t2)
        cp.b1 = OrderedDict((k, None) for k in self.b1)
        cp.b2 = OrderedDict((k, None) for k in self.b2)
        return cp
