import streamlit as st
import pandas as pd
from utils.api_client import SurfeApiClient, SurfeAPIError, AuthenticationError
from utils.helpers import (
    init_session_state,
    extract_company_data,
    get_default_value,
    create_download_buttons,
)

def is_in_size_range(employee_count, size_range):
    """Check if employee count falls within the specified size range."""
    try:
        if size_range == "1-10":
            return 1 <= employee_count <= 10
        elif size_range == "11-50":
            return 11 <= employee_count <= 50
        elif size_range == "51-200":
            return 51 <= employee_count <= 200
        elif size_range == "201-1000":
            return 201 <= employee_count <= 1000
        elif size_range == "1001-5000":
            return 1001 <= employee_count <= 5000
        elif size_range == "5001-10000":
            return 5001 <= employee_count <= 10000
        elif size_range == "10000+":
            return employee_count > 10000
        return False
    except (ValueError, TypeError):
        return False

# Initialize session state
init_session_state()

# Initialize pagination state
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'next_page_token' not in st.session_state:
    st.session_state.next_page_token = None
if 'current_search_criteria' not in st.session_state:
    st.session_state.current_search_criteria = None
if 'total_results_loaded' not in st.session_state:
    st.session_state.total_results_loaded = 0
if 'selected_employee_sizes' not in st.session_state:
    st.session_state.selected_employee_sizes = []

st.set_page_config(page_title="Company Search", layout="wide")
st.title("🔍 Company Search with Pagination")
st.markdown("Find companies based on specific criteria. Load up to 2000 results using pagination.")

if 'api_key' not in st.session_state or not st.session_state.api_key:
    st.error("🚨 Please enter your API key in the sidebar on the main page.")
    st.stop()

# Valid industry names extracted from successful Surfe API responses
VALID_INDUSTRIES = [
    # Technology & Software
    "Software", "Information Technology", "Computer", "Hardware",
    "Artificial Intelligence", "Machine Learning", "Information Services",
    "Business Intelligence", "Cloud Data Services", "Analytics", "Big Data",
    "Computer Vision", "Internet of Things", "Enterprise Software",
    "Natural Language Processing", "Technical Support", "Consumer Electronics",
    
    # E-Commerce & Retail
    "E-Commerce", "Retail", "Shopping", "Consumer Goods", "Fashion",
    "Lifestyle", "Online Portals", "Coupons", "Marketplace",
    "Price Comparison", "Wholesale", "B2C",
    
    # Manufacturing & Industrial
    "Manufacturing", "Industrial Automation", "Building Material",
    
    # Financial Services
    "Banking", "Financial Services", "Finance", "Credit Cards", "Debit Cards",
    "Accounting", "Investment Banking", "Insurance", "Real Estate",
    "Financial Planning", "Tax Services", "Auditing", "Bookkeeping",
    
    # Professional Services
    "Consulting", "Business Development", "Legal Services", "Law Firms",
    "Marketing", "Advertising", "Public Relations", "Human Resources",
    "Recruiting", "Management Consulting", "Strategy Consulting",
    
    # Telecommunications
    "Internet", "Telecommunications", "Wired Telecommunications", 
    "Wireless", "Mobile", "ISP", "Mobile Devices",
    
    # Transportation & Logistics
    "Freight Service", "Logistics", "Supply Chain Management",
    "Transportation", "Shipping", "Warehousing", "Courier Service",
    
    # Hospitality & Travel
    "Hospitality", "Hotel", "Leisure", "Resorts", "Travel",
    "Travel Accommodations", "Tourism", "Reservations", "Vacation Rental",
    
    # Food & Beverage
    "Food and Beverage", "Snack Food", "Food Processing", 
    "Food Delivery", "Restaurants", "Catering", "Coffee",
    
    # Healthcare
    "Health Care", "Wellness", "Health Insurance", "Medical Devices",
    "Pharmaceuticals", "Biotechnology", "Medical Services",
    
    # Media & Entertainment
    "Media and Entertainment", "Digital Entertainment", "Digital Media",
    "Publishing", "Broadcasting", "Gaming", "Music", "Film",
    
    # Education
    "Education", "E-Learning", "Training", "Universities", "Schools",
    
    # Energy & Utilities
    "Energy", "Oil and Gas", "Renewable Energy", "Utilities", "Solar",
    
    # Construction & Real Estate
    "Construction", "Architecture", "Engineering", "Real Estate Development",
    
    # Automotive
    "Automotive", "Car Manufacturing", "Auto Parts", "Transportation Equipment",
    
    # Government & Non-Profit
    "Government", "Non-Profit", "Public Sector", "Defense", "Military",
    
    # Other Services
    "Language Learning", "Translation Service", "Security",
    "Physical Security", "Homeland Security", "National Security",
    "Electronics", "Telecommunications Equipment"
]

