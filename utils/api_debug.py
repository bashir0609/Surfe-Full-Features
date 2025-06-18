import streamlit as st
import pandas as pd
import requests
import json
from .api_client import SurfeApiClient, SurfeAPIError, AuthenticationError
from .helpers import (
    init_session_state,
    extract_company_data,
    get_default_value,
    create_download_buttons,
)

def run_debug_interface():
    """Main function to run the complete API debug interface."""
    
    st.title("🧪 Complete Surfe API Test & Debug Tool")
    st.markdown("Test **ALL** Surfe API endpoints and understand their request/response structures.")

    if 'api_key' not in st.session_state or not st.session_state.api_key:
        st.error("🚨 Please enter your API key in the sidebar on the main page.")
        st.stop()

    # API Information
    st.markdown("## 🔍 Complete API Information")
    with st.expander("📚 All Known Endpoints & Documentation", expanded=True):
        st.markdown("""
        **Base URL:** `https://api.surfe.com`
        
        **Authentication:** Bearer token in Authorization header
        
        **All Available Endpoints:**
        
        ### 🏢 Company Features
        1. **Company Search:** `POST /v2/companies/search`
        2. **Company Enrichment (Start):** `POST /v2/companies/enrich`
        3. **Company Enrichment (Get):** `GET /v2/companies/enrich/{jobId}`
        4. **Company Lookalikes:** `POST /v2/companies/lookalikes`
        
        ### 👥 People Features
        5. **People Search:** `POST /v2/people/search`
        6. **People Enrichment (Start):** `POST /v2/people/enrich`
        7. **People Enrichment (Get):** `GET /v2/people/enrich/{jobId}`
        
        ### 🔧 Utility Endpoints
        8. **Get Filters:** `GET /v2/people/filters`
        9. **Check Credits:** `GET /v2/account/credits`
        
        **Rate Limits:**
        - 10 requests/second (bursts to 20)
        - 2000 requests/day
        """)

    # Feature Selection
    st.markdown("## 🎯 Select Feature to Test")

    feature_tabs = st.tabs([
        "🔍 Company Search", 
        "🏢 Company Enrichment", 
        "👯 Company Lookalikes", 
        "🔎 People Search", 
        "👥 People Enrichment"
    ])

    # ===== TAB 1: COMPANY SEARCH =====
    with feature_tabs[0]:
        test_company_search()

    # ===== TAB 2: COMPANY ENRICHMENT =====
    with feature_tabs[1]:
        test_company_enrichment()

    # ===== TAB 3: COMPANY LOOKALIKES =====
    with feature_tabs[2]:
        test_company_lookalikes()

    # ===== TAB 4: PEOPLE SEARCH =====
    with feature_tabs[3]:
        test_people_search()

    # ===== TAB 5: PEOPLE ENRICHMENT =====
    with feature_tabs[4]:
        test_people_enrichment()

    # ===== QUICK UTILITY TESTS =====
    st.markdown("---")
    st.markdown("## ⚡ Quick Utility Tests")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔐 Test API Key", key="test_api_key"):
            # Try multiple endpoints to validate API key
            validation_endpoints = [
                "v2/account/credits",
                "v2/credits",
                "v2/account", 
                "v1/account/credits",
                "account"
            ]
            
            st.markdown("**Testing API key with multiple endpoints:**")
            for endpoint in validation_endpoints:
                st.markdown(f"Testing `{endpoint}`...")
                test_api_endpoint(endpoint, None, f"API Key Test ({endpoint})", method="GET")
                st.markdown("---")

    with col2:
        if st.button("📊 Check Credits", key="check_credits"):
            # Try multiple possible credit endpoints
            credit_endpoints = [
                "v2/account/credits",
                "v2/credits", 
                "v1/account/credits",
                "v1/credits",
                "credits",
                "account/credits",
                "account"
            ]
            
            st.markdown("**Testing multiple credit endpoints:**")
            for endpoint in credit_endpoints:
                st.markdown(f"Testing `{endpoint}`...")
                test_api_endpoint(endpoint, None, f"Credit Check ({endpoint})", method="GET")
                st.markdown("---")

    with col3:
        if st.button("🎛️ Get Available Filters", key="get_filters"):
            # Try multiple possible filter endpoints
            filter_endpoints = [
                "v2/people/filters",
                "v2/filters", 
                "v1/people/filters",
                "v1/filters",
                "filters",
                "people/filters",
                "v2/companies/filters",
                "companies/filters"
            ]
            
            st.markdown("**Testing multiple filter endpoints:**")
            for endpoint in filter_endpoints:
                st.markdown(f"Testing `{endpoint}`...")
                test_api_endpoint(endpoint, None, f"Filters ({endpoint})", method="GET")
                st.markdown("---")

    # ===== ENDPOINT DISCOVERY SECTION =====
    st.markdown("---")
    st.markdown("## 🔍 Endpoint Discovery")
    
    with st.expander("🎯 Test Common API Patterns", expanded=False):
        st.markdown("Since `v2/companies/search` works, let's test related patterns:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Working Pattern Tests:**")
            working_tests = [
                "v2/companies",
                "v2/people", 
                "v2/organizations",
                "v2",
                "v1/companies/search",
                "v1/people/search"
            ]
            
            for endpoint in working_tests:
                if st.button(f"Test {endpoint}", key=f"test_{endpoint.replace('/', '_')}"):
                    test_api_endpoint(endpoint, None, f"Pattern Test ({endpoint})", method="GET")
        
        with col2:
            st.markdown("**Custom Endpoint Test:**")
            custom_endpoint = st.text_input("Test custom endpoint:", placeholder="v2/...")
            if st.button("Test Custom Endpoint") and custom_endpoint:
                test_api_endpoint(custom_endpoint, None, f"Custom Test ({custom_endpoint})", method="GET")
    st.markdown("---")
    st.markdown("## 🎯 All-in-One Feature Test")

    if st.button("🚀 Test All Features (Sequential)", key="test_all_features"):
        test_all_features_sequential()

    # ===== DOCUMENTATION SECTION =====
    st.markdown("---")
    st.markdown("## 📚 Implementation Guide")

    with st.expander("🔧 How to Fix Your App Based on Test Results"):
        show_implementation_guide()

