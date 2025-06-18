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
        if count <= 5000: return '1001-5000'
        if count <= 10000: return '5001-10000'
        return '10000+'
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

# NEW FUNCTIONS - Add these to fix display issues
def safe_convert_for_display(value, target_type="string"):
    """
    Safely convert values for display in Streamlit DataFrame
    Handles None, NaN, and various data types
    """
    # Handle None and NaN values
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "" if target_type == "string" else None
    
    # Handle empty strings
    if value == "" or str(value).strip() == "":
        return "" if target_type == "string" else None
    
    try:
        if target_type == "numeric":
            # Clean numeric values
            if isinstance(value, (int, float)):
                return value
            
            # Convert string to numeric
            cleaned = str(value).strip()
            # Remove common non-numeric characters
            cleaned = cleaned.replace(',', '').replace('$', '').replace('%', '')
            
            # Try to convert to numeric
            numeric_val = pd.to_numeric(cleaned, errors='coerce')
            return numeric_val if not pd.isna(numeric_val) else None
            
        else:  # string type
            if isinstance(value, list):
                # Handle arrays/lists by joining them
                return ', '.join([str(item) for item in value if item is not None])
            
            # Convert to string
            result = str(value).strip()
            return result if result and result != 'nan' and result != 'None' else ""
            
    except Exception as e:
        # If all else fails, return appropriate default
        return "" if target_type == "string" else None

def prepare_dataframe_for_display(df):
    """
    Prepare DataFrame for Streamlit display by fixing data types
    """
    # Create a copy to avoid modifying original
    display_df = df.copy()
    
    # Fix each column individually
    for col in display_df.columns:
        try:
            # Check if column contains mixed types
            if display_df[col].dtype == 'object':
                # Convert object columns to string, handling various data types
                display_df[col] = display_df[col].apply(
                    lambda x: safe_convert_for_display(x, "string")
                )
            elif display_df[col].dtype in ['int64', 'float64']:
                # Ensure numeric columns are clean
                display_df[col] = display_df[col].apply(
                    lambda x: safe_convert_for_display(x, "numeric")
                )
        except Exception as e:
            # If column conversion fails, convert to string as fallback
            display_df[col] = display_df[col].astype(str).replace(['nan', 'None', 'NaN'], '')
    
    return display_df

