import streamlit as st
import pandas as pd
from utils.api_client import SurfeApiClient, init_session_state, SurfeAPIError, AuthenticationError
from utils.helpers import (
    extract_company_data,
    get_default_value,
    safe_convert_numeric,
    safe_convert_string,
    create_download_buttons,
    format_linkedin_url
)

st.set_page_config(page_title="Company Enrichment", layout="wide")

# Initialize session state
init_session_state()

# --- Available Data Points ---
AVAILABLE_DATA_POINTS = {
    "Company Name": {"key": "name", "data_type": "string"},
    "Website": {"key": "website", "data_type": "string"},
    "Description": {"key": "description", "data_type": "string"},
    "LinkedIn URL": {"key": "linkedin", "data_type": "string"},
    "Founded Year": {"key": "founded", "data_type": "numeric"},
    "Employee Count": {"key": "employees", "data_type": "numeric"},
    "Company Size": {"key": "size", "data_type": "string"},
    "Keywords": {"key": "keywords", "data_type": "string"},
    "HQ Country": {"key": "hqCountry", "data_type": "string"},
    "HQ Address": {"key": "hqAddress", "data_type": "string"},
    "Industry": {"key": "industry", "data_type": "string"},
    "Sub-Industry": {"key": "subIndustry", "data_type": "string"},
    "Phone Numbers": {"key": "phones", "data_type": "string"},
    "Digital Presence": {"key": "digitalPresence", "data_type": "string"},
    "Status": {"key": "status", "data_type": "string"},
}

# --- Sidebar for Data Point Selection ---
with st.sidebar:
    st.header("📊 Select Data Points")
    selected_data_points = {}
    default_selections = ["Company Name", "Website", "LinkedIn URL", "Employee Count", "Company Size", "Industry"]
    for name in AVAILABLE_DATA_POINTS:
        selected_data_points[name] = st.checkbox(name, value=name in default_selections)
    
    selected_count = sum(selected_data_points.values())
    st.info(f"**{selected_count}** data points selected.")
    
    # Debug section
    with st.expander("🐛 Debug Info"):
        st.write("Session State:")
        debug_info = {
            "API Key Set": bool(st.session_state.get('api_key')),
            "API Key Length": len(st.session_state.get('api_key', '')),
            "Processing Status": st.session_state.get('processing_status', 'unknown'),
            "Selected Count": selected_count
        }
        st.json(debug_info)
        
        if st.button("Test API Key"):
            if st.session_state.get('api_key'):
                try:
                    client = SurfeApiClient(st.session_state.api_key)
                    if client.validate_api_key():
                        st.success("✅ API key is valid!")
                    else:
                        st.error("❌ API key validation failed")
                except Exception as e:
                    st.error(f"❌ Error testing API key: {str(e)}")
            else:
                st.warning("No API key found")

# --- Main App UI ---
st.title("🏢 Company Enrichment")
st.markdown("Upload a CSV file with company domains to enrich them with valuable data.")

# Check API key first
if 'api_key' not in st.session_state or not st.session_state.api_key:
    st.error("🚨 Please enter your API key in the sidebar on the main page.")
    st.info("👈 Go to the main page using the sidebar and enter your Surfe.com API key")
    st.stop()

# Show API key status (masked)
api_key = st.session_state.api_key
if len(api_key) > 10:
    masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
else:
    masked_key = "*" * len(api_key)