def suggest_industries(partial_input):
    """Suggest industries based on partial input."""
    if not partial_input or len(partial_input) < 2:
        return []
    
    partial_lower = partial_input.lower()
    suggestions = []
    
    # Exact matches first
    for industry in VALID_INDUSTRIES:
        if industry.lower().startswith(partial_lower):
            suggestions.append(industry)
    
    # Then partial matches
    for industry in VALID_INDUSTRIES:
        if partial_lower in industry.lower() and industry not in suggestions:
            suggestions.append(industry)
    
    return suggestions[:8]  # Return top 8 matches

# Initialize selected industries in session state
if 'selected_industries' not in st.session_state:
    st.session_state.selected_industries = []

# Industry management outside of form
st.header("🏭 Industry Selection")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Search & Add Industries:**")
    
    # Industry search input
    industry_search = st.text_input(
        "Type to search industries...", 
        placeholder="e.g., Software, Tech, Banking",
        key="industry_search"
    )
    
    # Show suggestions
    if industry_search and len(industry_search) >= 2:
        suggestions = suggest_industries(industry_search)
        if suggestions:
            st.markdown("**💡 Click to add:**")
            
            # Create columns for suggestion buttons
            suggestion_cols = st.columns(min(len(suggestions), 4))
            for i, suggestion in enumerate(suggestions):
                col_idx = i % 4
                with suggestion_cols[col_idx]:
                    if st.button(
                        f"➕ {suggestion}", 
                        key=f"add_{suggestion}_{i}",
                        help=f"Add {suggestion} to selected industries"
                    ):
                        if suggestion not in st.session_state.selected_industries:
                            st.session_state.selected_industries.append(suggestion)
                            st.rerun()
        else:
            st.info("💭 No matching industries found. Try different keywords.")
            # Allow custom industry input if no suggestions found
            if st.button(f"➕ Add '{industry_search}' as custom industry", key="add_custom"):
                custom_industry = industry_search.strip().title()
                if custom_industry not in st.session_state.selected_industries:
                    st.session_state.selected_industries.append(custom_industry)
                    st.warning(f"⚠️ Added '{custom_industry}' as custom industry. This may not work if the API doesn't recognize it.")
                    st.rerun()
    elif industry_search and len(industry_search) < 2:
        st.info("🔍 Type at least 2 characters to see suggestions")
    
    # Quick popular selections
    if not st.session_state.selected_industries:
        st.markdown("**🔥 Popular Industries:**")
        popular_industries = ["Software", "Information Technology", "E-Commerce", "Banking", "Manufacturing"]
        popular_cols = st.columns(len(popular_industries))
        for i, popular in enumerate(popular_industries):
            with popular_cols[i]:
                if st.button(f"⭐ {popular}", key=f"popular_{i}"):
                    st.session_state.selected_industries.append(popular)
                    st.rerun()

with col2:
    st.markdown("**Selected Industries:**")
    if st.session_state.selected_industries:
        # Show selected industries with remove buttons
        for i, industry in enumerate(st.session_state.selected_industries):
            col_remove1, col_remove2 = st.columns([3, 1])
            with col_remove1:
                st.write(f"✅ {industry}")
            with col_remove2:
                if st.button("❌", key=f"remove_{i}", help=f"Remove {industry}"):
                    st.session_state.selected_industries.remove(industry)
                    st.rerun()
        
        # Clear all button
        if st.button("🗑️ Clear All", key="clear_all_industries"):
            st.session_state.selected_industries = []
            st.rerun()
    else:
        st.info("👆 Search and add industries above")

st.markdown("---")

# Search form
with st.form("search_form"):
    st.header("🔍 Search Configuration")
    col1, col2 = st.columns(2)
    
    with col1:
        # Show selected industries (read-only in form)
        if st.session_state.selected_industries:
            st.success(f"✅ Selected Industries: {', '.join(st.session_state.selected_industries)}")
        else:
            st.warning("⚠️ No industries selected. Add industries above.")
    
    with col2:
        country = st.text_input("Country Code", placeholder="e.g., US, FR, DE")
    
    # Define the valid size ranges
    size_options = ["1-10", "11-50", "51-200", "201-1000", "1001-5000", "5001-10000", "10000+"]
    
    col3, col4 = st.columns(2)
    
    with col3:
        selected_sizes = st.multiselect(
            "Employee Count Range", 
            options=size_options,
            help="Select one or more size ranges (filtered client-side)."
        )
    
    with col4:
        results_per_page = st.number_input("Results per page", min_value=25, max_value=200, value=200)
    
    # Submit button
    submitted = st.form_submit_button("🔍 Search Companies", use_container_width=True)

