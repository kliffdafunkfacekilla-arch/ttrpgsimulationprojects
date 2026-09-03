import streamlit as st
import pandas as pd

st.title("Ostraka Management Console")

# Tab: Add Wildlife
with st.tab("Manage Wildlife"):
    name = st.text_input("Species Name")
    danger = st.slider("Danger Level", 1, 5)
    if st.button("Add Species"):
        # Add SQL INSERT logic here
        st.write(f"Added {name} to the database!")

# Tab: Global Rules
with st.tab("Simulation Settings"):
    growth = st.slider("Global Growth Rate", 0.0, 0.1, 0.02)
    st.write("Settings updated.")
