"""Basic Streamlit view for the API metrics endpoint."""
import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
st.set_page_config(page_title="Adaptive Cache Dashboard", layout="centered")
st.title("Adaptive Cache Management System")
st.caption(f"API: {API_URL}")

try:
    data = requests.get(f"{API_URL}/metrics", timeout=2).json()
    st.metric("Hit rate", f"{data['hit_rate']:.1%}")
    st.metric("Average latency", f"{data['average_latency_ms']:.2f} ms")
    st.metric("Backend cost", f"{data['cost']:.2f}")
    st.json(data)
except requests.RequestException:
    st.info("Start the FastAPI service, then refresh this page.")