# --- Data Extraction - UPDATED VERSION ---
def extract_company_data(enrichment_result, selected_data_points_keys):
    """
    Extracts company data from the enrichment response with improved error handling
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
                    emp_count = company.get('employeeCount')
                    value = calculate_company_size(emp_count) if emp_count else ""
                
                else:
                    # For all other keys, get the value directly
                    value = company.get(key)
                
                # Use improved safe conversion based on expected data type
                if key in ['employees', 'founded']:  # Numeric fields
                    extracted_data[key] = safe_convert_for_display(value, "numeric")
                else:  # String fields
                    extracted_data[key] = safe_convert_for_display(value, "string")
                    
                # Special formatting for LinkedIn URLs
                if key == 'linkedin' and extracted_data[key]:
                    extracted_data[key] = format_linkedin_url(extracted_data[key])

            results_map[row_index] = extracted_data
        except (ValueError, IndexError) as e:
            continue
            
    return results_map

# --- UI & Download Helpers ---
def create_download_buttons(df, file_name_prefix):
    """Generates CSV and Excel download buttons for a DataFrame with error handling."""
    st.markdown("---")
    st.header("💾 Download Results")
    
    col1, col2 = st.columns(2)

    try:
        # Prepare DataFrame for download by cleaning it
        download_df = prepare_dataframe_for_display(df)
        
        # CSV download
        csv_buffer = BytesIO()
        download_df.to_csv(csv_buffer, index=False)
        
        col1.download_button(
            label="📥 Download as CSV",
            data=csv_buffer.getvalue(),
            file_name=f"{file_name_prefix}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        # Excel download
        excel_buffer = BytesIO()
        download_df.to_excel(excel_buffer, index=False, engine='openpyxl')
        
        col2.download_button(
            label="📊 Download as Excel",
            data=excel_buffer.getvalue(),
            file_name=f"{file_name_prefix}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        
    except Exception as e:
        st.error(f"Error preparing download files: {e}")
        st.info("Try copying the data from the table above or contact support if the issue persists.")

# Helper function to initialize session state (move this to a separate utils file)
def init_session_state():
    """Initialize session state variables to prevent hanging."""
    default_values = {
        'processing_status': 'idle',
        'api_key': '',
        'delay': 1.0,
        'last_job_id': None,
        'enrichment_results': None,
        'error_count': 0,
        'debug_mode': False
    }
    
    for key, default_value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Add these functions to your utils/helpers.py file for enhanced UI components

def create_feature_card(title, description, icon="⚡", color="primary"):
    """Create a beautiful feature card with icon and description"""
    color_classes = {
        "primary": "border-l-4 border-blue-500 bg-blue-50",
        "success": "border-l-4 border-green-500 bg-green-50", 
        "warning": "border-l-4 border-yellow-500 bg-yellow-50",
        "danger": "border-l-4 border-red-500 bg-red-50"
    }
    
    st.markdown(f"""
    <div class="feature-card">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <span style="font-size: 2rem; margin-right: 1rem;">{icon}</span>
            <h3 style="margin: 0; color: var(--text-primary); font-weight: 600;">{title}</h3>
        </div>
        <p style="color: var(--text-secondary); margin: 0; line-height: 1.6;">{description}</p>
    </div>
    """, unsafe_allow_html=True)

def create_status_badge(text, status="success"):
    """Create a status badge with different colors"""
    status_colors = {
        "success": "var(--secondary-color)",
        "warning": "var(--accent-color)", 
        "error": "var(--danger-color)",
        "info": "var(--primary-color)"
    }
    
    color = status_colors.get(status, status_colors["info"])
    
    st.markdown(f"""
    <span class="status-badge {status}" style="
        background: rgba(99, 102, 241, 0.1);
        color: {color};
        border: 1px solid {color};
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: inline-block;
    ">{text}</span>
    """, unsafe_allow_html=True)

def create_gradient_header(text, subtitle=None):
    """Create a beautiful gradient header"""
    header_html = f"""
    <div style="text-align: center; margin: 2rem 0;">
        <h1 class="gradient-text" style="
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
            font-size: 3rem;
            margin-bottom: 0.5rem;
        ">{text}</h1>
    """
    
    if subtitle:
        header_html += f"""
        <p style="
            color: var(--text-secondary);
            font-size: 1.25rem;
            margin-top: 0.5rem;
            font-weight: 400;
        ">{subtitle}</p>
        """
    
    header_html += "</div>"
    
    st.markdown(header_html, unsafe_allow_html=True)

def create_stats_grid(stats_dict):
    """Create a beautiful stats grid"""
    cols = st.columns(len(stats_dict))
    
    for i, (label, value) in enumerate(stats_dict.items()):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-container" style="
                background: var(--background-card);
                border: 1px solid var(--border-color);
                border-radius: var(--border-radius);
                padding: 1.5rem;
                text-align: center;
                box-shadow: var(--shadow-sm);
                transition: all 0.3s ease;
            ">
                <div style="
                    font-size: 2.5rem;
                    font-weight: 700;
                    color: var(--primary-color);
                    margin-bottom: 0.5rem;
                ">{value}</div>
                <div style="
                    color: var(--text-secondary);
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    font-size: 0.875rem;
                ">{label}</div>
            </div>
            """, unsafe_allow_html=True)

