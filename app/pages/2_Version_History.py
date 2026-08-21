import streamlit as st
import difflib

st.set_page_config(page_title="Version History & Diff", layout="wide")
st.title("Version History")

version_1 = "Introducing our new premium smartphone. It has great battery life."
version_2 = "Introducing our new premium smartphone. It offers excellent battery life and a modern design."

st.subheader("Version 1")
st.text(version_1)

st.subheader("Version 2 (Current)")
st.text(version_2)

st.divider()
st.subheader("Version Diff View")

diff = difflib.ndiff(version_1.split(), version_2.split())
diff_text = " ".join(diff)
st.markdown(f"```text\n{diff_text}\n```")