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

st.set_page_config(page_title="People Search", layout="wide")
st.title("🔎 People Search")
st.markdown("Find people based on their name, company, title, and more.")

if 'api_key' not in st.session_state or not st.session_state.api_key:
    st.error("🚨 Please enter your API key in the sidebar on the main page.")
    st.stop()

with st.form("people_search_form"):
    st.header("Search Criteria")
    col1, col2 = st.columns(2)
    
    name = col1.text_input("Full Name", placeholder="e.g., John Doe")
    current_company = col2.text_input("Current Company Domain", placeholder="e.g., surfe.com")
    title = col1.text_input("Current Title", placeholder="e.g., Software Engineer")
    country = col2.text_input("Country Code", placeholder="e.g., US, FR")

    submitted = st.form_submit_button("Search People", use_container_width=True, type="primary")

if submitted:
    search_criteria = {"query": {}}
    if name:
        search_criteria["query"]["name"] = name
    if current_company:
        search_criteria["query"]["current_company"] = current_company
    if title:
        search_criteria["query"]["title"] = title
    if country:
        search_criteria["query"]["country"] = country

    if not search_criteria["query"]:
        st.warning("Please provide at least one search criterion.")
    else:
        client = SurfeApiClient(st.session_state.api_key)
        with st.spinner("Searching for people..."):
            results = client.search_people(search_criteria)
        
        if results and results.get('people'):
            people = results['people']
            st.success(f"Found {len(people)} people matching your criteria.")
            df = pd.DataFrame(people)
            st.dataframe(df)
            create_download_buttons(df, "people_search_results")
        else:
            st.error("No people found or an error occurred.")
            if results:
                st.json(results)