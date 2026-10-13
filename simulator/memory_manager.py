from typing import Set, List, Optional, Tuple

try:
    from .policies.base import BasePolicy
except (ImportError, ValueError):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from simulator.policies.base import BasePolicy



class AccessOutcome(tuple):
    """
    Subclass of tuple (is_hit, evicted) for backward compatibility,
    with explicit properties for dirty evictions and I/O costs.
    """
    def __new__(cls, is_hit: bool, evicted: Optional[int], was_dirty: bool = False, io_cost: int = 0):
        return super().__new__(cls, (is_hit, evicted))

    def __init__(self, is_hit: bool, evicted: Optional[int], was_dirty: bool = False, io_cost: int = 0):
        self.is_hit = is_hit
        self.evicted = evicted
        self.was_dirty = was_dirty
        self.io_cost = io_cost

class MemoryManager:
    """
    Simulates the Physical RAM and Paging System.
    Tracks resident frames, handles page faults, dirty bits, I/O cost accounting,
    and coordinates with eviction policies.
    """
    def __init__(
        self,
        num_frames: int,
        policy: BasePolicy,
        page_in_cost: int = 1,
        writeback_cost: int = 5
    ):
        self.num_frames = num_frames
        self.policy = policy
        self.page_in_cost = page_in_cost
        self.writeback_cost = writeback_cost
        self.resident_pages: Set[int] = set()
        self.frame_slots: List[Optional[int]] = [None] * num_frames
        self.dirty_bits: Dict[int, bool] = {}
        self.access_history: List[int] = []
        self.total_accesses: int = 0
        self.hits: int = 0
        self.faults: int = 0
        self.total_io_cost: int = 0
        self.dirty_evictions: int = 0
        self.last_io_cost: int = 0

    def access(self, page: int, is_write: bool = False) -> AccessOutcome:
        """
        Executes a memory reference.
        Args:
            page: Virtual page number being referenced.
            is_write: If True, marks page as modified/dirty.
        Returns:
            AccessOutcome tuple (is_hit, evicted) with .was_dirty and .io_cost attributes.
        """
        self.total_accesses += 1
        self.access_history.append(page)
        evicted = None
        was_dirty = False
        io_cost = 0

        if page in self.resident_pages:
            self.hits += 1
            is_hit = True
            if is_write:
                self.dirty_bits[page] = True
            self.policy.record_access(page, is_hit=True)
            self.last_io_cost = 0
            return AccessOutcome(True, None, was_dirty=False, io_cost=0)

        # Page Fault
        self.faults += 1
        is_hit = False
        io_cost += self.page_in_cost

        if len(self.resident_pages) < self.num_frames:
            # Free frame available
            for idx in range(self.num_frames):
                if self.frame_slots[idx] is None:
                    self.frame_slots[idx] = page
                    break
            self.resident_pages.add(page)
            self.dirty_bits[page] = is_write
        else:
            # RAM full: policy picks victim
            dirty_pages = {p for p, d in self.dirty_bits.items() if d and p in self.resident_pages}
            if hasattr(self.policy, "choose_victim_dirty"):
                victim = self.policy.choose_victim_dirty(self.resident_pages, dirty_pages)
            else:
                victim = self.policy.choose_victim(self.resident_pages)

            if victim not in self.resident_pages:
                victim = next(iter(self.resident_pages))

            was_dirty = bool(self.dirty_bits.get(victim, False))
            if was_dirty:
                self.dirty_evictions += 1
                io_cost += self.writeback_cost

            self.dirty_bits.pop(victim, None)
            self.resident_pages.remove(victim)

            slot_idx = self.frame_slots.index(victim) if victim in self.frame_slots else 0
            self.frame_slots[slot_idx] = page
            self.resident_pages.add(page)
            self.dirty_bits[page] = is_write
            evicted = victim

        self.total_io_cost += io_cost
        self.last_io_cost = io_cost
        self.policy.record_access(page, is_hit=False)
        return AccessOutcome(False, evicted, was_dirty=was_dirty, io_cost=io_cost)

    def set_policy(self, new_policy: BasePolicy, initialize_from_history: bool = True) -> None:
        """
        Dynamically hot-swaps the eviction policy and synchronizes state.
        If initialize_from_history is True, policy metadata is reconstructed from observed history.
        """
        self.policy = new_policy
        if initialize_from_history and hasattr(self.policy, "init_from_history"):
            self.policy.init_from_history(self.resident_pages, self.access_history)
        else:
            self.policy.sync_state(self.resident_pages)

    def get_resident_frames(self) -> List[Optional[int]]:
        return list(self.frame_slots)

    def get_dirty_map(self) -> Dict[int, bool]:
        return {p: self.dirty_bits.get(p, False) for p in self.resident_pages}

    def reset(self) -> None:
        self.resident_pages.clear()
        self.frame_slots = [None] * self.num_frames
        self.dirty_bits.clear()
        self.access_history.clear()
        self.total_accesses = 0
        self.hits = 0
        self.faults = 0
        self.total_io_cost = 0
        self.dirty_evictions = 0
        self.last_io_cost = 0
        self.policy.reset()

if __name__ == "__main__":
    from simulator.policies.lru import LRUPolicy
    print("--- MemoryManager Standalone Test ---")
    mm = MemoryManager(num_frames=3, policy=LRUPolicy())
    test_stream = [1, 2, 3, 2, 1, 4, 1, 5]
    for page in test_stream:
        is_hit, evicted = mm.access(page)
        status = "HIT " if is_hit else "MISS"
        evict_str = f"(Evicted {evicted})" if evicted is not None else ""
        print(f"Access Page {page} -> {status} | Frames: {mm.get_resident_frames()} {evict_str}")
    print(f"\nFinal Stats: Hits={mm.hits}, Faults={mm.faults}, Hit Rate={mm.hits/mm.total_accesses*100:.1f}%")

