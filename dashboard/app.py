"""Production-style Streamlit observability dashboard for the cache API."""
from datetime import datetime

import pandas as pd
import streamlit as st

from api_client import DashboardAPI


st.set_page_config(page_title="Adaptive Cache Control Room", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(
    """
    <style>
    @keyframes reveal { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    .stApp {
        background: radial-gradient(900px circle at 8% -10%, rgba(14, 165, 163, .16), transparent 52%),
            radial-gradient(700px circle at 95% 0%, rgba(245, 158, 11, .12), transparent 45%),
            linear-gradient(135deg, #f7faf9 0%, #edf6f4 52%, #f8fafc 100%);
        color: #172033;
    }
    [data-testid="stHeader"] { background: rgba(247, 250, 249, .72); }
    [data-testid="stMainBlockContainer"] { padding-top: 2rem; animation: reveal .35s ease-out both; }
    h1, h2, h3, [data-testid="stCaptionContainer"] { color: #172033 !important; }
    [data-testid="stMetric"], [data-testid="stDataFrame"], [data-testid="stVegaLiteChart"],
    [data-testid="stAlert"], [data-testid="stJson"], [data-testid="stExpander"] {
        background: rgba(255, 255, 255, .72); backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(100, 116, 139, .2);
        border-radius: 12px; box-shadow: 0 10px 28px rgba(51, 65, 85, .09);
    }
    [data-testid="stMetric"] { padding: 14px; transition: transform .18s ease, box-shadow .18s ease; }
    [data-testid="stMetric"]:hover { transform: translateY(-2px); box-shadow: 0 14px 30px rgba(13, 148, 136, .14); }
    [data-testid="stMetricLabel"] p { color: #52627a !important; }
    [data-testid="stMetricValue"] { color: #0f766e !important; font-variant-numeric: tabular-nums; }
    [data-testid="stDataFrame"], [data-testid="stVegaLiteChart"] { padding: 8px; }
    [data-testid="stSidebar"] { background: rgba(231, 242, 240, .8); }
    [data-testid="stButton"] button { border-radius: 9px; border: 1px solid rgba(13, 148, 136, .3); transition: .18s ease; }
    [data-testid="stButton"] button:hover { transform: translateY(-1px); box-shadow: 0 8px 18px rgba(13, 148, 136, .16); }
    .section-note { color: #64748b; margin-top: -.6rem; margin-bottom: 1rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_time(value: object) -> str:
    try:
        return datetime.fromtimestamp(float(value)).strftime("%H:%M:%S")
    except (TypeError, ValueError, OSError):
        return "-"


def score_explanation(item: dict) -> list[tuple[str, str, str]]:
    frequency = float(item.get("frequency", 0))
    age = max(datetime.now().timestamp() - float(item.get("last_access", datetime.now().timestamp())), 0)
    cost = float(item.get("cost", 0))
    size = float(item.get("size", 0))
    return [
        ("Frequency", "High" if frequency >= 3 else "Low", f"{frequency:.0f} observed accesses"),
        ("Recency", "Recent" if age < 60 else "Aging", f"{age:.0f}s since last access"),
        ("Cost impact", "Worth keeping" if cost >= 5 else "Low impact", f"backend cost {cost:.2f}"),
        ("Size penalty", "Light" if size < 512 else "Heavy", f"{size:.0f} bytes estimate"),
    ]


def event_style(row: pd.Series) -> list[str]:
    colors = {"HIT": "background-color: #dcfce7", "MISS": "background-color: #fee2e2",
              "EVICT": "background-color: #fef3c7"}
    return [colors.get(str(row.get("Decision", "")), "") for _ in row]


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
    st.header("Control room")
    algorithms = ["LRU", "LFU", "GDS", "Adaptive"]
    current_algorithm = overview.get("algorithm", "ADAPTIVE").title()
    algorithm = st.selectbox("Active algorithm", algorithms,
                             index=algorithms.index(current_algorithm))
    workload = st.selectbox("Synthetic workload", ["steady", "spike", "gradual"])
    request_count = st.slider("Request sample", 10, 200, 50, 10)
    developer_mode = st.toggle("Developer mode", value=False)
    st.divider()
    if algorithm.lower() != overview.get("algorithm", "").lower():
        overview = system.select_algorithm(algorithm.lower())
        st.session_state.comparison = None
    if st.button("Simulate workload", use_container_width=True, type="primary"):
        with st.spinner(f"Replaying {workload} traffic..."):
            overview = system.simulate(workload, request_count)
    if st.button("Replay Kaggle events", use_container_width=True):
        with st.spinner("Replaying chronological e-commerce traffic..."):
            overview = system.simulate_kaggle(request_count)
    if st.button("Run algorithm benchmark", use_container_width=True):
        with st.spinner("Comparing cache policies..."):
            st.session_state.comparison = system.benchmark(workload, request_count, 5)

st.title("Adaptive Cache Control Room")
st.caption("Live observability for cache efficiency, ML behavior, and request decisions.")

# Executive metrics are derived from the existing metrics API.
hits = int(overview.get("hits", 0))
misses = int(overview.get("misses", 0))
total_cost = float(overview.get("cost", 0.0))
average_miss_cost = total_cost / misses if misses else 0.0
cost_saved = hits * average_miss_cost
average_score = float(overview.get("average_prediction_score", 0.0))

st.header("Executive metrics")
st.markdown('<p class="section-note">Current session performance and estimated backend savings.</p>', unsafe_allow_html=True)
metrics = st.columns(6)
metrics[0].metric("Hit rate", f"{float(overview.get('hit_rate', 0)):.1%}")
metrics[1].metric("Average latency", f"{float(overview.get('average_latency_ms', 0)):.2f} ms")
metrics[2].metric("Total backend cost", f"{total_cost:.2f}")
metrics[3].metric("Cost saved", f"{cost_saved:.2f}", help="Estimated from avoided calls times observed average miss cost.")
metrics[4].metric("Backend calls avoided", f"{hits:,}")
metrics[5].metric("Average ML score", f"{average_score:.2f}")

st.header("AI decision insights")
st.markdown('<p class="section-note">Inspect why the active model values a cached response.</p>', unsafe_allow_html=True)
raw_state = system.cache_state()
if not raw_state:
    st.info("Run a simulation to populate AI decision insights.")
else:
    item_by_key = {entry["key"]: entry for entry in raw_state}
    selected_key = st.selectbox("Selected cache item", list(item_by_key))
    selected = item_by_key[selected_key]
    insight_cols = st.columns([1, 1, 2])
    insight_cols[0].metric("Prediction score", f"{float(selected.get('score') or 0):.3f}")
    insight_cols[1].metric("Decision", str(selected.get("decision", "keep")).upper())
    with insight_cols[2].container(border=True):
        st.caption("Feature explanation")
        explanation = score_explanation(selected)
        st.dataframe(pd.DataFrame(explanation, columns=["Signal", "Reading", "Evidence"]),
                     hide_index=True, use_container_width=True)
    if developer_mode:
        st.json({"key": selected_key, "raw_features": {
            "frequency": selected.get("frequency"), "recency_seconds": max(
                datetime.now().timestamp() - float(selected.get("last_access", datetime.now().timestamp())), 0
            ), "cost": selected.get("cost"), "size": selected.get("size")
        }}, expanded=True)

st.header("Cache behavior")
logs_raw = system.decisions(200)
logs = pd.DataFrame(logs_raw)
if logs.empty:
    st.info("No request decisions yet.")
else:
    logs["Time"] = logs["timestamp"].map(format_time)
    logs["Decision"] = logs["decision"].str.upper()
    logs["Score"] = pd.to_numeric(logs["score"], errors="coerce").round(3)
    behavior_cols = ["Time", "key", "Decision", "Score", "algorithm"]
    timeline, stream = st.columns([1.4, 1])
    with timeline:
        st.caption("Hit / miss / eviction timeline")
        timeline_frame = logs.head(60)[behavior_cols].rename(columns={"key": "Key", "algorithm": "Algorithm"})
        st.dataframe(timeline_frame.style.apply(event_style, axis=1), hide_index=True, use_container_width=True)
    with stream:
        st.caption("Live request stream")
        stream_frame = logs.head(12)[["Time", "key", "Decision", "Score"]].rename(columns={"key": "Key"})
        st.dataframe(stream_frame, hide_index=True, use_container_width=True)
    evictions = logs[logs["Decision"] == "EVICT"]
    if not evictions.empty:
        st.caption("Eviction log: lowest prediction score or exploration candidate")
        st.dataframe(evictions[["Time", "key", "Score", "algorithm"]].rename(
            columns={"key": "Key", "algorithm": "Algorithm"}), hide_index=True, use_container_width=True)

st.header("Algorithm comparison")
comparison = st.session_state.comparison
if comparison is None:
    st.info("Run the algorithm benchmark to compare LRU, LFU, GDS, and Adaptive.")
else:
    comparison_frame = pd.DataFrame(comparison).rename(columns={
        "algorithm": "Algorithm", "hit_rate": "Hit Rate",
        "average_latency_ms": "Latency (ms)", "cost": "Cost",
    })
    best = comparison_frame.loc[comparison_frame["Hit Rate"].idxmax()]
    st.markdown(f"Best hit-rate performer: **{best['Algorithm']}** at **{best['Hit Rate']:.1%}**")
    chart, table = st.columns([1.2, 1])
    with chart:
        st.bar_chart(comparison_frame.set_index("Algorithm")["Hit Rate"], color="#0f766e")
    with table:
        st.dataframe(comparison_frame[["Algorithm", "Hit Rate", "Latency (ms)", "Cost"]],
                     hide_index=True, use_container_width=True)

st.header("ML observability")
learning_cols = st.columns(4)
learning_cols[0].metric("Training samples", overview.get("training_samples", 0))
learning_cols[1].metric("Pending labels", overview.get("pending_labels", 0))
learning_cols[2].metric("Exploration count", overview.get("exploration_count", 0))
learning_cols[3].metric("Reuse quality", f"{float(overview.get('reuse_prediction_quality', 0)):.1%}")
warmup_label = "Training" if overview.get("warmup_phase", False) else "Ready"
exploration_ratio = float(overview.get("exploration_ratio", 0))
st.info(f"Model status: {warmup_label} | Confidence: {float(overview.get('model_confidence', 0)):.1%} | "
    f"Exploration ratio: {exploration_ratio:.1%} | "
    f"Exploration / exploitation: {overview.get('exploration_count', 0)} / {overview.get('exploitation_count', 0)}")
history = pd.DataFrame(system.history())
if not history.empty:
    history["Score"] = pd.to_numeric(history.get("prediction_score"), errors="coerce").fillna(0)
    history["Time"] = history["timestamp"].map(format_time)
    st.caption("Prediction score trend")
    st.line_chart(history.set_index("Time")["Score"], color="#d97706")
    st.caption("Training sample count trend")
    st.line_chart(history.set_index("Time")["training_samples"], color="#0f766e")

st.header("Cache state")
if not raw_state:
    st.info("The active cache is empty.")
else:
    state_frame = pd.DataFrame(raw_state)
    state_frame["last_access"] = state_frame["last_access"].map(format_time)
    st.dataframe(state_frame[["key", "frequency", "last_access", "cost", "size", "score", "decision"]],
                 hide_index=True, use_container_width=True)
    with st.expander("Cached JSON response"):
        st.json(selected.get("value", {}), expanded=True)

if developer_mode:
    st.header("Developer mode")
    st.json({"overview": overview, "latest_decisions": logs_raw[:10]}, expanded=False)
