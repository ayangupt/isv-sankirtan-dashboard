import os
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
    background-color: #000000 !important; /* Black background */
    color: #00ff00 !important;           /* Neon green text */
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

# 2b. Inject additional CSS to reduce spacing
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
SPREADSHEET_ID = '1TLD5SBqvjAKF_JsWC9owSCF8P-ndLWqgZD8WuLprKR8'  # Replace with your actual Spreadsheet ID
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

def fetch_data_from_sheets(range_name):
    """
    Fetches data from a specified range within the Google Sheets document.

    Args:
        range_name (str): The range to fetch data from (e.g., 'Charts!A1:B10').

    Returns:
        pd.DataFrame: DataFrame containing the fetched data.
    """
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

    try:
        # Create credentials from the loaded JSON
        creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)

        # Fetch data from the specified range
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name
        ).execute()
        values = result.get('values', [])

        if not values:
            st.warning(f"No data found in the range: **{range_name}**.")
            return pd.DataFrame()
        else:
            headers = values[0]
            rows = values[1:]
            df = pd.DataFrame(rows, columns=headers)
            st.success(f"Data fetched successfully from **{range_name}**.")
            return df

    except Exception as e:
        st.error(f"An error occurred while fetching data from **{range_name}**: {e}")
        return pd.DataFrame()