# Handle form submission (new search)
if submitted:
    # Reset pagination state for new search
    st.session_state.search_results = []
    st.session_state.next_page_token = None
    st.session_state.total_results_loaded = 0
    st.session_state.selected_employee_sizes = selected_sizes
    
    # Build the filters using selected industries
    filters = {}
    
    if st.session_state.selected_industries:
        filters["industries"] = st.session_state.selected_industries
    
    if country and country.strip():
        country_list = [c.strip().upper() for c in country.split(',') if c.strip()]
        if country_list:
            filters["countries"] = country_list
    
    # Validate minimum filters
    filter_count = sum([
        bool(st.session_state.selected_industries),
        bool(country and country.strip())
    ])
    
    if filter_count < 2:
        st.warning("⚠️ Please select at least **ONE industry** AND enter a **country code**.")
        st.info("💡 **Steps:**")
        st.write("1. Type in the industry search box above (e.g., 'Software')")
        st.write("2. Click on suggested industries to add them")
        st.write("3. Enter a country code (e.g., 'US')")
        if selected_sizes:
            st.info("📊 **Note:** Employee count filtering will be applied after getting results from the API.")
        st.stop()
    
    # Store search criteria for pagination
    st.session_state.current_search_criteria = {
        "filters": filters,
        "limit": results_per_page
    }
    
    # Perform initial search
    try:
        client = SurfeApiClient(st.session_state.api_key)
        with st.spinner("Searching for companies..."):
            results = client.search_companies(st.session_state.current_search_criteria)
        
        if results is None:
            st.error("❌ API request failed. Please try again in a few minutes.")
            st.stop()
        
        # Show debug info
        with st.expander("🔍 Debug: API Response"):
            st.json(results)
        
        companies = results.get('companies', []) if results else []
        
        if companies:
            st.session_state.search_results = companies
            st.session_state.next_page_token = results.get('nextPageToken')
            st.session_state.total_results_loaded = len(companies)
            
            st.success(f"✅ Found {len(companies)} companies in first page!")
            
        else:
            st.info("No companies found matching your criteria.")
            st.write("**Full API Response:**")
            st.json(results)
            st.stop()

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        st.exception(e)
        st.stop()

