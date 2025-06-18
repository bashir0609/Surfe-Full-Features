import streamlit as st
from utils.api_client import SurfeApiClient, init_session_state
from utils.helpers import enhanced_page_header, create_feature_card, create_stats_grid
import os

# Initialize session state first
init_session_state()

# --- Page Configuration ---
st.set_page_config(
    page_title="Surfe.com API Tools",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# # Load custom CSS using the new absolute path
# load_css(_css_file)

# --- Main Page UI ---
st.title("⚡ Surfe.com API Toolkit")
st.markdown("Welcome! Select a tool from the sidebar to get started.")
st.info("This toolkit provides access to Surfe.com's enrichment, search, and lookalike features.")

# --- THIS IS THE MODIFIED PART ---
# Get the absolute path of the directory where this script is located
_RELEASE = True
if not _RELEASE:
    _main_app_dir = os.path.dirname(os.path.abspath(__file__))
    _css_file = os.path.join(_main_app_dir, "styles.css")
else:
    _css_file = "styles.css"
# --- END OF MODIFIED PART ---

def load_css(file_name):
    """Function to load a local CSS file."""
    # Check if the file exists before trying to open it
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    else:
        st.warning(f"CSS file not found at {os.path.abspath(file_name)}")
        st.info("Please ensure 'styles.css' is in the same directory as 'main_app.py'.")

# --- Sidebar ---
with st.sidebar:
    st.header("🔧 Configuration")
    
    # API Key input with validation
    api_key_input = st.text_input(
        "Surfe.com API Key",
        type="password",
        help="Get your API key from https://app.surfe.com/api-settings",
        key="api_key_input",
        value=st.session_state.get('api_key', '')
    )
    
    # Update session state when API key changes
    if api_key_input != st.session_state.get('api_key', ''):
        st.session_state.api_key = api_key_input

    if not st.session_state.api_key:
        st.warning("Please enter your Surfe API key to use the tools.")
        st.markdown("[Get API Key →](https://app.surfe.com/api-settings)")
        
        # Show expected API key format
        with st.expander("ℹ️ API Key Format"):
            st.write("Your API key should:")
            st.write("- Be a long string (typically 32+ characters)")
            st.write("- Start with letters/numbers")
            st.write("- Not contain spaces")
            st.write("- Be obtained from your Surfe.com dashboard")
    else:
        # Validate API key format
        api_key = st.session_state.api_key.strip()
        
        if len(api_key) < 10:
            st.error("⚠️ API key seems too short. Please check your key.")
        elif ' ' in api_key:
            st.error("⚠️ API key contains spaces. Please remove them.")
        else:
            # Show masked key
            if len(api_key) > 10:
                masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
            else:
                masked_key = "*" * len(api_key)
            st.success(f"API key provided: {masked_key}")
            
            # Test API key button
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔍 Test API Key"):
                    with st.spinner("Testing API key..."):
                        try:
                            client = SurfeApiClient(st.session_state.api_key)
                            
                            # Try to validate the key
                            if client.validate_api_key():
                                st.success("✅ API key is valid!")
                            else:
                                st.error("❌ API key validation failed")
                                st.write("Possible issues:")
                                st.write("- Invalid or expired key")
                                st.write("- Network connectivity issues")
                                st.write("- API service temporarily down")
                        except Exception as e:
                            st.error(f"❌ Error testing API key: {str(e)}")
            
            with col2:
                # Check credits button
                if st.button("💳 Check Credits"):
                    with st.spinner("Checking credits..."):
                        try:
                            client = SurfeApiClient(st.session_state.api_key)
                            credits_info = client.check_credits()
                            if credits_info:
                                st.write("API Credit Information:")
                                st.json(credits_info)
                            else:
                                st.error("Could not retrieve credit information.")
                                st.write("This might indicate:")
                                st.write("- Invalid API key")
                                st.write("- Network issues")
                                st.write("- API endpoint changes")
                        except Exception as e:
                            st.error(f"Error checking credits: {str(e)}")
    
    st.markdown("---")
    st.header("⚙️ Rate Limiting")
    # Store rate limit in session state
    st.session_state.delay = st.slider(
        "Delay between requests (sec)",
        min_value=0.1,
        max_value=5.0,
        value=1.0,
        step=0.1,
        help="Adjusts delay for tools making individual API calls."
    )
    
    # Debug section
    with st.expander("🐛 Debug Information"):
        debug_info = {
            "API Key Length": len(st.session_state.get('api_key', '')),
            "API Key Set": bool(st.session_state.get('api_key')),
            "Session Keys": list(st.session_state.keys()),
            "Processing Status": st.session_state.get('processing_status', 'idle'),
            "Delay Setting": st.session_state.get('delay', 1.0)
        }
        st.json(debug_info)
        
        if st.button("Clear All Session Data"):
            # Clear all session state except current API key
            current_api_key = st.session_state.get('api_key', '')
            for key in list(st.session_state.keys()):
                if key != 'api_key_input':
                    del st.session_state[key]
            st.session_state.api_key = current_api_key
            st.success("Session data cleared!")
    
st.markdown("---")
st.header("🚀 Getting Started")
col1, col2 = st.columns(2)
with col1:
    st.subheader("📋 What You Need")
    st.markdown("""
    1.  **A Surfe.com API Key** (Enter in sidebar ←)
    2.  **A CSV File** with company domains
    3.  **Select your desired data points**
    """)
with col2:
    st.subheader("🛠️ Available Tools")
    st.markdown("""
    -   **Company Enrichment** - Add data to company domains
    -   **Company Search** - Find companies by criteria  
    -   **Company Lookalikes** - Find similar companies
    -   **People Enrichment** - Enrich LinkedIn profiles
    -   **People Search** - Find people by criteria
    """)

# Troubleshooting section
st.markdown("---")
st.header("🔧 Common Issues & Solutions")

with st.expander("❌ 'Failed to start enrichment job' Error"):
    st.markdown("""
    **This error usually means:**
    
    1. **Invalid API Key**
       - Check if your API key is correct
       - Make sure there are no extra spaces
       - Get a fresh key from Surfe.com if needed
    
    2. **Insufficient Credits**
       - Check your credit balance using the button above
       - Contact Surfe.com if you need more credits
    
    3. **Invalid Input Data**
       - Make sure your CSV has valid domain names
       - Domains should be like `example.com` (not URLs)
       - Remove any empty rows
    
    4. **Network/API Issues**
       - Check your internet connection
       - Try again in a few minutes
       - Contact Surfe.com support if persistent
    """)

with st.expander("🐌 App Hanging/Freezing"):
    st.markdown("""
    **If the app seems stuck:**
    
    1. **Refresh the page** (F5 or Ctrl+R)
    2. **Clear session data** using the debug section
    3. **Check file size** - Large files take longer to process
    4. **Wait for timeouts** - Operations timeout after 5 minutes
    5. **Check browser console** for JavaScript errors
    """)

with st.expander("📁 File Upload Issues"):
    st.markdown("""
    **File requirements:**
    
    - **Format**: CSV files only
    - **Size**: Under 200MB recommended  
    - **Domains**: Should be in format `example.com`
    - **Encoding**: UTF-8 preferred
    - **Columns**: Clear column headers
    """)

# Show current status
st.markdown("---")
if st.session_state.get('api_key'):
    st.success("✅ Ready to use! Select a tool from the sidebar.")
else:
    st.info("👈 Enter your API key in the sidebar to get started.")
