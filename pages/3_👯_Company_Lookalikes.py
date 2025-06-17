import streamlit as st
import pandas as pd
from utils.api_client import SurfeApiClient
from utils.helpers import (
    init_session_state, # <-- IMPORT THE FUNCTION
    extract_company_data,
    get_default_value,
    create_download_buttons,
)

# Call this at the start of each page
init_session_state()

st.set_page_config(page_title="Company Lookalikes", layout="wide")
st.title("👯 Company Lookalikes")
st.markdown("Find companies that are similar to a specific company domain.")

if 'api_key' not in st.session_state or not st.session_state.api_key:
    st.error("🚨 Please enter your API key in the sidebar on the main page.")
    st.stop()

with st.form("lookalike_form"):
    domain = st.text_input("Company Domain", placeholder="e.g., stripe.com")
    country = st.text_input("Filter by Country Code (Optional)", placeholder="e.g., US, DE")
    submitted = st.form_submit_button("Find Lookalikes", use_container_width=True)

if submitted:
    if not domain:
        st.warning("Please enter a company domain.")
    else:
        client = SurfeApiClient(st.session_state.api_key)
        with st.spinner(f"Finding companies similar to {domain}..."):
            results = client.get_company_lookalikes(domain, country if country else None)

        if results and results.get('organizations'):
            companies = results['organizations']
            st.success(f"Found {len(companies)} lookalike companies.")
            df = pd.DataFrame(companies)
            st.dataframe(df)
            create_download_buttons(df, f"lookalikes_for_{domain}")
        else:
            st.error("Could not find lookalikes or an error occurred.")
            if results:
                st.json(results)