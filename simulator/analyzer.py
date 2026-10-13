from collections import Counter
import math
from typing import List, Dict, Any, Optional

class WorkloadAnalyzer:
    """
    Sliding-window Workload Analyzer.
    Analyzes the last W memory requests to characterize access patterns:
    - Straight scan / Sequential
    - Cyclic Loop (and whether loop size > RAM frames)
    - Reuse-heavy / Locality
    - Random
    """

    def __init__(self, window_size: int = 30, frame_count: int = 4):
        self.window_size = window_size
        self.frame_count = frame_count

    def analyze_window(self, window: List[int]) -> Dict[str, Any]:
        """
        Analyzes a sequence of page requests in the current window.
        Returns extracted features and the classified pattern name.
        """
        w_len = len(window)
        if w_len < 3:
            return {
                "pattern": "Insufficient Data",
                "confidence": 0.0,
                "uniqueness_ratio": 0.0,
                "loop_detected": False,
                "loop_period": 0,
                "locality_score": 0.0,
                "entropy": 0.0,
            }

        unique_pages = set(window)
        unique_count = len(unique_pages)
        uniqueness_ratio = unique_count / w_len

        # Monotonicity check for straight scan
        monotonic_diffs = [window[i+1] - window[i] for i in range(w_len - 1)]
        is_monotonic_scan = (
            uniqueness_ratio >= 0.85 and
            all(d > 0 for d in monotonic_diffs)
        )
        near_scan = uniqueness_ratio >= 0.90

        # Loop / Cyclic detection
        # Check periodicity: if window[i] == window[i - k] for candidate period k
        best_loop_period = 0
        max_loop_match = 0.0

        for period in range(2, min(self.frame_count * 2 + 2, w_len // 2 + 1)):
            matches = sum(1 for i in range(period, w_len) if window[i] == window[i - period])
            total_checks = w_len - period
            match_rate = matches / total_checks if total_checks > 0 else 0.0
            if match_rate > 0.75 and match_rate > max_loop_match:
                max_loop_match = match_rate
                best_loop_period = period

        # Locality / Reuse score: fraction of references belonging to top frame_count pages
        counts = Counter(window)
        top_frames_accesses = sum(c for _, c in counts.most_common(self.frame_count))
        locality_score = top_frames_accesses / w_len

        # Normalized Shannon Entropy
        probs = [c / w_len for c in counts.values()]
        entropy = -sum(p * math.log2(p) for p in probs)
        max_entropy = math.log2(unique_count) if unique_count > 1 else 1.0
        normalized_entropy = (entropy / max_entropy) if max_entropy > 0 else 0.0

        # Pattern classification logic
        if is_monotonic_scan or near_scan:
            pattern = "Straight scan"
            confidence = uniqueness_ratio
            recommended_policy = "FIFO"
            reason = "Pages are scanned once and not reused; FIFO avoids recency overhead."
        elif best_loop_period > 0:
            if best_loop_period > self.frame_count:
                pattern = f"Loop bigger than RAM (Period={best_loop_period})"
                confidence = max_loop_match
                recommended_policy = "FIFO"
                reason = "Cyclic loop > RAM causes catastrophic LRU 0% hit rate. FIFO or Clock preserves pages better."
            else:
                pattern = f"Loop within RAM (Period={best_loop_period})"
                confidence = max_loop_match
                recommended_policy = "LRU"
                reason = "Cyclic working set fits in frames; LRU preserves the active working cycle."
        elif locality_score >= 0.65:
            pattern = "Reuses recent pages (Locality)"
            confidence = locality_score
            recommended_policy = "LRU"
            reason = "Frequent access to high-locality hot working set; LRU protects hot pages."
        elif normalized_entropy >= 0.85:
            pattern = "Random access"
            confidence = normalized_entropy
            recommended_policy = "Clock"
            reason = "Uncorrelated random references; Clock has minimal overhead with equivalent hit rate."
        else:
            pattern = "Mixed / General"
            confidence = 0.5
            recommended_policy = "LRU"
            reason = "Standard mixed reference behavior; LRU provides robust default recency tracking."

        return {
            "pattern": pattern,
            "confidence": round(confidence, 3),
            "uniqueness_ratio": round(uniqueness_ratio, 3),
            "loop_detected": best_loop_period > 0,
            "loop_period": best_loop_period,
            "locality_score": round(locality_score, 3),
            "normalized_entropy": round(normalized_entropy, 3),
            "recommended_policy": recommended_policy,
            "reason": reason,
        }

if __name__ == "__main__":
    print("--- WorkloadAnalyzer Standalone Test ---")
    analyzer = WorkloadAnalyzer(window_size=20, frame_count=4)
    
    test_cases = {
        "Sequential Scan": [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
        "Loop > RAM (Size 5 > 4)": [0, 1, 2, 3, 4, 0, 1, 2, 3, 4, 0, 1, 2, 3, 4],
        "Locality / Reuse": [1, 1, 2, 1, 3, 1, 2, 1, 4, 1, 1, 2, 3, 1],
        "Random Noise": [4, 19, 2, 11, 8, 22, 1, 15, 9, 3, 17, 6],
    }
    
    for name, stream in test_cases.items():
        res = analyzer.analyze_window(stream)
        print(f"\nWorkload: {name}")
        print(f"  Classified Pattern:    {res['pattern']}")
        print(f"  Confidence:            {res['confidence']}")
        print(f"  Recommended Policy:    {res['recommended_policy']}")
        print(f"  Reason:                {res['reason']}")

