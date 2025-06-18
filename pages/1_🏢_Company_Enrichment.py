import streamlit as st
import pandas as pd
import time
from utils.api_client import SurfeApiClient, init_session_state, SurfeAPIError, AuthenticationError
from utils.helpers import (
    extract_company_data,
    get_default_value,
    safe_convert_numeric,
    safe_convert_string,
    create_download_buttons,
    format_linkedin_url,
    create_feature_card,
    create_alert_box,
    enhanced_page_header
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
    default_selections = ["Website", "LinkedIn URL", "Founded Year", "Employee Count", "Company Size", "HQ Country", "HQ Address", "Industry"]
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

        # --- Single vs Bulk Enrichment Options ---
        if domain_column:
            valid_domains_unique = df[domain_column].dropna().unique()
            
            st.markdown("---")
            st.header("⚙️ Enrichment Mode Selection")
            
            col_mode1, col_mode2 = st.columns(2)
            
            with col_mode1:
                create_feature_card(
                    "Single Domain Enrichment",
                    "Process one domain at a time with detailed progress tracking and individual results",
                    "🎯"
                )
            
            with col_mode2:
                create_feature_card(
                    "Bulk Enrichment",
                    "Process all domains in one batch job for faster completion and better rate limiting",
                    "⚡"
                )
            
            # Mode selection
            enrichment_mode = st.radio(
                "Choose Enrichment Mode:",
                options=["🎯 Single Domain Mode", "⚡ Bulk Mode"],
                index=1,  # Default to bulk mode
                horizontal=True,
                help="Single mode: Process domains one by one. Bulk mode: Process all domains together."
            )
            
            # Show mode-specific information
            if enrichment_mode == "🎯 Single Domain Mode":
                create_alert_box(
                    f"📊 Single Mode: Will process {len(valid_domains_unique)} domains individually with detailed progress tracking.",
                    "info"
                )
                
                with st.expander("📋 Single Mode Features"):
                    st.markdown("""
                    **Advantages:**
                    - ✅ Detailed progress for each domain
                    - ✅ Continue processing if some domains fail
                    - ✅ See results as they complete
                    - ✅ Better error handling per domain
                    
                    **Considerations:**
                    - 🕐 Slower overall processing time
                    - 🔄 More API calls (affects rate limits)
                    - 📊 More detailed logging
                    """)
                
                # Single mode specific settings
                col_single1, col_single2 = st.columns(2)
                with col_single1:
                    delay_between = st.slider(
                        "Delay between domains (seconds)",
                        min_value=1.0,
                        max_value=10.0,
                        value=2.0,
                        step=0.5,
                        help="Time to wait between processing each domain"
                    )
                
                with col_single2:
                    max_retries = st.selectbox(
                        "Max retries per domain",
                        options=[1, 2, 3, 5],
                        index=1,
                        help="How many times to retry failed domains"
                    )
            
            else:  # Bulk Mode
                create_alert_box(
                    f"⚡ Bulk Mode: Will process all {len(valid_domains_unique)} domains in a single batch job.",
                    "success"
                )
                
                with st.expander("📋 Bulk Mode Features"):
                    st.markdown("""
                    **Advantages:**
                    - ⚡ Faster overall processing
                    - 🎯 Efficient API usage
                    - 🔄 Single job tracking
                    - 💰 Better rate limit utilization
                    
                    **Considerations:**
                    - 📊 Less granular progress
                    - ⚠️ All-or-nothing processing
                    - 🕐 Wait for entire batch to complete
                    """)
                
                # Bulk mode specific settings
                col_bulk1, col_bulk2 = st.columns(2)
                with col_bulk1:
                    if len(valid_domains_unique) > 500:
                        st.warning(f"⚠️ Large dataset detected: {len(valid_domains_unique)} domains")
                        st.info("Consider splitting into smaller batches if you encounter timeouts")
                
                with col_bulk2:
                    batch_timeout = st.selectbox(
                        "Batch timeout (minutes)",
                        options=[5, 10, 15, 20, 30],
                        index=2,  # Default to 15 minutes
                        help="Maximum time to wait for batch completion"
                    )
        
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
        
        # --- Main Enrichment Button ---
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
            
            # Show processing mode confirmation
            mode_text = "Single Domain Mode" if enrichment_mode == "🎯 Single Domain Mode" else "Bulk Mode"
            st.info(f"🚀 Starting {mode_text} enrichment for {len(valid_domains)} unique domains")
            
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
                
                if len(companies_payload) == 0:
                    st.error("No valid domains found after cleaning. Please check your domain format.")
                    st.stop()

                # Process based on selected mode
                if enrichment_mode == "🎯 Single Domain Mode":
                    # SINGLE DOMAIN MODE PROCESSING
                    st.subheader("🎯 Single Domain Processing")
                    
                    # Initialize results storage
                    all_results = {"companies": []}
                    successful_domains = 0
                    failed_domains = 0
                    
                    # Create progress containers
                    progress_bar = st.progress(0)
                    status_container = st.empty()
                    results_container = st.empty()
                    
                    # Process each domain individually
                    for idx, company_data in enumerate(companies_payload):
                        domain = company_data["domain"]
                        progress_percentage = idx / len(companies_payload)
                        
                        status_container.info(f"🔄 Processing domain {idx + 1}/{len(companies_payload)}: **{domain}**")
                        progress_bar.progress(progress_percentage)
                        
                        # Process single domain
                        single_payload = [company_data]
                        
                        try:
                            with st.spinner(f"Processing {domain}..."):
                                # Start enrichment for single domain
                                enrich_job = client.start_company_enrichment(single_payload)
                                
                                if enrich_job:
                                    job_id = enrich_job.get('enrichmentID') or enrich_job.get('id')
                                    
                                    if job_id:
                                        # Get results for this domain
                                        single_result = client.get_enrichment_results(job_id)
                                        
                                        if single_result and single_result.get('companies'):
                                            all_results["companies"].extend(single_result["companies"])
                                            successful_domains += 1
                                            status_container.success(f"✅ {domain} - Success!")
                                        else:
                                            failed_domains += 1
                                            status_container.error(f"❌ {domain} - No data returned")
                                    else:
                                        failed_domains += 1
                                        status_container.error(f"❌ {domain} - Job creation failed")
                                else:
                                    failed_domains += 1
                                    status_container.error(f"❌ {domain} - API request failed")
                        
                        except Exception as domain_error:
                            failed_domains += 1
                            status_container.error(f"❌ {domain} - Error: {str(domain_error)}")
                        
                        # Show current statistics
                        with results_container.container():
                            col_stat1, col_stat2, col_stat3 = st.columns(3)
                            with col_stat1:
                                st.metric("✅ Successful", successful_domains)
                            with col_stat2:
                                st.metric("❌ Failed", failed_domains)
                            with col_stat3:
                                st.metric("📊 Remaining", len(companies_payload) - idx - 1)
                        
                        # Delay between requests (only if not the last domain)
                        if idx < len(companies_payload) - 1:
                            time.sleep(delay_between)
                    
                    # Final progress update
                    progress_bar.progress(1.0)
                    status_container.success(f"🎉 Single domain processing complete! {successful_domains} successful, {failed_domains} failed.")
                    
                    # Use the collected results
                    results = all_results if all_results["companies"] else None

                else:
                    # BULK MODE PROCESSING
                    st.subheader("⚡ Bulk Processing")
                    
                    # Show payload preview
                    with st.expander("📋 Payload Preview (First 5 items)"):
                        st.json(companies_payload[:5])
                    
                    with st.spinner(f"Sending {len(companies_payload)} domains for enrichment..."):
                        enrich_job = client.start_company_enrichment(companies_payload)

                    # Debug the API response
                    st.write("🔍 API Response Debug:")
                    if enrich_job:
                        st.json(enrich_job)
                    else:
                        st.error("❌ No response from API")
                        st.stop()

                    job_id = enrich_job.get('enrichmentID') or enrich_job.get('id')
                    if enrich_job and job_id:
                        st.success(f"Enrichment job started successfully! (ID: {job_id})")
                        
                        # Store job ID in session state
                        st.session_state.last_job_id = job_id
                        st.session_state.processing_status = 'polling'
                        
                        # Use batch timeout from settings
                        timeout_seconds = batch_timeout * 60 if 'batch_timeout' in locals() else 300
                        
                        with st.spinner(f"Processing... This can take up to {batch_timeout if 'batch_timeout' in locals() else 5} minutes."):
                            results = client.get_enrichment_results(job_id, max_wait=timeout_seconds)
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
                        st.stop()

                # Continue with results processing (same for both modes)
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
                        stats_dict  = {}
                        for col in enriched_cols:
                            non_empty = df[col].notna().sum()
                            total = len(df)
                            percentage = f"{non_empty/total*100:.1f}%"
                            stats_dict[col.replace('enriched_', '').title()] = percentage
                        st.json(stats_dict)
                    
                    create_download_buttons(df, f"enriched_{uploaded_file.name}")
                else:
                    if enrichment_mode == "🎯 Single Domain Mode":
                        st.error("Single domain processing failed to retrieve any results.")
                        st.info("Check the individual domain results above for more details.")
                    else:
                        st.error("Failed to retrieve enrichment results.")
                        st.info(f"Job ID: {job_id} - You can check this job status later.")
                    
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
