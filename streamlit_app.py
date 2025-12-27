import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Page configuration
st.set_page_config(
    page_title="RFID Tool Tracking & Theft Prevention Dashboard",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-box {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(uploaded_file):
    """Load and preprocess the CSV data"""
    try:
        df = pd.read_csv(uploaded_file)
        
        # Convert date columns
        date_columns = ['Date Added', 'Last Updated', 'Check Out Date', 'Acquisition Date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce', format='%b %d, %Y %I:%M %p')
        
        # Clean and standardize data
        df['Building'] = df['Building'].fillna('Unknown')
        df['Room Name'] = df['Room Name'].fillna('Unknown')
        df['Checked Out To'] = df['Checked Out To'].fillna('Not Checked Out')
        df['Active'] = df['Active'].fillna('No')
        
        # Create derived columns
        df['Is Checked Out'] = df['Checked Out To'] != 'Not Checked Out'
        df['Days Since Last Update'] = (datetime.now() - df['Last Updated']).dt.days
        df['Days Since Checkout'] = (datetime.now() - df['Check Out Date']).dt.days
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def main():
    st.markdown('<h1 class="main-header">🔧 RFID Tool Tracking & Theft Prevention Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar for file upload and filters
    with st.sidebar:
        st.header("📁 Data Upload")
        uploaded_file = st.file_uploader(
            "Upload Asset CSV File",
            type=['csv'],
            help="Upload your asset tracking CSV file"
        )
        
        if uploaded_file is not None:
            df = load_data(uploaded_file)
            
            if df is not None:
                st.success(f"✅ Loaded {len(df)} assets")
                
                st.header("🔍 Filters")
                
                # Building filter
                buildings = ['All'] + sorted(df['Building'].unique().tolist())
                selected_building = st.selectbox("Select Building", buildings)
                
                # Active status filter
                active_filter = st.selectbox("Active Status", ['All', 'Active Only', 'Inactive Only'])
                
                # Check-out status filter
                checkout_filter = st.selectbox("Check-out Status", ['All', 'Checked Out', 'Available'])
                
                # Apply filters
                filtered_df = df.copy()
                
                if selected_building != 'All':
                    filtered_df = filtered_df[filtered_df['Building'] == selected_building]
                
                if active_filter == 'Active Only':
                    filtered_df = filtered_df[filtered_df['Active'] == 'Yes']
                elif active_filter == 'Inactive Only':
                    filtered_df = filtered_df[filtered_df['Active'] != 'Yes']
                
                if checkout_filter == 'Checked Out':
                    filtered_df = filtered_df[filtered_df['Is Checked Out'] == True]
                elif checkout_filter == 'Available':
                    filtered_df = filtered_df[filtered_df['Is Checked Out'] == False]
                
                st.info(f"📊 Showing {len(filtered_df)} assets")
        else:
            st.info("👆 Please upload a CSV file to get started")
            df = None
            filtered_df = None
    
    if df is not None and filtered_df is not None:
        # Key Metrics Row
        st.header("📈 Key Metrics")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_assets = len(filtered_df)
            st.metric("Total Assets", f"{total_assets:,}")
        
        with col2:
            checked_out = filtered_df['Is Checked Out'].sum()
            st.metric("Checked Out", f"{checked_out:,}", f"{checked_out/total_assets*100:.1f}%")
        
        with col3:
            available = total_assets - checked_out
            st.metric("Available", f"{available:,}", f"{available/total_assets*100:.1f}%")
        
        with col4:
            active_assets = (filtered_df['Active'] == 'Yes').sum()
            st.metric("Active Assets", f"{active_assets:,}")
        
        with col5:
            buildings_count = filtered_df['Building'].nunique()
            st.metric("Buildings", f"{buildings_count}")
        
        # Alert Section
        st.header("⚠️ Alerts & Warnings")
        alert_col1, alert_col2, alert_col3 = st.columns(3)
        
        with alert_col1:
            # Long-term checkouts
            long_checkouts = filtered_df[
                (filtered_df['Is Checked Out'] == True) & 
                (filtered_df['Days Since Checkout'] > 30)
            ]
            if len(long_checkouts) > 0:
                st.warning(f"🔴 {len(long_checkouts)} assets checked out >30 days")
        
        with alert_col2:
            # Stale updates
            stale_updates = filtered_df[filtered_df['Days Since Last Update'] > 90]
            if len(stale_updates) > 0:
                st.warning(f"🟡 {len(stale_updates)} assets not updated in 90+ days")
        
        with alert_col3:
            # Inactive but checked out
            inactive_checked = filtered_df[
                (filtered_df['Active'] != 'Yes') & 
                (filtered_df['Is Checked Out'] == True)
            ]
            if len(inactive_checked) > 0:
                st.error(f"🔴 {len(inactive_checked)} inactive assets checked out")
        
        # Main Dashboard Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📍 Location Overview", 
            "📦 Asset Status", 
            "👤 Check-out Analysis", 
            "📊 Analytics", 
            "🔍 Search & Details"
        ])
        
        with tab1:
            st.header("Asset Distribution by Location")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Building distribution
                building_counts = filtered_df['Building'].value_counts()
                fig_building = px.pie(
                    values=building_counts.values,
                    names=building_counts.index,
                    title="Assets by Building",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_building.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_building, use_container_width=True)
            
            with col2:
                # Room distribution (top 10)
                room_counts = filtered_df['Room Name'].value_counts().head(10)
                fig_room = px.bar(
                    x=room_counts.values,
                    y=room_counts.index,
                    orientation='h',
                    title="Top 10 Rooms by Asset Count",
                    labels={'x': 'Number of Assets', 'y': 'Room Name'},
                    color=room_counts.values,
                    color_continuous_scale='Blues'
                )
                fig_room.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_room, use_container_width=True)
            
            # Building-Room heatmap
            st.subheader("Building-Room Asset Distribution")
            building_room = filtered_df.groupby(['Building', 'Room Name']).size().reset_index(name='Count')
            building_room_pivot = building_room.pivot(index='Room Name', columns='Building', values='Count').fillna(0)
            
            if not building_room_pivot.empty:
                fig_heatmap = px.imshow(
                    building_room_pivot,
                    labels=dict(x="Building", y="Room", color="Asset Count"),
                    title="Asset Distribution Heatmap",
                    color_continuous_scale='YlOrRd',
                    aspect="auto"
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
        
        with tab2:
            st.header("Asset Status Overview")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Check-out status
                checkout_status = filtered_df['Is Checked Out'].value_counts()
                fig_checkout = px.pie(
                    values=checkout_status.values,
                    names=['Available', 'Checked Out'],
                    title="Check-out Status Distribution",
                    color_discrete_map={True: '#ff6b6b', False: '#51cf66'}
                )
                st.plotly_chart(fig_checkout, use_container_width=True)
            
            with col2:
                # Active status
                active_status = filtered_df['Active'].value_counts()
                fig_active = px.bar(
                    x=active_status.index,
                    y=active_status.values,
                    title="Active vs Inactive Assets",
                    labels={'x': 'Status', 'y': 'Count'},
                    color=active_status.values,
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig_active, use_container_width=True)
            
            # Status by Building
            st.subheader("Status by Building")
            status_by_building = pd.crosstab(
                filtered_df['Building'], 
                filtered_df['Is Checked Out']
            )
            fig_status = px.bar(
                status_by_building,
                title="Check-out Status by Building",
                labels={'value': 'Number of Assets', 'index': 'Building'},
                barmode='group',
                color_discrete_map={True: '#ff6b6b', False: '#51cf66'}
            )
            fig_status.update_layout(xaxis_title="Building", yaxis_title="Number of Assets")
            st.plotly_chart(fig_status, use_container_width=True)
        
        with tab3:
            st.header("Check-out Analysis")
            
            # Currently checked out assets
            checked_out_df = filtered_df[filtered_df['Is Checked Out'] == True].copy()
            
            if len(checked_out_df) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Check-out duration distribution
                    checkout_durations = checked_out_df['Days Since Checkout'].dropna()
                    if len(checkout_durations) > 0:
                        fig_duration = px.histogram(
                            checkout_durations,
                            nbins=30,
                            title="Check-out Duration Distribution (Days)",
                            labels={'value': 'Days Since Checkout', 'count': 'Number of Assets'},
                            color_discrete_sequence=['#ff6b6b']
                        )
                        st.plotly_chart(fig_duration, use_container_width=True)
                
                with col2:
                    # Checked out by building
                    checkout_by_building = checked_out_df['Building'].value_counts()
                    fig_checkout_building = px.bar(
                        x=checkout_by_building.index,
                        y=checkout_by_building.values,
                        title="Checked Out Assets by Building",
                        labels={'x': 'Building', 'y': 'Count'},
                        color=checkout_by_building.values,
                        color_continuous_scale='Reds'
                    )
                    st.plotly_chart(fig_checkout_building, use_container_width=True)
                
                # Long-term checkouts table
                st.subheader("🔴 Long-term Checkouts (>30 days)")
                long_term = checked_out_df[checked_out_df['Days Since Checkout'] > 30].sort_values(
                    'Days Since Checkout', ascending=False
                )
                
                if len(long_term) > 0:
                    display_cols = ['Asset ID', 'Building', 'Room Name', 'Checked Out To', 
                                  'Check Out Date', 'Days Since Checkout']
                    available_cols = [col for col in display_cols if col in long_term.columns]
                    st.dataframe(
                        long_term[available_cols].head(20),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.success("✅ No long-term checkouts found!")
                
                # All checked out assets table
                st.subheader("All Checked Out Assets")
                display_cols_all = ['Asset ID', 'Building', 'Room Name', 'Checked Out To', 
                                  'Check Out Date', 'Days Since Checkout', 'RFID Tag ID (hex)']
                available_cols_all = [col for col in display_cols_all if col in checked_out_df.columns]
                st.dataframe(
                    checked_out_df[available_cols_all].sort_values('Days Since Checkout', ascending=False),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.success("✅ No assets currently checked out!")
        
        with tab4:
            st.header("Analytics & Trends")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Assets added over time
                if 'Date Added' in filtered_df.columns:
                    filtered_df['Date Added'] = pd.to_datetime(filtered_df['Date Added'], errors='coerce')
                    assets_by_date = filtered_df.groupby(
                        filtered_df['Date Added'].dt.date
                    ).size().reset_index(name='Count')
                    assets_by_date = assets_by_date.sort_values('Date Added')
                    
                    fig_timeline = px.line(
                        assets_by_date,
                        x='Date Added',
                        y='Count',
                        title="Assets Added Over Time",
                        labels={'Date Added': 'Date', 'Count': 'Number of Assets Added'}
                    )
                    fig_timeline.update_traces(mode='lines+markers', fill='tozeroy')
                    st.plotly_chart(fig_timeline, use_container_width=True)
            
            with col2:
                # Last updated distribution
                if 'Days Since Last Update' in filtered_df.columns:
                    update_bins = [0, 7, 30, 90, 180, 365, float('inf')]
                    update_labels = ['<7 days', '7-30 days', '30-90 days', '90-180 days', '180-365 days', '>365 days']
                    filtered_df['Update Category'] = pd.cut(
                        filtered_df['Days Since Last Update'],
                        bins=update_bins,
                        labels=update_labels
                    )
                    update_dist = filtered_df['Update Category'].value_counts().sort_index()
                    
                    fig_update = px.bar(
                        x=update_dist.index,
                        y=update_dist.values,
                        title="Assets by Last Update Time",
                        labels={'x': 'Time Since Update', 'y': 'Number of Assets'},
                        color=update_dist.values,
                        color_continuous_scale='RdYlGn_r'
                    )
                    st.plotly_chart(fig_update, use_container_width=True)
            
            # Summary statistics
            st.subheader("Summary Statistics")
            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            
            with stat_col1:
                avg_checkout = checked_out_df['Days Since Checkout'].mean() if len(checked_out_df) > 0 else 0
                st.metric("Avg Checkout Days", f"{avg_checkout:.1f}")
            
            with stat_col2:
                max_checkout = checked_out_df['Days Since Checkout'].max() if len(checked_out_df) > 0 else 0
                st.metric("Max Checkout Days", f"{max_checkout:.0f}")
            
            with stat_col3:
                avg_update = filtered_df['Days Since Last Update'].mean()
                st.metric("Avg Days Since Update", f"{avg_update:.1f}")
            
            with stat_col4:
                unique_rfids = filtered_df['RFID Tag ID (hex)'].notna().sum()
                st.metric("Assets with RFID Tags", f"{unique_rfids:,}")
        
        with tab5:
            st.header("Search & Asset Details")
            
            # Search functionality
            search_col1, search_col2 = st.columns([3, 1])
            
            with search_col1:
                search_term = st.text_input("🔍 Search Assets", placeholder="Search by Asset ID, RFID Tag, Building, Room, or Person...")
            
            with search_col2:
                search_limit = st.number_input("Results Limit", min_value=10, max_value=1000, value=50, step=10)
            
            if search_term:
                search_mask = (
                    filtered_df['Asset ID'].astype(str).str.contains(search_term, case=False, na=False) |
                    filtered_df['RFID Tag ID (hex)'].astype(str).str.contains(search_term, case=False, na=False) |
                    filtered_df['Building'].astype(str).str.contains(search_term, case=False, na=False) |
                    filtered_df['Room Name'].astype(str).str.contains(search_term, case=False, na=False) |
                    filtered_df['Checked Out To'].astype(str).str.contains(search_term, case=False, na=False)
                )
                search_results = filtered_df[search_mask].head(search_limit)
                
                st.write(f"Found {len(search_results)} matching assets")
                
                if len(search_results) > 0:
                    # Display key columns
                    display_cols = [
                        'Asset ID', 'Building', 'Room Name', 'RFID Tag ID (hex)',
                        'Checked Out To', 'Check Out Date', 'Active', 'Last Updated'
                    ]
                    available_display_cols = [col for col in display_cols if col in search_results.columns]
                    st.dataframe(
                        search_results[available_display_cols],
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                st.info("Enter a search term to find specific assets")
            
            # Export functionality
            st.subheader("📥 Export Data")
            export_col1, export_col2, export_col3 = st.columns(3)
            
            with export_col1:
                if st.button("Export Filtered Data to CSV"):
                    csv = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"filtered_assets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            with export_col2:
                if st.button("Export Checked Out Assets"):
                    csv = checked_out_df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"checked_out_assets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            
            with export_col3:
                if st.button("Export All Data"):
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"all_assets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
    
    else:
        # Welcome screen
        st.info("""
        👋 **Welcome to the RFID Tool Tracking & Theft Prevention Dashboard!**
        
        **To get started:**
        1. Upload your asset tracking CSV file using the sidebar
        2. Explore the dashboard tabs to analyze your data
        3. Use filters to focus on specific buildings or asset statuses
        
        **Features:**
        - 📍 Location-based asset tracking
        - ⚠️ Alert system for long-term checkouts and stale data
        - 📊 Comprehensive analytics and visualizations
        - 🔍 Advanced search functionality
        - 📥 Data export capabilities
        """)

if __name__ == "__main__":
    main()

