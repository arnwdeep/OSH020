import argparse
import sys
from simulator import (
    WorkloadGenerator,
    AdaptiveEngine,
    run_benchmark_suite,
    run_single_policy
)

def print_banner():
    banner = r"""
================================================================================
   OSH020: WORKLOAD-ADAPTIVE PAGE REPLACEMENT ENGINE & SIMULATOR
================================================================================
"""
    print(banner)

def run_cli_demo(num_frames: int = 4, phase_length: int = 25, seed: int = 42):
    print_banner()
    print(f"[*] Configuration: Frames = {num_frames}, Phase Length = {phase_length}, Seed = {seed}\n")

    print("[*] Generating Multi-Phase Synthetic Workload:")
    stream, phases = WorkloadGenerator.generate_mixed(
        phase_length=phase_length,
        frame_count=num_frames,
        seed=seed
    )

    for i, (start, end, desc) in enumerate(phases, 1):
        print(f"    Phase {i} [Req {start:3d}..{end-1:3d}]: {desc}")
    print(f"    Total Memory References: {len(stream)}\n")

    print("[*] Running Benchmark Suite across all policies...")
    results = run_benchmark_suite(stream, num_frames=num_frames, window_size=25)

    print("\n" + "=" * 70)
    print(f"{'POLICY':<22} | {'HITS':<8} | {'FAULTS':<8} | {'HIT RATE (%)':<12}")
    print("-" * 70)

    # Sort results by hit rate descending (Optimal first or Adaptive compared)
    sorted_res = sorted(results.items(), key=lambda x: x[1].hit_rate, reverse=True)
    for name, res in sorted_res:
        prefix = "-> " if name == "Adaptive Engine" else "   "
        print(f"{prefix + name:<22} | {res.hits:<8} | {res.faults:<8} | {res.hit_rate:>6.2f}%")
    print("=" * 70)

    # Print Adaptive Switching details
    adaptive_res = results["Adaptive Engine"]
    print(f"\n[*] Adaptive Engine Policy Transitions (Total: {len(adaptive_res.switch_history)}):")
    if not adaptive_res.switch_history:
        print("    No switches occurred.")
    else:
        for sw in adaptive_res.switch_history:
            print(f"    Step {sw['step']:3d}: [{sw['from_policy']}] -> [{sw['to_policy']}] | Pattern: {sw['pattern']}")
            print(f"             Reason: {sw['reason']}")

    # Belady's Anomaly Demo
    print("\n" + "=" * 70)
    print("           BELADY'S ANOMALY DEMONSTRATION")
    print("=" * 70)
    belady_stream = WorkloadGenerator.get_belady_anomaly_trace()
    print(f"Reference Stream: {belady_stream}")
    fifo_3 = run_single_policy("FIFO", belady_stream, num_frames=3)
    fifo_4 = run_single_policy("FIFO", belady_stream, num_frames=4)
    lru_3 = run_single_policy("LRU", belady_stream, num_frames=3)
    lru_4 = run_single_policy("LRU", belady_stream, num_frames=4)

    print(f"\n[FIFO Policy]:")
    print(f"   3 Frames -> Faults: {fifo_3.faults} | Hit Rate: {fifo_3.hit_rate:.1f}%")
    print(f"   4 Frames -> Faults: {fifo_4.faults} | Hit Rate: {fifo_4.hit_rate:.1f}%")
    if fifo_4.faults > fifo_3.faults:
        print("   >>> ANOMALY DETECTED: More frames resulted in MORE page faults! (9 vs 10)")

    print(f"\n[LRU Policy (Stack Algorithm - Anomaly-Proof)]:")
    print(f"   3 Frames -> Faults: {lru_3.faults} | Hit Rate: {lru_3.hit_rate:.1f}%")
    print(f"   4 Frames -> Faults: {lru_4.faults} | Hit Rate: {lru_4.hit_rate:.1f}%")
    print("=" * 70 + "\n")

