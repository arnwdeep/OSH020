from abc import ABC, abstractmethod
from typing import Set, List, Optional

class BasePolicy(ABC):
    """
    Abstract Base Class for page replacement policies.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def record_access(self, page: int, is_hit: bool) -> None:
        """Called on every memory access to update policy internal state."""
        pass

    @abstractmethod
    def choose_victim(self, resident_pages: Set[int]) -> int:
        """Selects a page from resident_pages to evict."""
        pass

    @abstractmethod
    def sync_state(self, resident_pages: Set[int]) -> None:
        """Synchronizes internal state with the currently resident pages."""
        pass

    def init_from_history(self, resident_pages: Set[int], history: List[int]) -> None:
        """
        Reconstructs policy metadata for resident pages based on observed reference history.
        Default implementation falls back to sync_state.
        """
        self.sync_state(resident_pages)

    def choose_victim_dirty(self, resident_pages: Set[int], dirty_pages: Set[int]) -> int:
        """
        Selects a victim with dirty-page awareness (preferring clean pages).
        Default implementation delegates to standard choose_victim.
        """
        return self.choose_victim(resident_pages)

    def get_metadata_size(self) -> int:
        """Returns approximate metadata element count for budget enforcement."""
        return 0

    @abstractmethod
    def reset(self) -> None:
        """Resets the policy state for a fresh run."""
        pass

    @abstractmethod
    def clone(self) -> "BasePolicy":
        """Creates a deep copy/fresh clone of the policy."""
        pass
