"""Production-style Streamlit observability dashboard for the cache API."""
from datetime import datetime

import pandas as pd
import streamlit as st

from api_client import CANONICAL_ALGORITHMS, DashboardAPI, normalize_algorithm


st.set_page_config(page_title="Adaptive Cache Control Room", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(
    """
    <style>
    @keyframes reveal { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
    .stApp {
        background-color: #f8fafc;
        background-image: linear-gradient(rgba(15, 23, 42, .035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(15, 23, 42, .035) 1px, transparent 1px);
        background-size: 48px 48px;
        color: #111827;
    }
    [data-testid="stHeader"] { background: rgba(248, 250, 252, .9); }
    [data-testid="stMainBlockContainer"] { padding-top: 1.6rem; animation: reveal .35s ease-out both; }
    h1, h2, h3, [data-testid="stCaptionContainer"] { color: #111827 !important; }
    h1 { letter-spacing: .015em; font-weight: 700; }
    h2 { letter-spacing: .08em; text-transform: uppercase; font-size: 1rem; }
    [data-testid="stMetric"], [data-testid="stDataFrame"], [data-testid="stVegaLiteChart"],
    [data-testid="stAlert"], [data-testid="stJson"], [data-testid="stExpander"] {
        background: #ffffff; border: 1px solid #d9dee7;
        border-radius: 8px; box-shadow: 0 4px 14px rgba(15, 23, 42, .045);
    }
    [data-testid="stMetric"] { padding: 14px; transition: border-color .18s ease, box-shadow .18s ease; }
    [data-testid="stMetric"]:hover { border-color: #9ca8b8; box-shadow: 0 8px 20px rgba(15, 23, 42, .08); }
    [data-testid="stMetricLabel"] p { color: #64748b !important; text-transform: uppercase; letter-spacing: .1em; font-size: .68rem; }
    [data-testid="stMetricValue"] { color: #111827 !important; font-variant-numeric: tabular-nums; }
    [data-testid="stDataFrame"], [data-testid="stVegaLiteChart"] { padding: 8px; }
    [data-testid="stSidebar"] { background: #f1f4f8; border-right: 1px solid #d9dee7; }
    [data-testid="stButton"] button { border-radius: 6px; border: 1px solid #aeb8c5; color: #111827; background: #ffffff; transition: border-color .18s ease, background .18s ease; text-transform: uppercase; letter-spacing: .08em; font-size: .7rem; font-weight: 700; }
    [data-testid="stButton"] button:hover { border-color: #111827; background: #f8fafc; box-shadow: 0 5px 12px rgba(15, 23, 42, .08); }
    [data-testid="stButton"] button[kind="primary"] { background: #111827; color: #ffffff; border-color: #111827; }
    [data-testid="stButton"] button[kind="primary"]:hover { background: #263244; }
    [data-testid="stSelectbox"] label, [data-testid="stSlider"] label, [data-testid="stToggle"] label { color: #475569 !important; text-transform: uppercase; letter-spacing: .1em; font-size: .68rem; font-weight: 700; }
    [data-testid="stProgressBar"] > div > div { background: #0f766e; }
    .section-note { color: #64748b; margin-top: -.6rem; margin-bottom: 1rem; }
    .brand-kicker { color: #64748b; font-size: .7rem; letter-spacing: .22em; text-transform: uppercase; font-weight: 700; }
    .status-dot { color: #0f766e; animation: pulse 2s ease-in-out infinite; }
    .status-panel { background: #ffffff; border: 1px solid #d9dee7; border-radius: 8px; padding: .8rem 1rem; color: #334155; font-size: .82rem; }
    @keyframes pulse { 0%, 100% { opacity: .45; } 50% { opacity: 1; } }
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
    decision = str(row.get("Decision", "")).upper()
    styles = []
    for col in row.index:
        if col == "Decision":
            if decision == "HIT":
                styles.append("color: #22c55e; font-weight: 700; background-color: rgba(34, 197, 94, 0.20);")
            elif decision == "MISS":
                styles.append("color: #ef4444; font-weight: 700; background-color: rgba(239, 68, 68, 0.20);")
            elif decision in ("EVICT", "EVICTED"):
                styles.append("color: #f59e0b; font-weight: 700; background-color: rgba(245, 158, 11, 0.20);")
            else:
                styles.append("")
        else:
            if decision == "HIT":
                styles.append("background-color: rgba(34, 197, 94, 0.06);")
            elif decision == "MISS":
                styles.append("background-color: rgba(239, 68, 68, 0.06);")
            elif decision in ("EVICT", "EVICTED"):
                styles.append("background-color: rgba(245, 158, 11, 0.06);")
            else:
                styles.append("")
    return styles


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
    st.markdown('<div class="brand-kicker">RESILIENCE</div>', unsafe_allow_html=True)
    st.header("System / Adaptive Cache")
    st.caption("CONTROL ROOM")
    algorithms = list(CANONICAL_ALGORITHMS)
    current_algorithm = normalize_algorithm(overview.get("algorithm", "ADAPTIVE"))
    algorithm = st.selectbox("Active algorithm", algorithms,
                             index=algorithms.index(current_algorithm))
    workload = st.selectbox("Synthetic workload", ["steady", "spike", "gradual"])
    request_count = st.slider("Request sample", 10, 500, 50, 10)
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
            try:
                overview = system.simulate_kaggle(request_count)
            except RuntimeError as exc:
                st.warning(f"Kaggle event replay notice: {exc}. Replaying realistic e-commerce traffic instead.")
                overview = system.simulate("realistic", request_count)
    if st.button("Run algorithm benchmark", use_container_width=True):
        with st.spinner("Comparing cache policies..."):
            st.session_state.comparison = system.benchmark(workload, request_count, 5)

st.markdown('<div class="brand-kicker">RESILIENCE · SYSTEM / ADAPTIVE CACHE</div>', unsafe_allow_html=True)
st.title("System Control Room")
st.caption("Live observability for cache efficiency, ML behavior, cost, and request decisions.")

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

cost_breakdown = system.cost_breakdown()
with st.expander("💰 Cost Breakdown", expanded=False):
    st.caption("Backend Cost (simulated units), not INR or cloud billing.")
    cost_columns = st.columns(4)
    cost_columns[0].metric("Total backend cost", f"{cost_breakdown['total_backend_cost']:.2f} units")
    cost_columns[1].metric("Cost avoided", f"{cost_breakdown['cost_saved']:.2f} units")
    cost_columns[2].metric("Cache hits", cost_breakdown["cache_hits"])
    cost_columns[3].metric("Cache misses", cost_breakdown["cache_misses"])

    cost_rows = []
    for event_type, details in cost_breakdown["by_event_type"].items():
        cost_rows.append({
            "Event": event_type.upper(),
            "Count": details["count"],
            "Unit cost": f"{details['unit_cost']:.1f} units",
            "Misses": details["misses"],
            "Subtotal applied": f"{details['subtotal']:.2f} units",
        })
    st.dataframe(pd.DataFrame(cost_rows), hide_index=True, use_container_width=True)
    st.markdown(
        "**Cost basis:** VIEW → 1 unit · CART → 5 units · PURCHASE → 10 units  \n"
        "**MISS:** `cost += event_cost[event_type]`  \n"
        "**HIT:** `cost += 0` because backend retrieval is avoided."
    )
    st.caption(
        f"Total requests: {cost_breakdown['total_requests']} · "
        f"Backend calls avoided: {cost_breakdown['backend_calls_avoided']} · "
        "Cost Saved = estimated backend cost of avoided retrievals."
    )

    request_events = pd.DataFrame(cost_breakdown["recent_requests"])
    if not request_events.empty:
        request_events["timestamp"] = request_events["timestamp"].map(format_time)
        request_events["cache_status"] = request_events["cache_hit"].map({True: "HIT", False: "MISS"})
        request_events = request_events.rename(columns={
            "timestamp": "Timestamp", "key": "Cache key", "event_type": "Event",
            "cache_status": "Cache status", "retrieval_cost": "Retrieval cost",
            "cumulative_cost": "Cumulative cost",
        })
        st.caption("Request Cost Details · recent 50 requests")
        st.dataframe(request_events[[
            "Timestamp", "Cache key", "Event", "Cache status",
            "Retrieval cost", "Cumulative cost",
        ]], hide_index=True, use_container_width=True)
        request_options = list(range(len(request_events)))
        selected_request_index = st.selectbox(
            "Explain a request", request_options,
            format_func=lambda index: f"{request_events.iloc[index]['Timestamp']} · {request_events.iloc[index]['Cache key']}",
        )
        selected_request = request_events.iloc[selected_request_index]
        event_name = str(selected_request["Event"]).upper()
        status = selected_request["Cache status"]
        applied_cost = float(selected_request["Retrieval cost"])
        nominal_cost = {"VIEW": 1.0, "CART": 5.0, "PURCHASE": 10.0}.get(event_name, applied_cost)
        reason = (
            f"Response served from cache, so backend retrieval was avoided. "
            f"The configured {event_name} retrieval cost of {nominal_cost:.1f} units was not applied."
            if status == "HIT" else
            f"{event_name} event uses the configured simulated retrieval cost basis of {nominal_cost:.1f} units."
        )
        st.info(
            f"Event: **{event_name}**  ·  Cache status: **{status}**  ·  "
            f"Backend retrieval cost: **{applied_cost:.2f} units**\n\nReason: {reason}"
        )

st.header("AI decision insights")
st.markdown('<p class="section-note">Inspect why the active model values a cached response.</p>', unsafe_allow_html=True)
raw_state = system.cache_state()
if not raw_state:
    st.info("Run a simulation to populate AI decision insights.")
else:
    item_by_key = {entry["key"]: entry for entry in raw_state}
    selected_key = st.selectbox("Selected cache item", list(item_by_key))
    selected = item_by_key[selected_key]
    decision_records = [
        event for event in system.decisions(200)
        if event.get("decision_target", "cache_item") == "evicted_item"
        or event.get("key") in item_by_key
    ]
    selected_decision_index = st.selectbox(
        "Decision record",
        list(range(len(decision_records))) or [None],
        format_func=lambda index: (
            "No decision records"
            if index is None else
            f"{decision_records[index].get('decision', 'UNKNOWN').upper()} · "
            f"{decision_records[index].get('key', '-') } · "
            f"{format_time(decision_records[index].get('timestamp'))}"
        ),
    )
    selected_decisions = [event for event in decision_records if event.get("key") == selected_key]
    latest_decision = (
        decision_records[selected_decision_index]
        if selected_decision_index is not None else
        (selected_decisions[0] if selected_decisions else {})
    )
    selected_decision = str(latest_decision.get("decision", selected.get("decision", "keep"))).upper()
    selected_mode = str(latest_decision.get("decision_mode", "EXPLOITATION")).upper()
    selected_retention = latest_decision.get("retention_score")
    insight_cols = st.columns([1, 1, 2])
    insight_score = latest_decision.get("score", selected.get("score"))
    insight_cols[0].metric("Prediction score", f"{float(insight_score or 0):.3f}")
    insight_cols[1].metric("Decision", selected_decision)
    with insight_cols[2].container(border=True):
        st.caption("Feature explanation")
        explanation = score_explanation(selected)
        st.dataframe(pd.DataFrame(explanation, columns=["Signal", "Reading", "Evidence"]),
                     hide_index=True, use_container_width=True)
    if selected_decision == "EVICT":
        if selected_mode == "EXPLORATION":
            reason = "Exploration selected this candidate from the lower-ranked retention candidates to gather additional workload feedback."
        else:
            reason = "Low predicted future reuse made this item a weak retention candidate; it had the lowest retention score among eligible candidates."
        heading = "WHY EVICT?"
    elif selected_decision in {"KEEP", "RETAIN"}:
        reason = "The item currently has stronger retention value relative to the other candidates."
        heading = "WHY RETAIN?"
    else:
        reason = "The latest recorded decision does not contain an eviction or retention rationale."
        heading = "WHY THIS DECISION?"
    factor_rows = [
        {"Factor": "ML prediction score", "Value": f"{float(insight_score):.4f}" if insight_score is not None else "-"},
        {"Factor": "Frequency", "Value": str(latest_decision.get("frequency", selected.get("frequency")) or "-")},
        {"Factor": "Recency", "Value": str(format_time(latest_decision.get("last_access", selected.get("last_access"))))},
        {"Factor": "Cost impact", "Value": f"{float(latest_decision.get('cost', selected.get('cost')) or 0):.2f}"},
        {"Factor": "Size", "Value": f"{int(latest_decision.get('size', selected.get('size')) or 0)} B"},
        {"Factor": "Retention score", "Value": f"{float(selected_retention):.4f}" if selected_retention is not None else "Unavailable"},
    ]
    st.markdown(f"**{heading}**  \n{reason}")
    st.caption(f"Decision mode: {selected_mode}")
    st.dataframe(pd.DataFrame(factor_rows), hide_index=True, use_container_width=True)
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
        st.dataframe(stream_frame.style.apply(event_style, axis=1), hide_index=True, use_container_width=True)
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
        "algorithm": "Algorithm", "hits": "Hits", "misses": "Misses",
        "hit_rate": "Hit Rate", "evictions": "Evictions", "refreshes": "Refreshes",
        "average_latency_ms": "Latency (ms)", "cost": "Cost",
    })
    best = comparison_frame.loc[comparison_frame["Hit Rate"].idxmax()]
    st.markdown(f"Best hit-rate performer: **{best['Algorithm']}** at **{best['Hit Rate']:.1%}**")
    chart, table = st.columns([1.2, 1])
    with chart:
        st.bar_chart(comparison_frame.set_index("Algorithm")["Hit Rate"], color="#0f766e")
    with table:
        cols_to_show = [c for c in ["Algorithm", "Hits", "Misses", "Hit Rate", "Evictions", "Refreshes", "Latency (ms)", "Cost"] if c in comparison_frame.columns]
        display_frame = comparison_frame[cols_to_show].copy()
        if "Hit Rate" in display_frame.columns:
            display_frame["Hit Rate"] = display_frame["Hit Rate"].apply(lambda v: f"{v:.1%}" if isinstance(v, (int, float)) else v)
        if "Latency (ms)" in display_frame.columns:
            display_frame["Latency (ms)"] = display_frame["Latency (ms)"].apply(lambda v: f"{v:.2f}" if isinstance(v, (int, float)) else v)
        if "Cost" in display_frame.columns:
            display_frame["Cost"] = display_frame["Cost"].apply(lambda v: f"{v:.2f}" if isinstance(v, (int, float)) else v)
        st.dataframe(display_frame, hide_index=True, use_container_width=True)

st.header("AI system status")
learning_cols = st.columns(4)
learning_cols[0].metric("Training samples", overview.get("training_samples", 0))
learning_cols[1].metric("Pending labels", overview.get("pending_labels", 0))
learning_cols[2].metric("Exploration count", overview.get("exploration_count", 0))
learning_cols[3].metric("Reuse quality", f"{float(overview.get('reuse_prediction_quality', 0)):.1%}")
warmup_label = "Training" if overview.get("warmup_phase", False) else "Ready"
exploration_ratio = float(overview.get("exploration_ratio", 0))
training_samples = int(overview.get("training_samples", 0))
runtime_status = "ONLINE LEARNING: ACTIVE" if training_samples > 0 else "ONLINE LEARNING: WAITING FOR LABELS"
policy_status = "WARMUP: ACTIVE" if overview.get("warmup_phase", False) else "ADAPTIVE POLICY: ACTIVE"
st.markdown(
    f"<div class='status-panel'><span class='status-dot'>●</span> {runtime_status} · {policy_status} | "
    f"Model progress proxy: {float(overview.get('model_confidence', 0)):.1%} | "
    f"Exploration ratio: {exploration_ratio:.1%} | "
    f"Exploration / exploitation: {overview.get('exploration_count', 0)} / {overview.get('exploitation_count', 0)}</div>",
    unsafe_allow_html=True,
)
history = pd.DataFrame(system.history())
if not history.empty:
    history["Score"] = pd.to_numeric(history.get("prediction_score"), errors="coerce").fillna(0)
    history["Time"] = history["timestamp"].map(format_time)
    st.caption("Prediction score trend")
    st.line_chart(history.set_index("Time")["Score"], color="#d97706")
    st.caption("Training sample count trend")
    st.line_chart(history.set_index("Time")["training_samples"], color="#0f766e")
    non_null_scores = pd.to_numeric(history["prediction_score"], errors="coerce").dropna()
    if not non_null_scores.empty:
        st.caption(
            f"Current prediction score: {non_null_scores.iloc[-1]:.3f} · "
            f"Observed range: {non_null_scores.min():.3f}–{non_null_scores.max():.3f}"
        )

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
