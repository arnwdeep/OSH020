"""
Test and Verification Suite for OSH020 Hackathon Challenges KO-05-C1 to KO-05-C5
"""
import sys
from simulator.challenges import (
    run_challenge_1,
    run_challenge_2,
    run_challenge_3,
    run_challenge_4,
    run_challenge_5,
    run_all_challenges,
)

def test_challenge_1():
    rep = run_challenge_1()
    assert rep.passed, f"Challenge 1 failed: {rep.summary}"
    assert rep.details["stats"]["FIFO"]["faults"] == 5
    assert rep.details["stats"]["LRU"]["faults"] == 4
    print("[PASS] Challenge 01 (KO-05-C1) Baseline Fault Accounting")

def test_challenge_2():
    rep = run_challenge_2()
    assert rep.passed, f"Challenge 2 failed: {rep.summary}"
    assert rep.details["step4_evicted"] == 2
    assert rep.details["step5_hit"] is True
    print("[PASS] Challenge 02 (KO-05-C2) Policy-State Switch & Shadow Reconciliation")

def test_challenge_3():
    rep = run_challenge_3()
    assert rep.passed, f"Challenge 3 failed: {rep.summary}"
    assert rep.details["peak_shadow_size"] <= rep.details["metadata_cap"] * 1.5
    print("[PASS] Challenge 03 (KO-05-C3) Shadow Budget & Overhead Enforcement")

def test_challenge_4():
    rep = run_challenge_4()
    assert rep.passed, f"Challenge 4 failed: {rep.summary}"
    assert rep.details["stable_during_noise"] is True
    assert rep.details["switched_after_sustained"] is True
    assert rep.details["switch_window"] == 6
    print("[PASS] Challenge 04 (KO-05-C4) Phase-Change Noisy Selector & Hysteresis")

def test_challenge_5():
    rep = run_challenge_5()
    assert rep.passed, f"Challenge 5 failed: {rep.summary}"
    assert rep.details["stats"]["FIFO"]["total_io_cost"] == 9
    assert rep.details["stats"]["LRU"]["total_io_cost"] == 4
    assert rep.details["io_cost_saved"] == 5
    print("[PASS] Challenge 05 (KO-05-C5) Dirty-Page Cost & I/O Cost Selector")

def main():
    print("=" * 70)
    print("   OSH020: RUNNING VERIFICATION SUITE FOR ALL 5 CHALLENGES")
    print("=" * 70)
    test_challenge_1()
    test_challenge_2()
    test_challenge_3()
    test_challenge_4()
    test_challenge_5()
    print("=" * 70)
    print("   ALL 5 LIVE TECHNICAL CHALLENGES PASSED PERFECTLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
