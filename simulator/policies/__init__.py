from .base import BasePolicy
from .fifo import FIFOPolicy
from .lru import LRUPolicy
from .clock import ClockPolicy
from .optimal import OptimalPolicy
from .lfu import LFUPolicy
from .arc import ARCPolicy
from .dirty_aware import DirtyAwarePolicy

__all__ = [
    "BasePolicy",
    "FIFOPolicy",
    "LRUPolicy",
    "ClockPolicy",
    "OptimalPolicy",
    "LFUPolicy",
    "ARCPolicy",
    "DirtyAwarePolicy",
]
