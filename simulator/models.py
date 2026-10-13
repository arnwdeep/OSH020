from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any

class PatternType(str, Enum):
    SEQUENTIAL = "Sequential / Scan"
    LOOP = "Loop / Cyclic"
    RANDOM = "Random Access"
    LOCALITY = "Locality / Reuse-Heavy"
    MIXED = "Mixed / Dynamic"
    CUSTOM = "Custom Trace"

@dataclass
class PageAccessEvent:
    step: int
    page: int
    is_hit: bool
    evicted: Optional[int]
    active_policy: str
    frames: List[int]
    detected_pattern: Optional[str] = None
    switch_occurred: bool = False
    switch_reason: Optional[str] = None
    is_write: bool = False
    dirty_evicted: bool = False
    io_cost: int = 0
    cumulative_io_cost: int = 0
    resident_dirty_bits: Dict[int, bool] = field(default_factory=dict)

@dataclass
class PolicyScore:
    policy_name: str
    recent_hits: int
    recent_faults: int
    total_hits: int
    total_faults: int
    recent_hit_rate: float
    total_hit_rate: float

@dataclass
class SimulationResult:
    policy_name: str
    total_accesses: int
    hits: int
    faults: int
    hit_rate: float
    fault_rate: float
    history: List[PageAccessEvent] = field(default_factory=list)
    switch_history: List[Dict[str, Any]] = field(default_factory=list)
    policy_timeline: List[str] = field(default_factory=list)
    cumulative_hit_rates: List[float] = field(default_factory=list)
    total_io_cost: int = 0
    dirty_evictions: int = 0

@dataclass
class ChallengeReport:
    challenge_id: str
    title: str
    difficulty: str
    passed: bool
    summary: str
    details: Dict[str, Any] = field(default_factory=dict)
    trace: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class WorkloadConfig:
    pattern: PatternType
    total_requests: int
    unique_pages: int
    frame_count: int
    loop_size: Optional[int] = None
    locality_bias: float = 0.8
    seed: Optional[int] = 42
