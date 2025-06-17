import streamlit as st
import pandas as pd
from utils.api_client import SurfeApiClient, SurfeAPIError, AuthenticationError
from utils.helpers import (
    init_session_state, # <-- IMPORT THE FUNCTION
    extract_company_data,
    get_default_value,
    create_download_buttons,
)
# Initialize session state
init_session_state()

st.set_page_config(page_title="Company Search", layout="wide")
st.title("🔍 Company Search")
st.markdown("Find companies based on specific criteria like name, industry, or location.")

if 'api_key' not in st.session_state or not st.session_state.api_key:
    st.error("🚨 Please enter your API key in the sidebar on the main page.")
    st.stop()

with st.form("search_form"):
    st.header("Search Criteria")
    col1, col2 = st.columns(2)
    name = col1.text_input("Company Name (or part of it)")
    industries = col2.text_input("Industries (comma-separated)", placeholder="e.g., Software, Health")
    
    country = col1.text_input("Country Code", placeholder="e.g., US, FR, DE")
    # Define the valid size ranges the API accepts
    size_options = ["1-10", "11-50", "51-200", "201-1000", "1001-5000", "5001-10000", "10000+"]
    
    # Create a multiselect widget
    selected_sizes = col2.multiselect(
        "Employee Count Range", 
        options=size_options,
        help="Select one or more size ranges to search for."
    )
            
    limit = st.number_input("Max Results to Return", min_value=1, max_value=200, value=25)

    submitted = st.form_submit_button("Search Companies", use_container_width=True)

if submitted:
    # Build the 'filters' object with only the valid filters from the API documentation
    filters = {}
    if industries:
        # Capitalize the industry names to match the API's expected format
        filters["industries"] = [i.strip().title() for i in industries.split(',')]
    if country:
        filters["countries"] = [c.strip().upper() for c in country.split(',')]
        # Add the selected size ranges to the filters
    if selected_sizes:
        filters["size"] = selected_sizes
            
    # The final payload must be nested under a 'filters' key
    search_criteria = {
        "filters": filters,
        "limit": limit
    }

    if not filters:
        st.warning("Please enter at least one search criterion.")
    else:
        try:
            client = SurfeApiClient(st.session_state.api_key)
            with st.spinner("Searching for companies..."):
                results = client.search_companies(search_criteria)
            
            # The successful response contains a 'companies' or 'organizations' key
            companies = results.get('companies') or results.get('organizations')
            
            if companies:
                st.success(f"Found {len(companies)} companies.")
                df = pd.DataFrame(companies)
                st.dataframe(df)
                create_download_buttons(df, "company_search_results")
            else:
                st.info("No companies found matching your criteria.")
                if results:
                    st.write("API Response:")
                    st.json(results)

        except AuthenticationError as e:
            st.error(f"Authentication Failed: {e}. Please check your API key on the main page.")
        except SurfeAPIError as e:
            st.error(f"An API Error occurred: {e}")
            st.info("This might be a temporary issue with the Surfe API. Please try again or contact api.support@surfe.com if the problem persists.")
        except Exception as e:
            st.error(f"An unexpected error occurred in the application: {e}")