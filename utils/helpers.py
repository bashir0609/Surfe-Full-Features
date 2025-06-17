import pandas as pd
import numpy as np
import re
import streamlit as st
from io import BytesIO
from datetime import datetime

# --- Data Conversion and Cleaning ---
def safe_convert_numeric(value, default=None):
    if value is None or value == '' or str(value).strip() == '':
        return default
    try:
        cleaned = re.sub(r'[^\d.-]', '', str(value).strip())
        return pd.to_numeric(cleaned, errors='coerce') if cleaned else default
    except (ValueError, TypeError):
        return default

def safe_convert_string(value, default=""):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return default
    if isinstance(value, list):
        return ', '.join([str(item) for item in value if item is not None])
    return str(value) if value else default

def get_default_value(data_type):
    return None if data_type == "numeric" else ""

def calculate_company_size(employee_count):
    try:
        count = int(employee_count)
        if count <= 10: return '1-10'
        if count <= 50: return '11-50'
        if count <= 200: return '51-200'
        if count <= 1000: return '201-1000'
        return '1000+'
    except (ValueError, TypeError, AttributeError):
        return ''
    
def validate_domain(domain):
    """Validate and clean domain format."""
    if not domain or pd.isna(domain):
        return None
    
    domain_str = str(domain).strip().lower()
    
    # Remove common prefixes
    domain_str = domain_str.replace('https://', '').replace('http://', '').replace('www.', '')
    
    # Remove trailing slashes and paths
    domain_str = domain_str.split('/')[0]
    
    # Basic validation - must contain a dot
    if '.' not in domain_str:
        return None
        
    return domain_str

def format_linkedin_url(url):
    """
    Cleans and standardizes a LinkedIn company URL to a consistent format.
    """
    if not url or not isinstance(url, str):
        return ""
    
    clean_url = url.strip()
    
    # If it's already a valid-looking URL, just standardize it
    if 'linkedin.com/company' in clean_url:
        # Remove query parameters
        clean_url = clean_url.split('?')[0]
        # Ensure it ends with a slash
        if not clean_url.endswith('/'):
            clean_url += '/'
        # Ensure it uses https and www
        if clean_url.startswith('http://'):
            clean_url = clean_url.replace('http://', 'https://')
        if not clean_url.startswith('https://'):
             clean_url = 'https://' + clean_url
        if 'www.' not in clean_url:
            clean_url = clean_url.replace('https://', 'https://www.')

        return clean_url
    
    # If it's just a slug (e.g., 'google'), build the full URL
    if '/' not in clean_url:
        return f"https://www.linkedin.com/company/{clean_url}/"
        
    return url # Return original if it's an unrecognized format

# --- Data Extraction ---
def extract_company_data(enrichment_result, selected_data_points_keys):
    """
    Extracts company data from the enrichment response, explicitly mapping
    API field names (e.g., 'linkedinURL') to internal app keys (e.g., 'linkedin').
    """
    companies = enrichment_result.get('companies', [])
    if not companies:
        st.warning("API response did not contain company data.")
        return {}

    results_map = {}
    for company in companies:
        try:
            # Get the row index from the externalID
            external_id = company.get('externalID')
            if not external_id or not external_id.startswith('row_'):
                continue
            row_index = int(external_id.split('_')[1])
            
            extracted_data = {}
            for key in selected_data_points_keys:
                value = None
                
                # --- Specific Key Mapping Logic ---
                if key == 'linkedin':
                    # Look for the data in 'linkedinURL' or 'linkedInURL' from the API
                    value = company.get('linkedinURL') or company.get('linkedInURL')
                
                elif key == 'website':
                    # Handle the 'websites' array from the API
                    websites_list = company.get('websites', [])
                    if isinstance(websites_list, list) and websites_list:
                        value = websites_list[0]

                elif key == 'employees':
                    # Look for the data in 'employeeCount' from the API
                    value = company.get('employeeCount')

                elif key == 'size':
                    # Calculate size from employee count
                    value = calculate_company_size(company.get('employeeCount'))
                
                else:
                    # For all other keys, get the value directly
                    value = company.get(key)
                
                # Use safe conversion for final assignment
                if isinstance(value, (int, float)):
                     extracted_data[key] = safe_convert_numeric(value)
                else:
                     extracted_data[key] = safe_convert_string(value)

            results_map[row_index] = extracted_data
        except (ValueError, IndexError):
            continue
            
    return results_map

# --- UI & Download Helpers ---
def create_download_buttons(df, file_name_prefix):
    """Generates CSV and Excel download buttons for a DataFrame."""
    st.markdown("---")
    st.header("💾 Download Results")
    
    col1, col2 = st.columns(2)

    # CSV download
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    
    col1.download_button(
        label="📥 Download as CSV",
        data=csv_buffer.getvalue(),
        file_name=f"{file_name_prefix}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    # Excel download
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    
    col2.download_button(
        label="📊 Download as Excel",
        data=excel_buffer.getvalue(),
        file_name=f"{file_name_prefix}_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    

# Helper function to initialize session state (move this to a separate utils file)
def init_session_state():
    """Initialize session state variables to prevent hanging."""
    default_values = {
        'processing_status': 'idle',
        'api_key': '',
        'delay': 1.0,
        'last_job_id': None,
        'enrichment_results': None,
        'error_count': 0
    }
    
    for key, default_value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = default_value