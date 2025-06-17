# Surfe.com API Toolkit for Streamlit

This is a multi-page Streamlit application that provides a user-friendly interface for several key features of the [Surfe.com API](https://developers.surfe.com/). It allows users to enrich data, search for companies and people, and find company lookalikes without writing any code.

## ✨ Features

The application is divided into several tools, accessible from the sidebar navigation:

* **🏢 Company Enrichment**: Upload a CSV of company domains and enrich it with 16 different data points, including employee count, industry, location, and more.
* **🔍 Company Search**: Search for companies based on criteria like name, industry, country, and employee count.
* **👯 Company Lookalikes**: Provide a company domain to find a list of similar companies.
* **👥 People Enrichment**: Upload a CSV of LinkedIn profile URLs to enrich them with contact and professional data.
* **🔎 People Search**: Search for individuals based on their name, current company, title, and country.

## 📁 Project Structure

The project is organized into a modular structure for clarity and scalability:

```
/surfe_streamlit_app/
├── 📄 main_app.py               # Main app entry point
├── 📄 requirements.txt            # Project dependencies
├── 📄 styles.css                  # Custom CSS for styling
│
├── 📁 pages/                      # Each file is a page in the app
│   ├── 📄 1_🏢_Company_Enrichment.py
│   ├── 📄 2_🔍_Company_Search.py
│   ├── 📄 3_👯_Company_Lookalikes.py
│   ├── 📄 4_👥_People_Enrichment.py
│   └── 📄 5_🔎_People_Search.py
│
└── 📁 utils/                     # Helper modules
    ├── 📄 api_client.py           # Handles all API calls
    └── 📄 helpers.py              # Data processing functions
```

## 🚀 Getting Started

Follow these instructions to get the application running on your local machine.

### Prerequisites

* Python 3.8+
* A Surfe.com account and API key. You can get one from the [Surfe API Settings](https://app.surfe.com/api-settings) page.

### Installation

1.  **Clone the repository or download the files** and place them in a directory named `surfe_streamlit_app`.

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required dependencies** using the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

The only configuration required is your Surfe.com API Key.

1.  Run the application for the first time.
2.  The sidebar will have a field labeled **"Surfe.com API Key"**.
3.  Enter your key into this field. The key is stored in Streamlit's session state and will need to be entered each time you start the app.

### How to Run

1.  Navigate to the root directory of the project (`/surfe_streamlit_app/`) in your terminal.
2.  Run the following command:
    ```bash
    streamlit run main_app.py
    ```
3.  The application will open in a new tab in your default web browser.

## usage

1.  **Select a Tool**: Use the sidebar to navigate to the desired tool (e.g., Company Enrichment, People Search).
2.  **Follow On-Screen Instructions**:
    * For **enrichment tools**, upload a CSV file and select the column containing the domains or LinkedIn URLs.
    * For **search/lookalike tools**, fill in the form fields with your criteria.
3.  **Run the Tool**: Click the primary action button (e.g., "Start Enrichment", "Search Companies").
4.  **View and Download Results**: The results will be displayed in a table on the page. Use the download buttons to save the data as a CSV or Excel file.