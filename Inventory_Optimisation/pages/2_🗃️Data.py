import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")

st.dataframe(st.session_state.df, use_container_width= True)
