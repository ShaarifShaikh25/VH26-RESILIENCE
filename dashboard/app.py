"""Interactive visual comparison of cache eviction policies."""
import pandas as pd
import streamlit as st

from backend.benchmark.compare import run_comparison


st.set_page_config(page_title="Adaptive Cache Benchmark Dashboard", layout="wide")
st.title("Adaptive Cache Benchmark Dashboard")

workload_type = st.selectbox(
    "Workload type",
    options=["steady", "spike", "gradual"],
)

with st.spinner(f"Running {workload_type} benchmark..."):
    results = run_comparison(workload_type)

dataframe = pd.DataFrame(results).rename(columns={
    "algorithm": "Algorithm",
    "hit_rate": "Hit Rate",
    "avg_latency": "Latency",
    "cost": "Cost",
})

st.subheader("Benchmark results")
st.dataframe(
    dataframe,
    hide_index=True,
    column_config={
        "Hit Rate": st.column_config.NumberColumn(format="%.2f"),
        "Latency": st.column_config.NumberColumn(format="%.4f s"),
        "Cost": st.column_config.NumberColumn(format="%.0f"),
    },
    use_container_width=True,
)

hit_rate_chart, latency_chart, cost_chart = st.columns(3)
with hit_rate_chart:
    st.subheader("Hit Rate")
    st.bar_chart(dataframe, x="Algorithm", y="Hit Rate")
with latency_chart:
    st.subheader("Latency")
    st.bar_chart(dataframe, x="Algorithm", y="Latency")
with cost_chart:
    st.subheader("Cost")
    st.bar_chart(dataframe, x="Algorithm", y="Cost")
