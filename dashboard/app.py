"""Streamlit monitoring dashboard backed by the project's real cache services."""
from datetime import datetime

import pandas as pd
import streamlit as st

from backend.benchmark.compare import run_comparison
from backend.dashboard_service import DashboardService


st.set_page_config(page_title="Adaptive Cache Dashboard", layout="wide")
st.title("Adaptive Cache Benchmark Dashboard")
st.caption("Interactive cache session using the production cache manager and backend simulator.")

if "system" not in st.session_state:
    st.session_state.system = DashboardService()
    st.session_state.comparison = None

system: DashboardService = st.session_state.system

with st.sidebar:
    st.header("Controls")
    algorithm = st.selectbox("Cache algorithm", ["LRU", "LFU", "GDS", "Adaptive"],
                             index=["LRU", "LFU", "GDS", "ADAPTIVE"].index(system.cache.algorithm.upper()))
    workload = st.selectbox("Workload", ["steady", "spike", "gradual"])
    request_count = st.slider("Simulation requests", min_value=10, max_value=200, value=50, step=10)

    if algorithm.lower() != system.cache.algorithm:
        system.select_algorithm(algorithm.lower())
        st.session_state.comparison = None

    if st.button("Simulate workload", use_container_width=True, type="primary"):
        with st.spinner(f"Running {workload} traffic..."):
            system.simulate_workload(workload, request_count)

    if st.button("Run benchmark", use_container_width=True):
        with st.spinner("Comparing all policies..."):
            st.session_state.comparison = run_comparison(workload, request_count, 25)


# Section 1: System overview
st.header("System Overview")
overview = system.overview()
overview_columns = st.columns(5)
overview_columns[0].metric("Current algorithm", overview["algorithm"])
overview_columns[1].metric("Total requests", overview["requests"])
overview_columns[2].metric("Cache hit rate", f"{overview['hit_rate']:.1%}")
overview_columns[3].metric("Average latency", f"{overview['average_latency_ms']:.2f} ms")
overview_columns[4].metric("Total cost", f"{overview['cost']:.2f}")


# Section 2: Live metrics. These are actual request observations, not fabricated values.
st.header("Live Metrics")
history = pd.DataFrame(system.metric_history())
if history.empty:
    st.info("Simulate a workload to populate the live hit-rate and latency charts.")
else:
    history["time"] = history["timestamp"].map(datetime.fromtimestamp)
    chart_data = history.set_index("time")
    hit_chart, latency_chart = st.columns(2)
    with hit_chart:
        st.caption("Hit rate over time")
        st.line_chart(chart_data["hit_rate"])
    with latency_chart:
        st.caption("Latency over time")
        st.line_chart(chart_data["latency_ms"])


# Section 3: Algorithm comparison comes from backend.benchmark.compare.run_comparison.
st.header("Algorithm Comparison")
comparison = st.session_state.comparison
if comparison is None:
    st.info("Choose a workload and select **Run benchmark** to compare all algorithms.")
else:
    comparison_frame = pd.DataFrame(comparison).rename(columns={
        "algorithm": "Algorithm", "hit_rate": "Hit Rate",
        "average_latency_ms": "Latency (ms)", "cost": "Cost",
    })
    st.dataframe(
        comparison_frame[["Algorithm", "Hit Rate", "Latency (ms)", "Cost"]],
        hide_index=True,
        column_config={
            "Hit Rate": st.column_config.NumberColumn(format="%.2f"),
            "Latency (ms)": st.column_config.NumberColumn(format="%.2f"),
            "Cost": st.column_config.NumberColumn(format="%.2f"),
        },
        use_container_width=True,
    )


# Section 4: Cache state is read directly from the active AdaptiveCacheManager.
st.header("Cache State")
state = pd.DataFrame(system.cache_state())
if state.empty:
    st.info("The selected cache is empty.")
else:
    state["last_access"] = state["last_access"].map(
        lambda value: datetime.fromtimestamp(value).strftime("%H:%M:%S")
    )
    st.dataframe(
        state[["key", "frequency", "last_access", "cost", "size"]],
        hide_index=True,
        use_container_width=True,
    )


# Section 5: Decision logs originate in backend.metrics.logger's bounded event buffer.
st.header("Decision Logs")
logs = pd.DataFrame(system.decision_logs())
if logs.empty:
    st.info("No decisions yet. Simulate traffic to generate HIT, MISS, KEEP, and EVICT events.")
else:
    logs["timestamp"] = logs["timestamp"].map(
        lambda value: datetime.fromtimestamp(value).strftime("%H:%M:%S")
    )
    st.dataframe(
        logs[["timestamp", "key", "decision", "algorithm", "score"]],
        hide_index=True,
        use_container_width=True,
    )