st.success(f"✅ API Key loaded: {masked_key}")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    try:
        # Load and validate file
        df = pd.read_csv(uploaded_file)
        st.header("📄 File Preview")
        st.dataframe(df.head())
        
        st.info(f"File loaded successfully: {len(df)} rows, {len(df.columns)} columns")
        
        # Show column info
        with st.expander("📋 Column Information"):
            col_info = []
            for col in df.columns:
                non_null = df[col].notna().sum()
                col_info.append({
                    "Column": col,
                    "Non-null Count": non_null,
                    "Data Type": str(df[col].dtype),
                    "Sample Values": ", ".join(df[col].dropna().astype(str).head(3).tolist())
                })
            st.dataframe(pd.DataFrame(col_info))

        domain_column = st.selectbox("Select the column with company domains", options=df.columns)
        
        # Validate selected column
        if domain_column:
            valid_domains = df[domain_column].dropna()
            st.info(f"Found {len(valid_domains)} non-empty values in '{domain_column}' column")
            
            # Show sample domains
            with st.expander("🔍 Sample Domains to Process"):
                sample_domains = valid_domains.head(10).tolist()
                for i, domain in enumerate(sample_domains):
                    clean_domain = str(domain).strip().replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
                    st.write(f"{i+1}. `{domain}` → `{clean_domain}`")
                
                if len(valid_domains) > 10:
                    st.write(f"... and {len(valid_domains) - 10} more domains")
        
        # --- Raw Data Inspector for a Specific Domain ---
        with st.expander("🔬 Inspect Raw API Data for a Specific Domain"):
            st.write(
                "Enter any single domain to see the exact JSON data returned by the API. "
                "This is useful for debugging or finding the correct field names."
            )
            
            # Text input for the user to enter a domain
            inspect_domain = st.text_input("Domain to Inspect", placeholder="e.g., surfe.com")

            if st.button("Fetch Raw Data"):
                # Validate that the user has entered a domain and an API key
                if not inspect_domain.strip():
                    st.warning("Please enter a domain to inspect.")
                elif 'api_key' not in st.session_state or not st.session_state.api_key:
                    st.error("🚨 Please enter your API key in the sidebar first.")
                else:
                    st.info(f"Fetching raw API data for: **{inspect_domain}**")
                    with st.spinner("Calling API..."):
                        try:
                            client = SurfeApiClient(st.session_state.api_key)
                            # Create a payload for the single domain from the text input
                            payload = [{"domain": inspect_domain.strip(), "externalID": "raw_inspect"}]
                            enrich_job = client.start_company_enrichment(payload)
                            job_id = enrich_job.get('enrichmentID') or enrich_job.get('id')
                            
                            if job_id:
                                results = client.get_enrichment_results(job_id)
                                if results and results.get('companies'):
                                    st.success("✅ Raw data received!")
                                    st.json(results['companies'][0])
                                else:
                                    st.error("Could not retrieve enrichment results for this domain.")
                                    st.json(results)
                            else:
                                st.error("Failed to start enrichment job for this domain.")
                                st.json(enrich_job)

                        except Exception as e:
                            st.error(f"An error occurred: {e}")
        
        if st.button("🚀 Start Enrichment", type="primary", use_container_width=True, disabled=(selected_count==0)):
            if selected_count == 0:
                st.warning("Please select at least one data point from the sidebar.")
                st.stop()

            # Validate inputs before starting
            if not domain_column:
                st.error("Please select a domain column.")
                st.stop()
                
            valid_domains = df[domain_column].dropna().unique()
            if len(valid_domains) == 0:
                st.error("No valid domains found in the selected column.")
                st.stop()
            
            # Show what we're about to process
            st.info(f"🚀 Starting enrichment for {len(valid_domains)} unique domains")
            
            try:
                # Create API client
                client = SurfeApiClient(st.session_state.api_key)
                
                # Prepare payload
                companies_payload = []
                for i, domain in enumerate(valid_domains):
                    clean_domain = str(domain).strip().replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
                    if clean_domain and '.' in clean_domain:  # Basic domain validation
                        companies_payload.append({
                            "domain": clean_domain, 
                            "externalID": f"row_{i}"
                        })
                
                st.info(f"📦 Prepared {len(companies_payload)} valid domains for enrichment")
                
                # Show payload preview
                with st.expander("📋 Payload Preview (First 5 items)"):
                    st.json(companies_payload[:5])
                
                if len(companies_payload) == 0:
                    st.error("No valid domains found after cleaning. Please check your domain format.")
                    st.stop()

                with st.spinner(f"Sending {len(companies_payload)} domains for enrichment..."):
                    enrich_job = client.start_company_enrichment(companies_payload)

                # Debug the API response
                st.write("🔍 API Response Debug:")
                if enrich_job:
                    st.json(enrich_job)
                else:
                    st.error("❌ No response from API")
                    st.stop()

                # if enrich_job and enrich_job.get('id'):
                #     job_id = enrich_job.get('id')
                #     st.success(f"Enrichment job started successfully! (ID: {job_id})")

                job_id = enrich_job.get('enrichmentID') or enrich_job.get('id')
                if enrich_job and job_id:
                    st.success(f"Enrichment job started successfully! (ID: {job_id})")
                    
                    # Store job ID in session state
                    st.session_state.last_job_id = job_id
                    st.session_state.processing_status = 'polling'
                    
                    with st.spinner("Processing... This can take a few minutes."):
                        results = client.get_enrichment_results(job_id)

                    if results:
                        st.success("Enrichment complete! Mapping results back to your file.")
                        
                        # Show results preview
                        with st.expander("📊 Raw Results Preview"):
                            st.json(results)
                        
                        selected_keys = [AVAILABLE_DATA_POINTS[name]["key"] for name, sel in selected_data_points.items() if sel]
                        company_data_map = extract_company_data(results, selected_keys)

                        # Prepare new columns
                        for name, selected in selected_data_points.items():
                            if selected:
                                config = AVAILABLE_DATA_POINTS[name]
                                df[f"enriched_{config['key']}"] = get_default_value(config['data_type'])
                        
                        # Map data back to original dataframe
                        domain_to_index_map = {domain: i for i, domain in enumerate(valid_domains)}

                        for index, row in df.iterrows():
                            domain = row[domain_column]
                            if pd.notna(domain):
                                clean_domain = str(domain).strip().replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
                                if clean_domain in domain_to_index_map:
                                    result_idx = domain_to_index_map[clean_domain]
                                    if result_idx in company_data_map:
                                        for key, value in company_data_map[result_idx].items():
                                            # Apply special formatting only for the 'linkedin' key
                                            if key == 'linkedin':
                                                df.at[index, f"enriched_{key}"] = format_linkedin_url(value)
                                            else:
                                                df.at[index, f"enriched_{key}"] = value

                        st.header("✨ Enriched Data")
                        st.dataframe(df)
                        
                        # Show enrichment statistics
                        enriched_cols = [col for col in df.columns if col.startswith('enriched_')]
                        if enriched_cols:
                            st.subheader("📊 Enrichment Statistics")
                            stats = {}
                            for col in enriched_cols:
                                non_empty = df[col].notna().sum()
                                total = len(df)
                                stats[col.replace('enriched_', '')] = f"{non_empty}/{total} ({non_empty/total*100:.1f}%)"
                            st.json(stats)
                        
                        create_download_buttons(df, f"enriched_{uploaded_file.name}")
                    else:
                        st.error("Failed to retrieve enrichment results.")
                        st.info(f"Job ID: {job_id} - You can check this job status later.")
                else:
                    st.error("Failed to start the enrichment job.")
                    st.write("Possible issues:")
                    st.write("1. Invalid API key")
                    st.write("2. Invalid domain format")
                    st.write("3. API service temporarily unavailable")
                    st.write("4. Network connectivity issues")
                    
                    # Show detailed error info if available
                    if enrich_job:
                        st.write("Response received but no job ID found:")
                        st.json(enrich_job)
                    
            except Exception as e:
                st.error(f"Error during enrichment process: {str(e)}")
                st.write("Full error details:")
                st.exception(e)

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
        st.write("Full error details:")
        st.exception(e)

# Add helpful information
st.markdown("---")
st.header("💡 Troubleshooting Tips")
st.markdown("""
1. **API Key Issues**: Make sure your API key is valid and has sufficient credits
2. **Domain Format**: Domains should be in format like `example.com` (without http/https)
3. **File Format**: CSV should have a column with company domains
4. **Rate Limits**: If you get rate limited, wait a few minutes and try again
5. **Large Files**: For files with >1000 domains, processing may take several minutes
""")

with st.expander("🔧 Advanced Debugging"):
    st.write("Use these tools to reset the application's state if you encounter issues.")

    if st.button("Clear Job State & Reset Page"):
        """
        Clears all temporary data from the session but preserves the API key.
        This is useful for starting a fresh job without re-entering credentials.
        """
        keys_to_preserve = ['api_key', 'api_key_input']
        for key in list(st.session_state.keys()):
            if key not in keys_to_preserve:
                del st.session_state[key]
        
        # Re-initialize the state after clearing
        init_session_state() 
        st.success("Session state cleared! Your API key has been preserved.")
        st.rerun()

    if st.button("Show Full Session State"):
        """Displays the raw session state dictionary for debugging."""
        st.json({k: v for k, v in st.session_state.items()})
