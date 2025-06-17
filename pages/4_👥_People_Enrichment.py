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

st.set_page_config(page_title="People Enrichment", layout="wide")
st.title("👥 People Enrichment")
st.markdown("Upload a CSV with LinkedIn profile URLs to find contact information.")
st.warning("Note: This feature is a placeholder and may require adjustments based on the exact Surfe People Enrichment API behavior.", icon="⚠️")

if 'api_key' not in st.session_state or not st.session_state.api_key:
    st.error("🚨 Please enter your API key in the sidebar on the main page.")
    st.stop()

uploaded_file = st.file_uploader("Upload a CSV with LinkedIn URLs", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head())
        
        linkedin_col = st.selectbox("Select column with LinkedIn Profile URLs", options=df.columns)
        
        if st.button("Start People Enrichment", use_container_width=True, type="primary"):
            client = SurfeApiClient(st.session_state.api_key)
            
            people_payload = []
            for i, row in df.iterrows():
                if pd.notna(row[linkedin_col]):
                    people_payload.append({
                        "linkedin_url": row[linkedin_col],
                        "externalID": f"row_{i}"
                    })
            
            st.info(f"Preparing to enrich {len(people_payload)} profiles.")
            # This is a simplified workflow. The actual API might be bulk/polling like companies.
            # Assuming a direct enrichment for this example.
            st.error("This functionality is not fully implemented as the People Enrichment API flow can vary. This serves as a structural example.")
            #
            # # --- Full Implementation would look like this ---
            # with st.spinner("Starting people enrichment job..."):
            #     job = client.start_people_enrichment(people_payload)
            # if job and job.get('id'):
            #     with st.spinner("Processing people..."):
            #         results = client.get_enrichment_results(job.get('id')) # Assuming same polling mechanism
            #     st.success("Enrichment complete!")
            #     st.json(results)
            # else:
            #     st.error("Failed to start people enrichment job.")

    except Exception as e:
        st.error(f"An error occurred: {e}")