def main():
    st.title("ISV Sankirtan Mission Control")

    # Countdown portion
    current_dir = os.path.dirname(__file__)
    countdown_file = os.path.join(current_dir, "countdown.html")
    if os.path.exists(countdown_file):
        with open(countdown_file, "r", encoding="utf-8") as f:
            countdown_html = f.read()
        components.html(countdown_html, height=120, scrolling=False)
    else:
        st.warning("Countdown file not found.")

    # Define ranges for Charts and Numbers sheets
    charts_range = 'Charts!A1:B10'    # Adjust as needed
    numbers_range = 'Numbers!A1:C10'  # Adjust as needed

    # Fetch data from both sheets
    st.header("Fetching Data from Google Sheets")
    df_charts = fetch_data_from_sheets(charts_range)
    df_numbers = fetch_data_from_sheets(numbers_range)

    # Initialize metrics dictionary
    metrics = {}

    # Process Numbers Data to Extract Metrics
    if not df_numbers.empty:
        # Ensure expected columns exist
        expected_numbers_columns = {"ISV Score", "ISV Goal", "Mayapur Score"}
        if not expected_numbers_columns.issubset(df_numbers.columns):
            st.error(f"'Numbers' sheet is missing one or more required columns: {expected_numbers_columns}")
        else:
            # Convert columns to numeric
            try:
                df_numbers["ISV Score"] = pd.to_numeric(df_numbers["ISV Score"], errors='coerce')
                df_numbers["ISV Goal"] = pd.to_numeric(df_numbers["ISV Goal"], errors='coerce')
                df_numbers["Mayapur Score"] = pd.to_numeric(df_numbers["Mayapur Score"], errors='coerce')
            except Exception as e:
                st.error(f"Error converting metrics to numeric: {e}")

            # Extract metrics from Numbers data
            # Assuming the first row contains the metrics
            isv_score = df_numbers["ISV Score"].iloc[0] if not df_numbers["ISV Score"].empty else 0
            isv_goal = df_numbers["ISV Goal"].iloc[0] if not df_numbers["ISV Goal"].empty else 0
            mayapur_score = df_numbers["Mayapur Score"].iloc[0] if not df_numbers["Mayapur Score"].empty else 0

            # Update metrics dictionary
            metrics["YTD ISV Total Book Points"] = isv_score
            metrics["ISV End of Year Goal"] = isv_goal
            metrics["YTD Mayapur Total Book Points"] = mayapur_score
    else:
        st.info("No data available in the 'Numbers' sheet.")

    # Update Placeholder Stats with Fetched Metrics
    ytd_isv_total = metrics.get("YTD ISV Total Book Points", 0)
    isv_goal = metrics.get("ISV End of Year Goal", 0)
    ytd_mayapur_total = metrics.get("YTD Mayapur Total Book Points", 0)
    percent_reached = (ytd_isv_total / isv_goal) * 100 if isv_goal else 0

    # Display the first three metrics side by side
    col1, col2, col3 = st.columns(3)

    # Column 1: YTD ISV + YTD Mayapur
    col1.metric("YTD ISV Total Book Points", f"{ytd_isv_total:,}")
    col1.metric("YTD Mayapur Total Book Points", f"{ytd_mayapur_total:,}")

    # Column 2: End of Year Goal
    col2.metric("ISV End of Year Goal", f"{isv_goal:,}")

    # Column 3: Percentage Reached
    col3.metric("Percentage Goal Reached", f"{percent_reached:.2f}%")

    # Display Charts Data
    st.subheader("Charts Data")
    if df_charts.empty:
        st.info("No data available in the 'Charts' sheet.")
    else:
        # Ensure expected columns exist
        expected_charts_columns = {"MetricName", "MetricValue"}
        if not expected_charts_columns.issubset(df_charts.columns):
            st.error(f"'Charts' sheet is missing one or more required columns: {expected_charts_columns}")
        else:
            # Convert MetricValue to numeric
            try:
                df_charts["MetricValue"] = pd.to_numeric(df_charts["MetricValue"], errors='coerce')
            except Exception as e:
                st.error(f"Error converting 'MetricValue' to numeric: {e}")

            st.write(df_charts)

            # Pie Chart for Charts Data
            st.subheader("Charts Pie Chart")
            fig_charts_pie, ax_charts_pie = plt.subplots()
            fig_charts_pie.patch.set_facecolor('#000000')
            ax_charts_pie.set_facecolor('#000000')
            wedges, texts, autotexts = ax_charts_pie.pie(
                df_charts["MetricValue"],
                labels=df_charts["MetricName"],
                autopct="%1.1f%%",
                textprops={'color': '#00ff00'}
            )
            for text in texts:
                text.set_color('#00ff00')
            for autotext in autotexts:
                autotext.set_color('#00ff00')
            plt.tight_layout()
            st.pyplot(fig_charts_pie)

            # Bar Chart for Charts Data
            st.subheader("Charts Bar Chart")
            fig_charts_bar, ax_charts_bar = plt.subplots()
            fig_charts_bar.patch.set_facecolor('#000000')
            ax_charts_bar.set_facecolor('#000000')
            ax_charts_bar.bar(df_charts["MetricName"], df_charts["MetricValue"], color='#00ff00')
            ax_charts_bar.spines["left"].set_color('#00ff00')
            ax_charts_bar.spines["right"].set_color('#00ff00')
            ax_charts_bar.spines["top"].set_color('#00ff00')
            ax_charts_bar.spines["bottom"].set_color('#00ff00')
            ax_charts_bar.tick_params(axis='x', colors='#00ff00')
            ax_charts_bar.tick_params(axis='y', colors='#00ff00')
            plt.tight_layout()
            st.pyplot(fig_charts_bar)

    # Display Numbers Data (Optional: If you want to display the Numbers sheet as a table)
    st.subheader("Numbers Data")
    if df_numbers.empty:
        st.info("No data available in the 'Numbers' sheet.")
    else:
        # Display the Numbers Data
        st.write(df_numbers)

        # Example Visualization for Numbers Data: Bar Chart
        st.subheader("Numbers Bar Chart")
        fig_numbers_bar, ax_numbers_bar = plt.subplots()
        fig_numbers_bar.patch.set_facecolor('#000000')
        ax_numbers_bar.set_facecolor('#000000')
        ax_numbers_bar.bar(
            ["YTD ISV Total Book Points", "ISV End of Year Goal", "YTD Mayapur Total Book Points"],
            [ytd_isv_total, isv_goal, ytd_mayapur_total],
            color='#00ff00'
        )
        ax_numbers_bar.spines["left"].set_color('#00ff00')
        ax_numbers_bar.spines["right"].set_color('#00ff00')
        ax_numbers_bar.spines["top"].set_color('#00ff00')
        ax_numbers_bar.spines["bottom"].set_color('#00ff00')
        ax_numbers_bar.tick_params(axis='x', colors='#00ff00')
        ax_numbers_bar.tick_params(axis='y', colors='#00ff00')
        plt.tight_layout()
        st.pyplot(fig_numbers_bar)

if __name__ == "__main__":
    main()
