"""
Example usage of the Theft Prevention Dashboard module in Streamlit.
This shows how to import and use the dashboard in your Streamlit app.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from theft_prevention_dashboard import TheftPreventionDashboard, render_theft_prevention_dashboard

# Page configuration
st.set_page_config(
    page_title="Theft Prevention Dashboard",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Theft Prevention Dashboard")

# Load your data (example - adjust to your data loading method)
@st.cache_data
def load_data():
    """Load your asset data."""
    # Example: Load from CSV
    # df = pd.read_csv("your_data.csv")
    
    # For this example, we'll create sample data
    # Replace this with your actual data loading logic
    sample_data = {
        'Asset Name': ['Laptop-001', 'Tablet-002', 'Tool-003', 'Camera-004', 'Laptop-005'],
        'Status': ['Checked Out', 'Available', 'Missing', 'Checked Out', 'Available'],
        'Location': ['Building A', 'Building B', 'Building A', 'Building C', 'Building B'],
        'Checkout Date': ['2024-01-15', None, None, '2024-12-01', None],
        'Due Date': ['2024-01-30', None, None, '2024-12-15', None],
        'Assigned To': ['John Doe', None, None, 'Jane Smith', None],
        'Category': ['Electronics', 'Electronics', 'Tools', 'Electronics', 'Electronics']
    }
    return pd.DataFrame(sample_data)

# Load data
df = load_data()

if df is not None and len(df) > 0:
    # Option 1: Use the convenience function (renders everything)
    render_theft_prevention_dashboard(df)
    
    # Option 2: Use the class for more control
    # dashboard = TheftPreventionDashboard(df)
    # dashboard.render_full_dashboard()
    
    # Option 3: Render specific components
    # dashboard = TheftPreventionDashboard(df)
    # dashboard.render_metrics_cards()
    # dashboard.render_alerts_table()
    # dashboard.render_status_distribution()
else:
    st.warning("No data available. Please load asset data first.")

