import streamlit as st
from src.evals.runner import run_evaluations

st.set_page_config(page_title="Evaluation Dashboard", layout="wide")
st.title("Evaluation Metrics")

metrics = run_evaluations()

col1, col2, col3 = st.columns(3)
col1.metric("Approval-within-N (N=3)", f"{metrics['approval_within_n']}%")
col2.metric("Average Revision Cycles", f"{metrics['average_revision_cycles']:.1f}")
col3.metric("Style-Violation Catch Rate", f"{metrics['style_violation_catch_rate']}%")

st.divider()
st.subheader("Detailed Evaluation Runs")
st.write("Waiting for complete execution logs to populate this table.")