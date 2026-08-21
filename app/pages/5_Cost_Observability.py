import streamlit as st

st.set_page_config(page_title="Cost & Observability", layout="wide")
st.title("Observability Dashboard")

st.subheader("Workflow Averages")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Avg Token Use", "4,250")
col2.metric("Avg Latency (s)", "12.4")
col3.metric("Avg Model Calls", "3")
col4.metric("Avg Cost ($)", "0.012")

st.divider()
st.subheader("Recent Workflow Traces")
st.table([
    {"Workflow ID": "W-101", "Tokens": 3100, "Latency": "8.2s", "Calls": 2, "Cost": "$0.008"},
    {"Workflow ID": "W-102", "Tokens": 5500, "Latency": "15.1s", "Calls": 4, "Cost": "$0.015"},
    {"Workflow ID": "W-103", "Tokens": 4150, "Latency": "13.9s", "Calls": 3, "Cost": "$0.013"}
])