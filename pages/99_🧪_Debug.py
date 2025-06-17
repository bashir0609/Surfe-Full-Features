import streamlit as st
from utils.api_debug import run_debug_interface
from utils.helpers import init_session_state

# Initialize session state
init_session_state()

# Set page config
st.set_page_config(page_title="API Debug", layout="wide")

# Run the debug interface
run_debug_interface()