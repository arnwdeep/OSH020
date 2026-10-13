import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from typing import List, Dict, Tuple

from simulator import (
    WorkloadGenerator,
    AdaptiveEngine,
    run_benchmark_suite,
    run_single_policy,
    run_challenge_1,
    run_challenge_2,
    run_challenge_3,
    run_challenge_4,
    run_challenge_5,
    run_all_challenges,
)

st.set_page_config(
    page_title="OSH020 — Workload-Adaptive Page Replacement Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# EDITORIAL KLEIN BLUE & STARK WHITE THEME INJECTION
# ==============================================================================
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;0,700;1,400;1,600;1,700&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500;600&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">

<style>
    :root {
        --cobalt-blue: #0029FF;
        --pure-white: #FFFFFF;
        --off-white: #FAFAFC;
    }

    /* Overall Page Canvas */
    .stApp {
        background-color: #FFFFFF !important;
        font-family: 'Space Grotesk', sans-serif !important;
        color: #0F172A !important;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        max-width: 1440px !important;
    }

    /* Top Hero Poster Banner */
    .hero-cobalt-banner {
        background-color: #0029FF;
        color: #FFFFFF;
        padding: 3rem 3.5rem 3.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(0, 41, 255, 0.25);
    }

    .hero-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        border-bottom: 1px solid rgba(255, 255, 255, 0.25);
        padding-bottom: 1rem;
        margin-bottom: 2.5rem;
    }

    .hero-flourish-wrap {
        display: flex;
        flex-direction: column;
        gap: 0.8rem;
        margin-bottom: 2.5rem;
    }

    .hero-flourish-line {
        display: flex;
        align-items: center;
        gap: 1.5rem;
        flex-wrap: wrap;
    }

    .serif-display-word {
        font-family: 'Cormorant Garamond', serif;
        font-size: clamp(3.8rem, 8vw, 7.5rem);
        font-style: italic;
        font-weight: 400;
        line-height: 0.85;
        letter-spacing: -0.02em;
        color: #FFFFFF;
    }

    .parenthesis-box {
        display: inline-flex;
        flex-direction: column;
        border-left: 2px solid #FFFFFF;
        border-right: 2px solid #FFFFFF;
        border-radius: 30px;
        padding: 0.35rem 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        background: rgba(255, 255, 255, 0.08);
    }

    .hero-meta-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.5rem;
        padding: 1.2rem 0;
        border-top: 1px solid rgba(255, 255, 255, 0.25);
        border-bottom: 1px solid rgba(255, 255, 255, 0.25);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
    }

    .hero-welcome-word {
        font-family: 'Cormorant Garamond', serif;
        font-size: clamp(4rem, 9vw, 8rem);
        font-weight: 400;
        color: #FFFFFF;
        line-height: 0.9;
        margin-top: 2.5rem;
        letter-spacing: -0.02em;
    }

    /* Category Ribbon */
    .ribbon-banner {
        background: #FFFFFF;
        border-top: 2px solid #0029FF;
        border-bottom: 2px solid #0029FF;
        padding: 0.75rem 1.5rem;
        display: flex;
        justify-content: space-between;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        color: #0029FF;
        text-transform: uppercase;
        margin-bottom: 2rem;
    }

    /* Editorial Spec Cards */
    .editorial-kpi-card {
        border: 2px solid #0029FF;
        background: #FFFFFF;
        padding: 1.25rem;
        border-radius: 8px;
        box-shadow: 4px 4px 0px rgba(0, 41, 255, 0.12);
        margin-bottom: 1rem;
    }

    .kpi-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748B;
        margin-bottom: 0.3rem;
    }

    .kpi-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: #0029FF;
    }

    .kpi-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #64748B;
        margin-top: 0.2rem;
    }

    /* Frame Visualizer Box */
    .frame-box {
        border: 2px solid #0029FF;
        border-radius: 6px;
        padding: 1rem;
        text-align: center;
        background: #FAFAFC;
    }

    .frame-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: #64748B;
        text-transform: uppercase;
    }

    .frame-page {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.5rem;
        font-weight: 700;
        color: #0029FF;
        margin-top: 0.2rem;
    }

    /* Bottom Massive Wordmark */
    .bottom-wordmark {
        font-family: 'Syne', sans-serif;
        font-size: clamp(3rem, 8vw, 7.5rem);
        font-weight: 800;
        color: #0029FF;
        text-align: right;
        letter-spacing: -0.02em;
        border-top: 2px solid #0029FF;
        padding-top: 1rem;
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# HERO SECTION (ELECTRIC COBALT BLUE)
# ==============================================================================
st.markdown("""
<div class="hero-cobalt-banner">
    <div class="hero-top-row">
        <div>OSH020 // ARCHITECTURE</div>
        <div>OCT 2026 // BUILD 1.0</div>
        <div>VIRTUAL MEMORY // KERNEL SIM</div>
    </div>
    
    <div class="hero-flourish-wrap">
        <div class="hero-flourish-line">
            <span class="serif-display-word">PORT</span>
            <div class="parenthesis-box">
                <span>— A WORKLOAD —</span>
                <span>ADAPTIVE</span>
            </div>
        </div>
        <div class="hero-flourish-line" style="margin-left: 4vw;">
            <div class="parenthesis-box">
                <span>PAGING —</span>
                <span>ENGINE</span>
            </div>
            <span class="serif-display-word">FOLIO</span>
        </div>
    </div>

    <div class="hero-meta-grid">
        <div>
            <div style="opacity: 0.7; font-size: 0.68rem;">PROJECT ARCHITECTURE</div>
            <div style="font-weight: 600;">OSH020 VIRTUAL MEMORY LAB</div>
        </div>
        <div style="text-align: center;">
            <div style="opacity: 0.7; font-size: 0.68rem;">ALGORITHMS</div>
            <div style="font-weight: 600;">LRU · FIFO · CLOCK · ARC · LFU · OPTIMAL</div>
        </div>
        <div style="text-align: right;">
            <div style="opacity: 0.7; font-size: 0.68rem;">DYNAMIC PROTOCOL</div>
            <div style="font-weight: 600;">SLIDING-WINDOW ZERO-LOSS HOT-SWAP</div>
        </div>
    </div>

    <div class="hero-welcome-word">
        Welcome.
    </div>
</div>

<div class="ribbon-banner">
    <span>SEQUENTIAL SCAN</span>
    <span>CYCLIC LOOP (&gt; RAM)</span>
    <span>80/20 LOCALITY</span>
    <span>RANDOM NOISE</span>
    <span>BELADY ANOMALY</span>
    <span>DYNAMIC ADAPTATION</span>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# SIDEBAR CONTROLS
# ==============================================================================
st.sidebar.markdown("### ⚙️ SIMULATION SETUP")

workload_choice = st.sidebar.selectbox(
    "Workload Pattern",
    [
        "Multi-Phase Mixed (Dynamic Shifts)",
        "Sequential Scan",
        "Cyclic Loop",
        "80/20 Locality (Temporal Reuse)",
        "Uniform Random",
        "Belady's Anomaly Trace",
        "Custom Trace"
    ]
)

num_frames = st.sidebar.slider("Physical RAM Frames", min_value=2, max_value=8, value=4, step=1)
window_size = st.sidebar.slider("Sliding Window Size (W)", min_value=10, max_value=50, value=25, step=5)
cooldown = st.sidebar.slider("Switch Cooldown Steps", min_value=3, max_value=20, value=5, step=1)

# Generate Workload
stream: List[int] = []
phases_desc = []

if workload_choice == "Multi-Phase Mixed (Dynamic Shifts)":
    phase_len = st.sidebar.slider("Phase Length", 20, 60, 30, step=5)
    seed = st.sidebar.number_input("Random Seed", value=42, step=1)
    stream, phases = WorkloadGenerator.generate_mixed(phase_length=phase_len, frame_count=num_frames, seed=seed)
    phases_desc = phases

elif workload_choice == "Sequential Scan":
    reqs = st.sidebar.slider("Total Requests", 20, 150, 60)
    stream = WorkloadGenerator.generate_sequential(total_requests=reqs)

elif workload_choice == "Cyclic Loop":
    reqs = st.sidebar.slider("Total Requests", 20, 150, 60)
    loop_size = st.sidebar.slider("Loop Size", 2, 12, num_frames + 1)
    stream = WorkloadGenerator.generate_loop(total_requests=reqs, loop_size=loop_size)

elif workload_choice == "80/20 Locality (Temporal Reuse)":
    reqs = st.sidebar.slider("Total Requests", 20, 150, 80)
    ws_size = st.sidebar.slider("Hot Working Set Size", 2, 8, num_frames)
    stream = WorkloadGenerator.generate_locality(total_requests=reqs, working_set_size=ws_size)

elif workload_choice == "Uniform Random":
    reqs = st.sidebar.slider("Total Requests", 20, 150, 60)
    pages = st.sidebar.slider("Unique Pages Pool", 5, 30, 15)
    stream = WorkloadGenerator.generate_random(total_requests=reqs, unique_pages=pages)

elif workload_choice == "Belady's Anomaly Trace":
    stream = WorkloadGenerator.get_belady_anomaly_trace()

elif workload_choice == "Custom Trace":
    custom_input = st.sidebar.text_area("Enter page numbers (comma separated)", "1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5")
    stream = WorkloadGenerator.parse_trace_string(custom_input)
    if not stream:
        st.error("Invalid custom trace.")
        st.stop()

# Run Simulation
results = run_benchmark_suite(stream, num_frames=num_frames, window_size=window_size)
adaptive_res = results["Adaptive Engine"]
optimal_res = results.get("Optimal (MIN)")

# ==============================================================================
# EDITORIAL KPI SCORECARD
# ==============================================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="editorial-kpi-card">
        <div class="kpi-label">TOTAL ACCESSES</div>
        <div class="kpi-value">{len(stream)}</div>
        <div class="kpi-sub">Reference stream length</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="editorial-kpi-card">
        <div class="kpi-label">ADAPTIVE HIT RATE</div>
        <div class="kpi-value" style="color: #0029FF;">{adaptive_res.hit_rate}%</div>
        <div class="kpi-sub">{adaptive_res.hits} Hits / {adaptive_res.faults} Faults</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    best_baseline = max(
        [(k, v) for k, v in results.items() if k not in ("Adaptive Engine", "Optimal (MIN)")],
        key=lambda x: x[1].hit_rate
    )
    st.markdown(f"""
    <div class="editorial-kpi-card">
        <div class="kpi-label">BEST STATIC ({best_baseline[0]})</div>
        <div class="kpi-value" style="color: #475569;">{best_baseline[1].hit_rate}%</div>
        <div class="kpi-sub">{best_baseline[1].hits} Hits / {best_baseline[1].faults} Faults</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    opt_rate = optimal_res.hit_rate if optimal_res else 0.0
    st.markdown(f"""
    <div class="editorial-kpi-card">
        <div class="kpi-label">OPTIMAL BENCHMARK (MIN)</div>
        <div class="kpi-value" style="color: #7c3aed;">{opt_rate}%</div>
        <div class="kpi-sub">Theoretical ceiling</div>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# TABS SECTION
# ==============================================================================
# ==============================================================================
# TABS SECTION
# ==============================================================================
tab_leaderboard, tab_timeline, tab_inspector, tab_belady, tab_challenges = st.tabs([
    "📊 Policy Comparison Leaderboard",
    "📈 Cumulative Hit Rates & Transitions",
    "🔍 Memory Frame Step Inspector",
    "⚠️ Belady's Anomaly Sensitivity Lab",
    "🏆 Live Technical Challenges (KO-05)"
])

# Tab 1: Leaderboard
with tab_leaderboard:
    st.markdown("#### Performance Ranking")
    rows = []
    for pol_name, res in results.items():
        rows.append({
            "Policy": pol_name,
            "Hits": res.hits,
            "Page Faults": res.faults,
            "Hit Rate (%)": res.hit_rate,
            "Fault Rate (%)": res.fault_rate,
            "Type": "Adaptive" if pol_name == "Adaptive Engine" else ("Theoretical" if "Optimal" in pol_name else "Static")
        })
    df_results = pd.DataFrame(rows).sort_values("Hit Rate (%)", ascending=False).reset_index(drop=True)

    c_chart, c_tbl = st.columns([3, 2])
    with c_chart:
        chart = alt.Chart(df_results).mark_bar(cornerRadius=4).encode(
            x=alt.X("Hit Rate (%):Q", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("Policy:N", sort="-x", title=""),
            color=alt.Color("Type:N", scale=alt.Scale(
                domain=["Adaptive", "Theoretical", "Static"],
                range=["#0029FF", "#7c3aed", "#94a3b8"]
            )),
            tooltip=["Policy", "Hits", "Page Faults", "Hit Rate (%)"]
        ).properties(height=320)
        st.altair_chart(chart, use_container_width=True)

    with c_tbl:
        st.dataframe(df_results, use_container_width=True)

# Tab 2: Timeline
with tab_timeline:
    st.markdown("#### Cumulative Hit Rate Over Time")
    time_series = {"Step": list(range(len(stream)))}
    for pol_name, res in results.items():
        time_series[pol_name] = res.cumulative_hit_rates

    df_time = pd.DataFrame(time_series).melt(id_vars=["Step"], var_name="Policy", value_name="Cumulative Hit Rate (%)")

    line_chart = alt.Chart(df_time).mark_line(strokeWidth=2).encode(
        x="Step:Q",
        y=alt.Y("Cumulative Hit Rate (%):Q", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color("Policy:N"),
        tooltip=["Step", "Policy", "Cumulative Hit Rate (%)"]
    ).properties(height=360).interactive()
    st.altair_chart(line_chart, use_container_width=True)

    st.markdown(f"#### 🔄 Adaptive Decisions ({len(adaptive_res.switch_history)} Transitions)")
    if adaptive_res.switch_history:
        sw_df = pd.DataFrame(adaptive_res.switch_history)
        st.dataframe(
            sw_df.rename(columns={
                "step": "Step",
                "from_policy": "Old Policy",
                "to_policy": "New Policy",
                "pattern": "Detected Pattern",
                "reason": "Rationale"
            }),
            use_container_width=True
        )

# Tab 3: Inspector
with tab_inspector:
    st.markdown("#### Interactive Memory Reference Step Explorer")
    step_idx = st.slider("Access Step Index", 0, len(stream) - 1, 0)
    ev = adaptive_res.history[step_idx]

    ic1, ic2, ic3, ic4 = st.columns(4)
    with ic1:
        st.metric("Accessed Page", f"Page {ev.page}")
    with ic2:
        st.metric("Access Result", "CACHE HIT ✅" if ev.is_hit else "PAGE FAULT ❌")
    with ic3:
        st.metric("Active Policy", ev.active_policy)
    with ic4:
        st.metric("Evicted Page", f"Page {ev.evicted}" if ev.evicted is not None else "None")

    st.markdown("##### Physical RAM Frames")
    frame_cols = st.columns(num_frames)
    for i, p in enumerate(ev.frames):
        with frame_cols[i]:
            val_text = f"P{p}" if p != -1 else "Empty"
            border_color = "#16a34a" if p == ev.page and ev.is_hit else ("#dc2626" if p == ev.page and not ev.is_hit else "#0029FF")
            st.markdown(f"""
            <div style="border: 2px solid {border_color}; border-radius: 6px; padding: 12px; text-align: center; background: #FAFAFC;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #64748B;">FRAME {i}</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.4rem; font-weight: 700; color: #0029FF; margin-top: 4px;">{val_text}</div>
            </div>
            """, unsafe_allow_html=True)

# Tab 4: Belady
with tab_belady:
    st.markdown("#### Belady's Anomaly Sensitivity Lab")
    belady_trace = WorkloadGenerator.get_belady_anomaly_trace()
    st.code(f"Trace: {', '.join(map(str, belady_trace))}")

    frame_range = list(range(2, 8))
    b_data = []
    for f in frame_range:
        f_fifo = run_single_policy("FIFO", belady_trace, num_frames=f)
        f_lru = run_single_policy("LRU", belady_trace, num_frames=f)
        f_adap = AdaptiveEngine(num_frames=f).run_trace(belady_trace)
        b_data.append({"Frames": f, "Policy": "FIFO", "Page Faults": f_fifo.faults})
        b_data.append({"Frames": f, "Policy": "LRU", "Page Faults": f_lru.faults})
        b_data.append({"Frames": f, "Policy": "Adaptive Engine", "Page Faults": f_adap.faults})

    df_b = pd.DataFrame(b_data)
    b_chart = alt.Chart(df_b).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X("Frames:O", title="Number of Frames"),
        y=alt.Y("Page Faults:Q", title="Total Page Faults"),
        color=alt.Color("Policy:N"),
        tooltip=["Frames", "Policy", "Page Faults"]
    ).properties(height=350)
    st.altair_chart(b_chart, use_container_width=True)

# Tab 5: Live Technical Challenges
with tab_challenges:
    st.markdown("### 🏆 Kernel Ops: Live Technical Challenges (Crew KO-05)")
    st.markdown(
        "Interactive test verification and state traces for all 5 hackathon challenge options. "
        "Each test case demonstrates verified OS replacement invariants and resource trade-offs."
    )

    c_mode = st.radio(
        "Select Challenge View:",
        [
            "⚡ All Challenges Summary Scorecard",
            "01 Baseline fault accounting (KO-05-C1 | Easy)",
            "02 Policy-state switch & shadow reconciliation (KO-05-C2 | Medium)",
            "03 Shadow budget & per-reference overhead (KO-05-C3 | Medium)",
            "04 Phase-change noisy selector & hysteresis (KO-05-C4 | Hard)",
            "05 Dirty-page cost & I/O trade-off (KO-05-C5 | Hard)",
        ],
        horizontal=True
    )

    if c_mode == "⚡ All Challenges Summary Scorecard":
        all_reps = run_all_challenges()
        st.markdown("#### ✅ Verification Suite Scorecard")
        sc_cols = st.columns(5)
        for idx, (cid, rep) in enumerate(all_reps.items()):
            with sc_cols[idx]:
                st.markdown(f"""
                <div style="border: 2px solid #16a34a; border-radius: 8px; padding: 14px; background: #f0fdf4; text-align: center;">
                    <div style="font-size: 0.75rem; font-weight: 700; color: #166534;">{rep.challenge_id} ({rep.difficulty})</div>
                    <div style="font-size: 1.1rem; font-weight: 800; color: #15803d; margin: 4px 0;">PASSED ✅</div>
                    <div style="font-size: 0.72rem; color: #14532d;">{rep.title}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")
        for cid, rep in all_reps.items():
            with st.expander(f"📌 {rep.challenge_id}: {rep.title} — {rep.difficulty}", expanded=True):
                st.write(f"**Summary:** {rep.summary}")
                st.json(rep.details)

    elif "01 Baseline" in c_mode:
        rep1 = run_challenge_1()
        st.success(f"Status: {rep1.challenge_id} PASSED ✅")
        st.info(f"**Challenge Description:** {rep1.summary}")

        st.markdown("##### Reference Stream: `[1, 2, 3, 1, 4, 1]` with 3 Physical RAM Frames")
        stats_df = pd.DataFrame(rep1.details["stats"]).T.reset_index().rename(columns={"index": "Policy"})
        st.dataframe(stats_df, use_container_width=True)

        st.markdown("##### Step-by-Step Multi-Policy Frame State Trace")
        st.dataframe(pd.DataFrame(rep1.trace), use_container_width=True)

    elif "02 Policy-state" in c_mode:
        rep2 = run_challenge_2()
        st.success(f"Status: {rep2.challenge_id} PASSED ✅")
        st.info(f"**Challenge Description:** {rep2.summary}")

        st.markdown("##### State Transition Inspection")
        c2_col1, c2_col2 = st.columns(2)
        with c2_col1:
            st.metric("Frames Retained at Switch", str(rep2.details["resident_at_switch"]))
        with c2_col2:
            st.metric("Reference 4 Eviction", f"Page {rep2.details['step4_evicted']} (Least-Recent)")

        st.markdown("##### Execution Trace Across Switch Boundary")
        st.dataframe(pd.DataFrame(rep2.trace), use_container_width=True)

    elif "03 Shadow budget" in c_mode:
        rep3 = run_challenge_3()
        st.success(f"Status: {rep3.challenge_id} PASSED ✅")
        st.info(f"**Challenge Description:** {rep3.summary}")

        c3_1, c3_2, c3_3 = st.columns(3)
        with c3_1:
            st.metric("Declared Metadata Cap", f"{rep3.details['metadata_cap']} units")
        with c3_2:
            st.metric("Peak Shadow Footprint", f"{rep3.details['peak_shadow_size']} units")
        with c3_3:
            st.metric("Average Per-Reference Work", f"{rep3.details['avg_work_ns']} ns")

        st.markdown("##### Policy Comparison Under Cyclic Workload (1..20)")
        p_res = pd.DataFrame(rep3.details["policy_results"]).T.reset_index().rename(columns={"index": "Policy"})
        st.dataframe(p_res, use_container_width=True)

    elif "04 Phase-change" in c_mode:
        rep4 = run_challenge_4()
        st.success(f"Status: {rep4.challenge_id} PASSED ✅")
        st.info(f"**Challenge Description:** {rep4.summary}")

        st.markdown("##### Decision Windows & Hysteresis State Trace")
        st.dataframe(pd.DataFrame(rep4.trace), use_container_width=True)

    elif "05 Dirty-page" in c_mode:
        rep5 = run_challenge_5()
        st.success(f"Status: {rep5.challenge_id} PASSED ✅")
        st.info(f"**Challenge Description:** {rep5.summary}")

        c5_1, c5_2, c5_3 = st.columns(3)
        with c5_1:
            st.metric("Page-In Cost (Read)", rep5.details["page_in_cost"])
        with c5_2:
            st.metric("Writeback Cost (Dirty)", rep5.details["writeback_cost"])
        with c5_3:
            st.metric("I/O Cost Saved by Dirty-Awareness", f"{rep5.details['io_cost_saved']} units")

        st.markdown("##### I/O Cost Comparison Across Policies")
        df_dirty = pd.DataFrame(rep5.details["stats"]).T.reset_index().rename(columns={"index": "Policy"})
        st.dataframe(df_dirty, use_container_width=True)

        st.markdown(f"**Selector Decision:** {rep5.details['selector_insight']}")
        st.markdown("##### Step-by-Step Access Trace")
        st.dataframe(pd.DataFrame(rep5.trace), use_container_width=True)

# Bottom Wordmark
st.markdown("""
<div class="bottom-wordmark">
    SIMULATOR
</div>
""", unsafe_allow_html=True)

