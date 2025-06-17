import requests
import time
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Custom Exception Classes for granular error handling ---
class SurfeAPIError(Exception):
    """Base exception for Surfe API errors."""
    pass

class AuthenticationError(SurfeAPIError):
    """Raised for API key-related errors (401, 403)."""
    pass

class RateLimitError(SurfeAPIError):
    """Raised when the API rate limit is exceeded (429)."""
    pass

class SurfeApiClient:
    """A client to interact with the Surfe.com v2 API."""
    
    BASE_URL = "https://api.surfe.com/v2"

    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API key is required.")
        
        self.api_key = api_key
        
        # Create session with proper configuration
        self.session = requests.Session()
        
        # Configure retry strategy to handle temporary failures
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers properly
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Connection': 'close'  # Prevent hanging connections
        }

    def _post(self, endpoint, json_payload, timeout=30):
        """Helper for POST requests."""
        try:
            response = self.session.post(
                f"{self.BASE_URL}{endpoint}",
                headers=self.headers,  # Use self.headers, not self.session.headers
                json=json_payload,
                timeout=timeout,
                stream=False  # Don't stream to avoid hanging
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                st.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self._post(endpoint, json_payload, timeout)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            st.error("⏰ Request timed out. Please try again.")
            return None
        except requests.exceptions.ConnectionError:
            st.error("🌐 Connection error. Please check your internet connection.")
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                st.error("🔐 Invalid API key. Please check your credentials.")
            elif e.response.status_code == 403:
                st.error("❌ Access denied. Check your API permissions.")
            else:
                st.error(f"HTTP Error {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return None

    def _get(self, endpoint, timeout=30):
        """Helper for GET requests."""
        try:
            response = self.session.get(
                f"{self.BASE_URL}{endpoint}",
                headers=self.headers,  # Use self.headers
                timeout=timeout,
                stream=False
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                st.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self._get(endpoint, timeout)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            st.error("⏰ Request timed out. Please try again.")
            return None
        except requests.exceptions.ConnectionError:
            st.error("🌐 Connection error. Please check your internet connection.")
            return None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                st.error("🔐 Invalid API key. Please check your credentials.")
            elif e.response.status_code == 403:
                st.error("❌ Access denied. Check your API permissions.")
            else:
                st.error(f"HTTP Error {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return None

    def start_company_enrichment(self, companies_payload):
        """Starts a bulk company enrichment job."""
        # Validate payload size
        if len(companies_payload) > 1000:
            st.warning("Large batch detected. This may take several minutes.")
        
        return self._post("/companies/enrich", {"companies": companies_payload}, timeout=60)

    def get_enrichment_results(self, job_id, max_wait=300):
        """Polls for the results of an enrichment job with progress tracking."""
        url = f"/companies/enrich/{job_id}"
        start_time = time.time()
        poll_count = 0
        
        # Create progress containers
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            while time.time() - start_time < max_wait:
                poll_count += 1
                elapsed = time.time() - start_time
                progress = min(elapsed / max_wait, 0.95)  # Never show 100% until complete
                
                progress_bar.progress(progress)
                status_text.text(f"Polling job status... (Attempt {poll_count}, {elapsed:.0f}s elapsed)")
                
                result = self._get(url, timeout=30)
                
                if not result:
                    status_text.error("Failed to get job status")
                    return None
                
                status = result.get('status', 'processing').lower()
                
                if status == 'completed':
                    progress_bar.progress(1.0)
                    status_text.success("✅ Job completed successfully!")
                    # Clear progress indicators after a moment
                    time.sleep(1)
                    progress_bar.empty()
                    status_text.empty()
                    return result
                elif status == 'failed':
                    progress_bar.empty()
                    status_text.error(f"❌ Job failed: {result.get('message', 'Unknown error')}")
                    return None
                elif status in ['processing', 'pending']:
                    # Show more detailed status if available
                    progress_info = result.get('progress', {})
                    if progress_info:
                        completed = progress_info.get('completed', 0)
                        total = progress_info.get('total', 0)
                        if total > 0:
                            job_progress = completed / total
                            status_text.text(f"Processing... {completed}/{total} completed ({job_progress:.1%})")
                
                # Wait before next poll, but allow for early termination
                for i in range(10):  # 10 seconds total
                    time.sleep(1)
                    # Check if user navigated away or if there's a stop signal
                    if not st.session_state.get('processing_status') == 'polling':
                        progress_bar.empty()
                        status_text.empty()
                        return None
            
            # Timeout reached
            progress_bar.empty()
            status_text.warning(f"⏰ Job timed out after {max_wait} seconds. Job ID: {job_id}")
            st.info("You can check the job status later or contact support if the job is still processing.")
            return None
            
        except KeyboardInterrupt:
            progress_bar.empty()
            status_text.warning("Job polling cancelled by user.")
            return None
        except Exception as e:
            progress_bar.empty()
            status_text.error(f"Error during polling: {str(e)}")
            return None

    def search_companies(self, search_criteria):
        """Search for companies based on criteria."""
        return self._post("/companies/search", search_criteria)
    
    def search_people(self, search_criteria):
        """Search for people based on criteria."""
        return self._post("/people/search", search_criteria)
        
    def get_company_lookalikes(self, domain, country=None):
        """Find companies similar to a given company domain."""
        payload = {"domain": domain}
        if country:
            payload["country"] = country
        return self._post("/organizations/lookalikes", payload)

    def start_people_enrichment(self, people_payload):
        """Starts a bulk people enrichment job."""
        # Note: The endpoint might differ based on API version. This is a common pattern.
        return self._post("/people/enrich", {"people": people_payload})

    def check_credits(self):
        """Check API credits."""
        return self._get("/account/credits")
    
    def validate_api_key(self):
        """Validate API key by making a simple request."""
        try:
            result = self.check_credits()
            return result is not None
        except Exception:
            return False
    
    def close(self):
        """Close the session to free up resources."""
        if hasattr(self, 'session'):
            self.session.close()
    
    # def get_filters(self):
    #     """Gets the available filters for searching from the /people-filters endpoint."""
    #     return self._get("/people-filters")

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