# Show current results if any exist
if st.session_state.search_results:
    
    # Apply client-side employee count filtering
    filtered_companies = st.session_state.search_results
    if st.session_state.selected_employee_sizes:
        original_count = len(filtered_companies)
        filtered_companies = []
        for company in st.session_state.search_results:
            employee_count = company.get('employeeCount', 0)
            if employee_count and any(is_in_size_range(employee_count, size_range) for size_range in st.session_state.selected_employee_sizes):
                filtered_companies.append(company)
        
        if len(filtered_companies) != original_count:
            st.info(f"📊 Employee count filter: {original_count} → {len(filtered_companies)} companies")
    
    # Results header
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.session_state.selected_employee_sizes:
            st.success(f"📊 Showing {len(filtered_companies)} companies (from {st.session_state.total_results_loaded} total loaded)")
        else:
            st.success(f"📊 Showing {len(filtered_companies)} companies")
    
    with col2:
        # Load More button
        if st.session_state.next_page_token and st.session_state.total_results_loaded < 10000:
            if st.button("📥 Load More Results", key="load_more"):
                try:
                    client = SurfeApiClient(st.session_state.api_key)
                    
                    # Add nextPageToken to search criteria
                    next_page_criteria = st.session_state.current_search_criteria.copy()
                    next_page_criteria["nextPageToken"] = st.session_state.next_page_token
                    
                    with st.spinner("Loading more results..."):
                        results = client.search_companies(next_page_criteria)
                    
                    if results and results.get('companies'):
                        new_companies = results.get('companies', [])
                        st.session_state.search_results.extend(new_companies)
                        st.session_state.next_page_token = results.get('nextPageToken')
                        st.session_state.total_results_loaded += len(new_companies)
                        
                        st.success(f"✅ Loaded {len(new_companies)} more companies! Total: {st.session_state.total_results_loaded}")
                        st.rerun()
                    else:
                        st.info("No more results available.")
                        st.session_state.next_page_token = None
                        
                except Exception as e:
                    st.error(f"Error loading more results: {e}")
        
        elif st.session_state.total_results_loaded >= 2000:
            st.info("📊 Maximum 2000 results loaded")
        elif not st.session_state.next_page_token:
            st.info("📄 No more pages available")
    
    with col3:
        # Clear results button
        if st.button("🗑️ Clear Results", key="clear_results"):
            st.session_state.search_results = []
            st.session_state.next_page_token = None
            st.session_state.total_results_loaded = 0
            st.session_state.current_search_criteria = None
            st.rerun()
    
    # Show pagination info
    if st.session_state.next_page_token:
        pages_loaded = (st.session_state.total_results_loaded // st.session_state.current_search_criteria.get('limit', 200)) + 1
        st.info(f"📄 Pages loaded: {pages_loaded} | Total results: {st.session_state.total_results_loaded} | Next page available")
    else:
        st.info(f"📄 All available results loaded: {st.session_state.total_results_loaded} companies")
    
    # Display results
    if filtered_companies:
        df = pd.DataFrame(filtered_companies)
        st.dataframe(df, use_container_width=True)
        
        # Show sample company data
        with st.expander("📊 Sample Company Data Structure"):
            st.json(filtered_companies[0])
            
            # Show available fields
            all_fields = set()
            for company in filtered_companies[:3]:
                all_fields.update(company.keys())
            st.write("**Available Fields:**", sorted(list(all_fields)))
        
        # Download buttons
        create_download_buttons(df, f"company_search_results_{st.session_state.total_results_loaded}")
        
    else:
        st.warning("No companies match your employee count filter criteria.")

# Show search tips
st.markdown("---")
st.header("💡 Search Tips")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🎯 How to Search")
    st.markdown("""
    **🏭 Industry Selection:**
    1. **Type keywords** in the search box (e.g., "tech", "soft", "bank")
    2. **Click suggestions** to add industries to your search
    3. **Remove industries** by clicking the ❌ button
    4. **Use popular options** for quick selection
    
    **🌍 Country Codes:**
    - `US` (United States), `DE` (Germany), `FR` (France)
    - `CA` (Canada), `GB` (United Kingdom), `AU` (Australia)
    
    **✅ Requirements:**
    - **At least 1 industry** + **1 country** required
    - Both filters must be provided for API to work
    """)

with col2:
    st.subheader("💡 Pro Tips")
    st.markdown("""
    **🔍 Industry Search Tips:**
    - Try **broad terms**: "tech" finds "Technology", "Information Technology"
    - Try **specific terms**: "AI" finds "Artificial Intelligence"
    - **Multiple industries** = broader results
    - **Single industry** = more focused results
    
    **📊 Getting More Results:**
    - Use **popular industries** (Software, E-Commerce, Banking)
    - Try **related industries** together (Software + Information Technology)
    - Use **broad countries** (US has most companies)
    
    **⚡ Autocomplete Features:**
    - **Real-time suggestions** as you type
    - **Smart matching** finds partial and exact matches
    - **Visual selection** with click-to-add buttons
    - **Easy removal** of selected industries
    """)

# Clear all selected industries button
if st.session_state.selected_industries:
    st.markdown("---")
    if st.button("🗑️ Clear All Selected Industries", key="clear_all_bottom"):
        st.session_state.selected_industries = []
        st.rerun()

with col2:
    st.subheader("📊 Pagination Features")
    st.markdown("""
    **🔄 How Pagination Works:**
    - Each page loads up to 200 companies
    - Click "Load More" to get next page
    - Continue until you reach 2000 total results
    - Results accumulate in the table
    
    **📈 Pro Tips:**
    - Start with broad search criteria
    - Use employee count filter after loading results
    - Download results before clearing
    - Monitor your daily quota (2000 total searches)
    
    **⚡ Performance:**
    - Broader searches = more total results available
    - Specific industries = fewer pages needed
    - Employee filtering happens client-side (faster)
    """)

with st.expander("🔧 Troubleshooting Pagination"):
    st.markdown("""
    **If Load More doesn't work:**
    
    1. **Check API Response** - Expand debug section to see if nextPageToken exists
    2. **Verify Search Criteria** - Make sure original search worked
    3. **Check Daily Quota** - You might have hit the 2000/day limit
    4. **Refresh Page** - If pagination state gets corrupted
    5. **Try Simpler Search** - Broader criteria often have more pages available
    
    **Expected Behavior:**
    - First search: Gets up to 200 results + nextPageToken
    - Load More: Uses nextPageToken to get next 200 results
    - Continues until no more nextPageToken or 2000 total results
    """)
