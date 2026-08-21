import streamlit as st
import requests

st.set_page_config(page_title="Content Approval Pipeline", layout="wide")
st.title("Brief Submission")

st.markdown("Enter the brief details to start the agent workflow.")

topic = st.text_input("Topic")
constraints = st.text_area("Constraints")

if st.button("Submit Brief", type="primary"):
    if topic and constraints:
        st.info("Sending brief to Backend API...")
    else:
        st.error("Please enter both Topic and Constraints.")