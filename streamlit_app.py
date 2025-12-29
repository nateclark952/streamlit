import streamlit as st
import pandas as pd
from pathlib import Path
import glob

# Page configuration
st.set_page_config(
    page_title="Redbeam Data Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Redbeam Data Dashboard")

# Function to load the most recent CSV file
@st.cache_data
def load_latest_data():
    """Load the most recent CSV file from the output directory."""
    # Try multiple possible paths (local Windows path and Streamlit Cloud)
    possible_paths = [
        Path(r"C:\Users\natec\OneDrive\Desktop\redbeam scraper"),  # Local Windows
        Path.home() / "Desktop" / "redbeam scraper",  # Alternative local path
        Path(".") / "data",  # Streamlit Cloud relative path
        Path("."),  # Current directory
    ]
    
    output_dir = None
    for path in possible_paths:
        if path.exists() and path.is_dir():
            output_dir = path
            break
    
    # If no directory found, try current directory
    if output_dir is None:
        output_dir = Path(".")
    
    # Find all CSV files
    csv_files = list(output_dir.glob("*.csv"))
    
    if not csv_files:
        return None, None
    
    # Get the most recent file
    try:
        latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
        df = pd.read_csv(latest_file)
        return df, latest_file
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None, None

# Load data
df, file_path = load_latest_data()

if df is None or file_path is None:
    st.warning("No data files found. Please run the scraper first or upload a CSV file.")
    
    # Allow file upload as fallback
    uploaded_file = st.file_uploader("Upload a CSV file", type=['csv'])
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            file_path = Path(uploaded_file.name)
            st.success("File uploaded successfully!")
        except Exception as e:
            st.error(f"Error reading uploaded file: {e}")
            st.stop()
    else:
        st.stop()

file_display_name = file_path.name if isinstance(file_path, Path) else str(file_path)
st.success(f"Loaded data from: {file_display_name}")
st.info(f"Data shape: {df.shape[0]} rows × {df.shape[1]} columns")

# Display raw data
st.subheader("Raw Data")
st.dataframe(df, use_container_width=True)

# Data analysis section
st.subheader("Data Analysis")

# Check if we have the expected columns for status_by_building
# This is a common analysis - grouping by building and counting status
if 'Building' in df.columns or 'building' in df.columns:
    building_col = 'Building' if 'Building' in df.columns else 'building'
    
    # Check for status-related columns
    status_cols = [col for col in df.columns if 'status' in col.lower() or 'available' in col.lower() or 'checked' in col.lower()]
    
    if status_cols:
        status_col = status_cols[0]
        
        try:
            # Create status_by_building DataFrame
            status_by_building = df.groupby([building_col, status_col]).size().unstack(fill_value=0)
            
            # Fix the column assignment issue - check number of columns first
            if status_by_building.shape[1] == 2:
                # Only assign if we have exactly 2 columns
                status_by_building.columns = ['Available', 'Checked Out']
            elif status_by_building.shape[1] == 1:
                # If only one column, rename it appropriately
                col_name = status_by_building.columns[0]
                if 'available' in str(col_name).lower():
                    status_by_building.columns = ['Available']
                elif 'checked' in str(col_name).lower() or 'out' in str(col_name).lower():
                    status_by_building.columns = ['Checked Out']
                else:
                    # Keep original name or use a default
                    status_by_building.columns = [str(col_name)]
            else:
                # More than 2 columns - keep original names or handle differently
                st.warning(f"Found {status_by_building.shape[1]} status columns. Displaying all.")
            
            st.subheader("Status by Building")
            st.dataframe(status_by_building, use_container_width=True)
            
            # Create a bar chart
            st.bar_chart(status_by_building)
            
        except Exception as e:
            st.error(f"Error creating status by building analysis: {e}")
            st.write("Available columns:", df.columns.tolist())
    else:
        st.info("No status columns found in the data.")
        st.write("Available columns:", df.columns.tolist())
else:
    st.info("No 'Building' column found in the data.")
    st.write("Available columns:", df.columns.tolist())

# Summary statistics
st.subheader("Summary Statistics")
st.dataframe(df.describe(), use_container_width=True)

# Column information
with st.expander("Column Information"):
    col_info = pd.DataFrame({
        'Column': df.columns,
        'Data Type': df.dtypes,
        'Non-Null Count': df.count(),
        'Null Count': df.isnull().sum()
    })
    st.dataframe(col_info, use_container_width=True)