def test_company_search():
    """Test company search functionality."""
    st.markdown("### 🔍 Company Search Testing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Simple Search Payload:**")
        company_search_payload = {
            "filters": {
                "name": "Microsoft",
                "industries": ["Software"],
                "countries": ["US"],
                "size": ["1000+"]
            },
            "limit": 5
        }
        st.json(company_search_payload)
    
    with col2:
        st.markdown("**Alternative Search Structure:**")
        alt_company_search = {
            "name": "Google",
            "industry": ["Technology"],
            "country": ["US"],
            "limit": 3
        }
        st.json(alt_company_search)
    
    # Custom payload editor
    company_search_custom = st.text_area(
        "Custom Company Search Payload:", 
        value=json.dumps(company_search_payload, indent=2),
        height=150,
        key="company_search_payload"
    )
    
    if st.button("🚀 Test Company Search", key="test_company_search"):
        test_api_endpoint("v2/companies/search", company_search_custom, "Company Search")

def test_company_enrichment():
    """Test company enrichment functionality."""
    st.markdown("### 🏢 Company Enrichment Testing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Start Enrichment Payload:**")
        company_enrichment_payload = {
            "companies": [
                {"domain": "surfe.com", "externalID": "test_1"},
                {"domain": "microsoft.com", "externalID": "test_2"}
            ]
        }
        st.json(company_enrichment_payload)
    
    with col2:
        st.markdown("**Expected Response:**")
        st.code("""
        {
          "enrichmentID": "abc123",
          "status": "processing"
        }
        """)
    
    company_enrichment_custom = st.text_area(
        "Custom Company Enrichment Payload:", 
        value=json.dumps(company_enrichment_payload, indent=2),
        height=150,
        key="company_enrichment_payload"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Start Company Enrichment", key="start_company_enrichment"):
            test_api_endpoint("v2/companies/enrich", company_enrichment_custom, "Company Enrichment Start")
    
    with col2:
        job_id_input = st.text_input("Job ID for Results:", placeholder="Enter job ID to get results")
        if st.button("📊 Get Enrichment Results", key="get_company_enrichment") and job_id_input:
            test_api_endpoint(f"v2/companies/enrich/{job_id_input}", None, "Company Enrichment Results", method="GET")

def test_company_lookalikes():
    """Test company lookalikes functionality."""
    st.markdown("### 👯 Company Lookalikes Testing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Lookalikes Payload:**")
        lookalikes_payload = {
            "domain": "stripe.com",
            "country": "US"
        }
        st.json(lookalikes_payload)
    
    with col2:
        st.markdown("**Alternative Structure:**")
        alt_lookalikes = {
            "companyDomain": "surfe.com",
            "filters": {
                "countries": ["US", "DE"]
            }
        }
        st.json(alt_lookalikes)
    
    lookalikes_custom = st.text_area(
        "Custom Lookalikes Payload:", 
        value=json.dumps(lookalikes_payload, indent=2),
        height=120,
        key="lookalikes_payload"
    )
    
    if st.button("🚀 Test Company Lookalikes", key="test_lookalikes"):
        test_api_endpoint("v2/companies/lookalikes", lookalikes_custom, "Company Lookalikes")

def test_people_search():
    """Test people search functionality."""
    st.markdown("### 🔎 People Search Testing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**People Search Payload:**")
        people_search_payload = {
            "filters": {
                "name": "John Doe",
                "currentCompany": "microsoft.com",
                "title": "Software Engineer",
                "country": "US"
            },
            "limit": 10
        }
        st.json(people_search_payload)
    
    with col2:
        st.markdown("**Alternative Structure:**")
        alt_people_search = {
            "query": {
                "name": "David",
                "company": "surfe.com",
                "title": "CEO"
            }
        }
        st.json(alt_people_search)
    
    people_search_custom = st.text_area(
        "Custom People Search Payload:", 
        value=json.dumps(people_search_payload, indent=2),
        height=150,
        key="people_search_payload"
    )
    
    if st.button("🚀 Test People Search", key="test_people_search"):
        test_api_endpoint("v2/people/search", people_search_custom, "People Search")

def test_people_enrichment():
    """Test people enrichment functionality."""
    st.markdown("### 👥 People Enrichment Testing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Start People Enrichment:**")
        people_enrichment_payload = {
            "include": {
                "email": True,
                "mobile": True
            },
            "people": [
                {
                    "firstName": "David",
                    "lastName": "Chevalier",
                    "companyDomain": "surfe.com",
                    "linkedinUrl": "https://www.linkedin.com/in/david-maurice-chevalier",
                    "externalID": "person_1"
                }
            ]
        }
        st.json(people_enrichment_payload)
    
    with col2:
        st.markdown("**Alternative Structure:**")
        alt_people_enrichment = {
            "people": [
                {
                    "linkedin_url": "https://linkedin.com/in/someone",
                    "company": "microsoft.com",
                    "externalID": "test_person"
                }
            ]
        }
        st.json(alt_people_enrichment)
    
    people_enrichment_custom = st.text_area(
        "Custom People Enrichment Payload:", 
        value=json.dumps(people_enrichment_payload, indent=2),
        height=180,
        key="people_enrichment_payload"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Start People Enrichment", key="start_people_enrichment"):
            test_api_endpoint("v2/people/enrich", people_enrichment_custom, "People Enrichment Start")
    
    with col2:
        people_job_id = st.text_input("People Job ID:", placeholder="Enter job ID for results")
        if st.button("📊 Get People Results", key="get_people_enrichment") and people_job_id:
            test_api_endpoint(f"v2/people/enrich/{people_job_id}", None, "People Enrichment Results", method="GET")

def test_api_endpoint(endpoint, payload_str, feature_name, method="POST"):
    """Test any API endpoint with proper error handling and response display."""
    try:
        if payload_str and method == "POST":
            payload = json.loads(payload_str)
        else:
            payload = None
        
        # Make API call
        url = f"https://api.surfe.com/{endpoint}"
        headers = {
            "Authorization": f"Bearer {st.session_state.api_key}",
            "Content-Type": "application/json"
        }
        
        st.markdown(f"### 📡 {feature_name} - Request Details")
        st.markdown(f"**URL:** `{url}`")
        st.markdown(f"**Method:** `{method}`")
        st.markdown("**Headers:**")
        st.json({k: v if k != "Authorization" else "Bearer [HIDDEN]" for k, v in headers.items()})
        
        if payload:
            st.markdown("**Payload:**")
            st.json(payload)
        
        with st.spinner(f"Testing {feature_name}..."):
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            else:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        # Display results
        st.markdown(f"### 📊 {feature_name} - Response Details")
        st.markdown(f"**Status Code:** {response.status_code}")
        
        # Status-specific styling
        if response.status_code == 200:
            st.success("✅ API call successful!")
        elif response.status_code == 401:
            st.error("🔐 Authentication failed - check your API key")
        elif response.status_code == 403:
            st.error("🚫 Insufficient credits or access denied")
        elif response.status_code == 404:
            st.error("🔍 Endpoint not found")
        elif response.status_code == 429:
            st.error("⏱️ Rate limit exceeded")
        else:
            st.warning(f"⚠️ Unexpected status code: {response.status_code}")
        
        # Response headers - use details instead of expander to avoid nesting
        if st.checkbox("Show Response Headers", key=f"show_headers_{feature_name.replace(' ', '_')}"):
            st.json(dict(response.headers))
        
        # Response body
        try:
            response_data = response.json()
            st.markdown("**Response Data:**")
            st.json(response_data)
            
            # Feature-specific data analysis
            analyze_response_data(response_data, feature_name)
            
        except json.JSONDecodeError:
            st.markdown("**Raw Response:**")
            st.text(response.text)
            
    except json.JSONDecodeError as e:
        st.error(f"❌ Invalid JSON payload: {e}")
    except requests.RequestException as e:
        st.error(f"❌ Request failed: {e}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
        st.exception(e)

def analyze_response_data(data, feature_name):
    """Analyze response data specific to each feature."""
    if not data:
        return
    
    if "Company Search" in feature_name:
        companies = data.get('companies', [])
        if companies:
            st.info(f"📊 Found {len(companies)} companies")
            if st.checkbox("Show Sample Company Structure", key=f"show_company_{feature_name.replace(' ', '_')}"):
                st.json(companies[0])
                
                # Show available fields
                all_fields = set()
                for company in companies[:3]:
                    all_fields.update(company.keys())
                st.write("**Available Fields:**", sorted(list(all_fields)))
    
    elif "People Search" in feature_name:
        people = data.get('people', [])
        if people:
            st.info(f"👥 Found {len(people)} people")
            if st.checkbox("Show Sample Person Structure", key=f"show_person_{feature_name.replace(' ', '_')}"):
                st.json(people[0])
    
    elif "Enrichment" in feature_name:
        if "enrichmentID" in data or "id" in data:
            job_id = data.get('enrichmentID') or data.get('id')
            st.success(f"🎯 Enrichment job started with ID: `{job_id}`")
        elif "companies" in data or "people" in data:
            items = data.get('companies') or data.get('people', [])
            st.info(f"✨ Enrichment completed for {len(items)} items")
    
    elif "Lookalikes" in feature_name:
        orgs = data.get('organizations', [])
        if orgs:
            st.info(f"👯 Found {len(orgs)} lookalike companies")

def test_all_features_sequential():
    """Test all features in sequence."""
    st.markdown("### Running comprehensive test of all features...")
    
    # Test 1: Company Search
    st.markdown("#### 1. Testing Company Search...")
    test_api_endpoint("v2/companies/search", json.dumps({
        "filters": {"industries": ["Software"], "countries": ["US"]}, 
        "limit": 3
    }), "Company Search")
    
    st.markdown("---")
    
    # Test 2: People Search  
    st.markdown("#### 2. Testing People Search...")
    test_api_endpoint("v2/people/search", json.dumps({
        "filters": {"title": "CEO", "country": "US"}, 
        "limit": 3
    }), "People Search")
    
    st.markdown("---")
    
    # Test 3: Company Lookalikes
    st.markdown("#### 3. Testing Company Lookalikes...")
    test_api_endpoint("v2/companies/lookalikes", json.dumps({
        "domain": "surfe.com"
    }), "Company Lookalikes")
    
    st.markdown("---")
    
    # Test 4: Check Credits
    st.markdown("#### 4. Checking Credits...")
    test_api_endpoint("v2/account/credits", None, "Credit Check", method="GET")

def show_implementation_guide():
    """Show implementation guide for fixing app pages."""
    st.markdown("""
    **After testing each feature above:**
    
    ### 1. Company Search (pages/2_🔍_Company_Search.py)
    - ✅ Update endpoint URL if needed
    - ✅ Fix payload structure based on successful tests
    - ✅ Update response parsing logic
    
    ### 2. Company Enrichment (pages/1_🏢_Company_Enrichment.py)  
    - ✅ Verify enrichment start payload format
    - ✅ Check job polling endpoint and response structure
    - ✅ Update field mapping based on actual response
    
    ### 3. Company Lookalikes (pages/3_👯_Company_Lookalikes.py)
    - ✅ Verify domain parameter structure
    - ✅ Update response parsing for organizations array
    
    ### 4. People Search (pages/5_🔎_People_Search.py)
    - ✅ Update search filters structure
    - ✅ Fix response parsing for people array
    
    ### 5. People Enrichment (pages/4_👥_People_Enrichment.py)
    - ✅ Implement proper enrichment workflow
    - ✅ Update payload structure for people array
    
    ### 6. API Client (utils/api_client.py)
    - ✅ Update all endpoint URLs based on successful tests
    - ✅ Fix any authentication or header issues
    - ✅ Update timeout and retry logic if needed
    """)
    
    st.info("💡 **Pro Tip:** Test each feature individually first, then implement the fixes one by one for systematic debugging!")
