import os
import datetime
import json
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import streamlit.components.v1 as components

# Google Auth & Sheets API
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# 1. Configure Streamlit page
st.set_page_config(
    page_title="Mission Control Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🚀"
)

# 2. Inject custom CSS for "mission control" style
dark_mission_css = """
<style>
body {
    background-color: #000000 !important; /* black */
    color: #00ff00 !important;           /* neon green */
}
.stMarkdown, .stButton, .stSidebar, .css-1n76uvr, .css-10trblm {
    color: #00ff00 !important;
    background-color: #000000 !important;
}
h1, h2, h3, h4 {
    color: #00ff00 !important;
}
textarea, input {
    background-color: #111111 !important;
    color: #00ff00 !important;
    border: 1px solid #00ff00 !important;
}
</style>
"""
st.markdown(dark_mission_css, unsafe_allow_html=True)

# 2b. (NEW) Inject additional CSS to reduce spacing
spacing_tweaks = """
<style>
/* Reduce spacing below subheaders (e.g., h2) */
h2 {
  margin-bottom: 0.5rem !important; /* Adjust as needed */
}

/* Reduce spacing on certain container classes 
   (these are examples; class names may differ in your Streamlit version) */
.css-1n76uvr, .css-12oz5g7, .css-1cpxqw2 {
  margin-bottom: 0rem !important;
  padding-bottom: 0rem !important;
}
</style>
"""
st.markdown(spacing_tweaks, unsafe_allow_html=True)

# 3. Google Sheets credentials
SERVICE_ACCOUNT_FILE = 'service_account.json'  # Or an environment variable/path
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# @st.cache_data
# def fetch_data_from_sheets():
#     creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
#     service = build('sheets', 'v4', credentials=creds)
#     SPREADSHEET_ID = '1TLD5SBqvjAKF_JsWC9owSCF8P-ndLWqgZD8WuLprKR8'  # Replace with your real ID
#     RANGE_NAME = 'Sheet1!A1:B10'
#     sheet = service.spreadsheets()
#     result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
#     values = result.get('values', [])
#     if values:
#         headers = values[0]
#         rows = values[1:]
#         return pd.DataFrame(rows, columns=headers)
#     else:
#         return pd.DataFrame()

@st.cache_data
def fetch_data_from_sheets():
    # Build service_account_info from separate fields in secrets
    service_account_info = {
        "type": st.secrets["SERVICE_ACCOUNT"]["type"],
        "project_id": st.secrets["SERVICE_ACCOUNT"]["project_id"],
        "private_key_id": st.secrets["SERVICE_ACCOUNT"]["private_key_id"],
        "private_key": st.secrets["SERVICE_ACCOUNT"]["private_key"],
        "client_email": st.secrets["SERVICE_ACCOUNT"]["client_email"],
        "client_id": st.secrets["SERVICE_ACCOUNT"]["client_id"],
        "auth_uri": st.secrets["SERVICE_ACCOUNT"]["auth_uri"],
        "token_uri": st.secrets["SERVICE_ACCOUNT"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["SERVICE_ACCOUNT"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["SERVICE_ACCOUNT"]["client_x509_cert_url"],
        "universe_domain": st.secrets["SERVICE_ACCOUNT"]["universe_domain"]
    }

    # Create credentials from the loaded JSON
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)

    # Example: fetch data from a specific spreadsheet & range
    SPREADSHEET_ID = '1TLD5SBqvjAKF_JsWC9owSCF8P-ndLWqgZD8WuLprKR8'  # Replace with your real ID
    RANGE_NAME = 'Sheet1!A1:B10'
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])

    if values:
        headers = values[0]
        rows = values[1:]
        return pd.DataFrame(rows, columns=headers)
    else:
        return pd.DataFrame()


def main():
    st.title("ISV Sankirtan Mission Control")

    # Countdown portion (unchanged) --
    st.subheader("Time Left to Beat Mayapur")
    current_dir = os.path.dirname(__file__)
    countdown_file = os.path.join(current_dir, "countdown.html")
    with open(countdown_file, "r", encoding="utf-8") as f:
        countdown_html = f.read()
    components.html(countdown_html, height=120, scrolling=False)

    # Hard-coded placeholders for demonstration
    ytd_isv_total = 12500
    isv_goal = 20000
    percent_reached = (ytd_isv_total / isv_goal) * 100 if isv_goal else 0
    ytd_mayapur_total = 15000

    # Display the first three side by side
    col1, col2, col3 = st.columns(3)

    # Column 1: YTD ISV + YTD Mayapur
    col1.metric("YTD ISV Total Book Points", f"{ytd_isv_total:,}")
    col1.metric("YTD Mayapur Total Book Points", f"{ytd_mayapur_total:,}")

    # Column 2: End of Year Goal
    col2.metric("ISV End of Year Goal", f"{isv_goal:,}")

    # Column 3: Percentage Reached
    col3.metric("Percentage Goal Reached", f"{percent_reached:.2f}%")

    # Fetch & display data from Google Sheets
    df = fetch_data_from_sheets()
    if df.empty:
        st.write("No data found in the specified range.")
        return

    if "MetricValue" in df.columns:
        df["MetricValue"] = pd.to_numeric(df["MetricValue"], errors='coerce')

    st.subheader("Raw Data")
    st.write(df)

    # Pie Chart
    st.subheader("Pie Chart")
    if "MetricValue" in df.columns and "MetricName" in df.columns:
        fig, ax = plt.subplots()
        fig.patch.set_facecolor('#000000')
        ax.set_facecolor('#000000')
        wedges, texts, autotexts = ax.pie(
            df["MetricValue"],
            labels=df["MetricName"],
            autopct="%1.1f%%",
            textprops={'color': '#00ff00'}
        )
        for text in texts:
            text.set_color('#00ff00')
        for autotext in autotexts:
            autotext.set_color('#00ff00')
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.write("Columns 'MetricName'/'MetricValue' not found, cannot plot pie chart.")

    # Bar Chart
    st.subheader("Bar Chart")
    if "MetricValue" in df.columns and "MetricName" in df.columns:
        fig2, ax2 = plt.subplots()
        fig2.patch.set_facecolor('#000000')
        ax2.set_facecolor('#000000')
        ax2.bar(df["MetricName"], df["MetricValue"], color='#00ff00')
        ax2.spines["left"].set_color('#00ff00')
        ax2.spines["right"].set_color('#00ff00')
        ax2.spines["top"].set_color('#00ff00')
        ax2.spines["bottom"].set_color('#00ff00')
        ax2.tick_params(axis='x', colors='#00ff00')
        ax2.tick_params(axis='y', colors='#00ff00')
        plt.tight_layout()
        st.pyplot(fig2)
    else:
        st.write("Columns 'MetricName'/'MetricValue' not found, cannot plot bar chart.")

if __name__ == "__main__":
    main()
