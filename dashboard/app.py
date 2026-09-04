"""Streamlit monitoring dashboard backed by the project's real cache services."""
from datetime import datetime

import pandas as pd
import streamlit as st

from api_client import DashboardAPI


st.set_page_config(page_title="Adaptive Cache Dashboard", layout="wide")
st.markdown(
    """
    <style>
    @keyframes fade-up {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes metric-pop {
        0% { opacity: 0; transform: translateY(8px) scale(.98); }
        65% { opacity: 1; transform: translateY(0) scale(1.015); }
        100% { opacity: 1; transform: translateY(0) scale(1); }
    }
    .stApp {
        background:
            radial-gradient(900px circle at 15% -5%, rgba(37, 99, 235, .13), transparent 55%),
            radial-gradient(700px circle at 90% 20%, rgba(20, 184, 166, .10), transparent 48%),
            linear-gradient(135deg, #f8fbff 0%, #eef6ff 52%, #f7fafc 100%);
        color: #172033;
    }
    [data-testid="stHeader"] { background: rgba(248, 251, 255, .72); }
    [data-testid="stMainBlockContainer"] {
        padding-top: 2.5rem;
        animation: fade-up .45s ease-out both;
    }
    h1, h2, h3, [data-testid="stCaptionContainer"] { color: #172033 !important; }
    [data-testid="stMetric"], [data-testid="stDataFrame"], [data-testid="stVegaLiteChart"],
    [data-testid="stAlert"], [data-testid="stSidebar"] > div:first-child {
        background: rgba(255, 255, 255, .78);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(148, 163, 184, .28);
        border-radius: 12px;
        box-shadow: 0 10px 28px rgba(71, 85, 105, .12);
    }
    [data-testid="stMetric"] {
        padding: 15px;
        animation: metric-pop .55s ease-out both;
        transition: transform .2s ease, border-color .2s ease, box-shadow .2s ease;
    }
    [data-testid="stMetric"]:hover, [data-testid="stDataFrame"]:hover,
    [data-testid="stVegaLiteChart"]:hover {
        transform: scale(1.03);
        border-color: rgba(20, 184, 166, .48);
        box-shadow: 0 12px 32px rgba(20, 184, 166, .16);
    }
    [data-testid="stMetricLabel"] p { color: #52627a !important; }
    [data-testid="stMetricValue"] { color: #0f766e !important; font-variant-numeric: tabular-nums; }
    [data-testid="stDataFrame"], [data-testid="stVegaLiteChart"] { padding: 10px; transition: .2s ease; }
    [data-testid="stSidebar"] { background: rgba(235, 243, 252, .82); }
    [data-testid="stButton"] button {
        border-radius: 10px; border: 1px solid rgba(13, 148, 136, .35);
        transition: transform .2s ease, box-shadow .2s ease;
    }
    [data-testid="stButton"] button:hover {
        transform: translateY(-1px) scale(1.02);
        box-shadow: 0 8px 20px rgba(20, 184, 166, .20);
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("Adaptive Cache Benchmark Dashboard")
st.caption("Interactive cache session using the production cache manager and backend simulator.")

if "system" not in st.session_state:
    st.session_state.system = DashboardAPI()
    st.session_state.comparison = None

system: DashboardAPI = st.session_state.system
try:
    overview = system.overview()
except RuntimeError as exc:
    st.error(str(exc))
    st.info("Start the backend with: python -m uvicorn backend.main:app --reload")
    st.stop()

with st.sidebar:
    st.header("Controls")
    algorithm = st.selectbox("Cache algorithm", ["LRU", "LFU", "GDS", "Adaptive"],
                             index=["LRU", "LFU", "GDS", "ADAPTIVE"].index(overview["algorithm"]))
    workload = st.selectbox("Workload", ["steady", "spike", "gradual"])
    request_count = st.slider("Simulation requests", min_value=10, max_value=200, value=50, step=10)

    if algorithm.lower() != overview["algorithm"].lower():
        overview = system.select_algorithm(algorithm.lower())
        st.session_state.comparison = None

    if st.button("Simulate workload", use_container_width=True, type="primary"):
        with st.spinner(f"Running {workload} traffic..."):
            overview = system.simulate(workload, request_count)

    if st.button("Run benchmark", use_container_width=True):
        with st.spinner("Comparing all policies..."):
            st.session_state.comparison = system.benchmark(workload, request_count, 5)


# Section 1: System overview
st.header("System Overview")
overview_columns = st.columns(5)
overview_columns[0].metric("Current algorithm", overview["algorithm"])
overview_columns[1].metric("Total requests", overview["requests"])
overview_columns[2].metric("Cache hit rate", f"{overview['hit_rate']:.1%}")
overview_columns[3].metric("Average latency", f"{overview['average_latency_ms']:.2f} ms")
overview_columns[4].metric("Total cost", f"{overview['cost']:.2f}")


# Section 2: Live metrics. These are actual request observations, not fabricated values.
st.header("Live Metrics")
history = pd.DataFrame(system.history())
if history.empty:
    st.info("Simulate a workload to populate the live hit-rate and latency charts.")
else:
    history["time"] = history["timestamp"].map(datetime.fromtimestamp)
    chart_data = history.set_index("time")
    hit_chart, latency_chart = st.columns(2)
    with hit_chart:
        st.caption("Hit rate over time")
        st.line_chart(chart_data["hit_rate"], color="#22d3ee")
    with latency_chart:
        st.caption("Latency over time")
        st.line_chart(chart_data["latency_ms"], color="#a78bfa")


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
logs = pd.DataFrame(system.decisions())
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