def run_challenges_cli(challenge_arg: str):
    from simulator.challenges import (
        run_challenge_1,
        run_challenge_2,
        run_challenge_3,
        run_challenge_4,
        run_challenge_5,
        run_all_challenges
    )

    print("\n" + "=" * 78)
    print("   KERNEL OPS / LIVE TECHNICAL CHALLENGES — CREW (KO-05) OSH020")
    print("=" * 78)

    runners = {
        "1": run_challenge_1,
        "2": run_challenge_2,
        "3": run_challenge_3,
        "4": run_challenge_4,
        "5": run_challenge_5,
    }

    selected = ["1", "2", "3", "4", "5"] if challenge_arg.lower() in ("all", "0") else [challenge_arg]

    for key in selected:
        if key not in runners:
            print(f"[!] Unknown challenge: {key}. Choose 1, 2, 3, 4, 5, or 'all'.")
            continue

        report = runners[key]()
        status_tag = "[PASS] SUCCESS" if report.passed else "[FAIL] FAILED"
        print(f"\n>>> {report.challenge_id}: {report.title} ({report.difficulty}) — {status_tag}")
        print("-" * 78)
        print(f"Summary: {report.summary}\n")

        if key == "1":
            stats = report.details["stats"]
            print(f"{'POLICY':<16} | {'HITS':<6} | {'FAULTS':<6} | {'HIT RATE (%)':<12}")
            print("-" * 50)
            for p_name, st in stats.items():
                print(f"{p_name:<16} | {st['hits']:<6} | {st['faults']:<6} | {st['hit_rate']:>6.2f}%")

        elif key == "2":
            print("Step Trace (Reconciling FIFO -> LRU state at Step 4):")
            for t in report.trace:
                status = "HIT " if t["is_hit"] else "FAULT"
                ev_str = f"Evicted {t['evicted']}" if t["evicted"] is not None else "No eviction"
                print(f"  Step {t['step']}: Page {t['page']} [{t['active_policy']}] -> {status} | Frames: {t['frames']} | {ev_str}")

        elif key == "3":
            dt = report.details
            print(f"Total References: {dt['total_references']} | Declared Metadata Cap: {dt['metadata_cap']} units")
            print(f"Peak Shadow Footprint: {dt['peak_shadow_size']} units | Cap Enforcements: {dt['enforcement_count']}")
            print(f"Per-Reference Work: Avg {dt['avg_work_ns']} ns | Peak {dt['max_work_ns']} ns")
            print("Policy Results:")
            for p, st in dt["policy_results"].items():
                print(f"  {p:<10}: Hits={st['hits']}, Faults={st['faults']}, Rate={st['hit_rate']}%")

        elif key == "4":
            print("Decision Windows Trace (Hysteresis & Noise Suppression):")
            for w in report.trace:
                sw_tag = f"*** SWITCHED to {w['to_policy']} ***" if w["switched"] else ""
                print(f"  Window {w['window']}: Scores FIFO={w['fifo_faults']}, LRU={w['lru_faults']} | Active={w['active_policy']} | Margin={w['margin']} {sw_tag}")
                print(f"            Reason: {w['reason']}")

        elif key == "5":
            dt = report.details
            print(f"Resource Costs: Page-In = {dt['page_in_cost']}, Dirty Writeback = {dt['writeback_cost']}")
            print(f"{'POLICY':<18} | {'FAULTS':<8} | {'DIRTY EVICTIONS':<16} | {'TOTAL I/O COST':<14}")
            print("-" * 62)
            for p, st in dt["stats"].items():
                print(f"{p:<18} | {st['faults']:<8} | {st['dirty_evictions']:<16} | {st['total_io_cost']:<14}")
            print(f"\nSelector Insight: {dt['selector_insight']}")

    print("\n" + "=" * 78 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OSH020 Workload-Adaptive Page Replacement Simulator")
    parser.add_argument("--frames", type=int, default=4, help="Number of physical RAM frames (default: 4)")
    parser.add_argument("--phase-len", type=int, default=25, help="Length of each workload phase (default: 25)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--challenge", type=str, default=None, help="Run live technical challenge: 1, 2, 3, 4, 5, or 'all'")
    args = parser.parse_args()

    if args.challenge:
        run_challenges_cli(args.challenge)
    else:
        run_cli_demo(num_frames=args.frames, phase_length=args.phase_len, seed=args.seed)