def create_progress_card(title, current, total, description=""):
    """Create a progress card with percentage"""
    percentage = (current / total * 100) if total > 0 else 0
    
    st.markdown(f"""
    <div style="
        background: var(--background-card);
        border: 1px solid var(--border-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-sm);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h4 style="margin: 0; color: var(--text-primary);">{title}</h4>
            <span style="font-weight: 600; color: var(--primary-color);">{percentage:.1f}%</span>
        </div>
        
        <div style="
            background: var(--border-color);
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 0.5rem;
        ">
            <div style="
                background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
                height: 100%;
                width: {percentage}%;
                transition: width 0.3s ease;
            "></div>
        </div>
        
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: var(--text-secondary); font-size: 0.875rem;">{description}</span>
            <span style="color: var(--text-muted); font-size: 0.875rem;">{current}/{total}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_alert_box(message, alert_type="info", dismissible=False):
    """Create a beautiful alert box"""
    icons = {
        "info": "ℹ️",
        "success": "✅", 
        "warning": "⚠️",
        "error": "❌"
    }
    
    colors = {
        "info": ("rgba(59, 130, 246, 0.1)", "#3b82f6"),
        "success": ("rgba(16, 185, 129, 0.1)", "var(--secondary-color)"),
        "warning": ("rgba(245, 158, 11, 0.1)", "var(--accent-color)"),
        "error": ("rgba(239, 68, 68, 0.1)", "var(--danger-color)")
    }
    
    bg_color, border_color = colors.get(alert_type, colors["info"])
    icon = icons.get(alert_type, icons["info"])
    
    st.markdown(f"""
    <div style="
        background: {bg_color};
        border-left: 4px solid {border_color};
        border-radius: var(--border-radius-sm);
        padding: 1rem;
        margin: 1rem 0;
        display: flex;
        align-items: center;
    ">
        <span style="font-size: 1.25rem; margin-right: 0.75rem;">{icon}</span>
        <span style="color: var(--text-primary);">{message}</span>
    </div>
    """, unsafe_allow_html=True)

# Example usage functions for your pages:

def enhanced_page_header(title, subtitle, icon="⚡"):
    """Enhanced header for pages"""
    st.markdown(f"""
    <div style="text-align: center; margin: 2rem 0 3rem 0;">
        <div style="font-size: 4rem; margin-bottom: 1rem;">{icon}</div>
        <h1 style="
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
            font-size: 3rem;
            margin-bottom: 0.5rem;
        ">{title}</h1>
        <p style="
            color: var(--text-secondary);
            font-size: 1.25rem;
            margin-top: 0.5rem;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        ">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def create_step_indicator(steps, current_step):
    """Create a step indicator for multi-step processes"""
    step_html = """
    <div style="display: flex; justify-content: center; margin: 2rem 0;">
    """
    
    for i, step in enumerate(steps):
        is_current = i == current_step
        is_completed = i < current_step
        
        if is_completed:
            color = "var(--secondary-color)"
            bg = "var(--secondary-color)"
            text_color = "white"
        elif is_current:
            color = "var(--primary-color)"
            bg = "var(--primary-color)"
            text_color = "white"
        else:
            color = "var(--border-color)"
            bg = "var(--background-secondary)"
            text_color = "var(--text-muted)"
        
        step_html += f"""
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            margin: 0 1rem;
        ">
            <div style="
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: {bg};
                border: 2px solid {color};
                display: flex;
                align-items: center;
                justify-content: center;
                color: {text_color};
                font-weight: 600;
                margin-bottom: 0.5rem;
            ">{i + 1}</div>
            <span style="
                color: {text_color};
                font-size: 0.875rem;
                text-align: center;
                max-width: 80px;
            ">{step}</span>
        </div>
        """
        
        if i < len(steps) - 1:
            step_html += f"""
            <div style="
                flex: 1;
                height: 2px;
                background: {color};
                margin: 20px 0.5rem 0 0.5rem;
                max-width: 100px;
            "></div>
            """
    
    step_html += "</div>"
    st.markdown(step_html, unsafe_allow_html=True)
