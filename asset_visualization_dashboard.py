"""
Asset Visualization Dashboard Module
Provides comprehensive visualizations and analytics for asset management data.
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np


class AssetVisualizationDashboard:
    """Main class for asset visualization and analytics."""
    
    def __init__(self, df: pd.DataFrame):
        """Initialize the dashboard with asset data."""
        self.df = df.copy()
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare and clean data for visualization."""
        # Convert date columns - try multiple formats
        date_columns = ['Acquisition Date', 'Date Added', 'Last Updated', 
                       'Warranty Start Date', 'Warranty End Date',
                       'Lease Start Date', 'Lease End Date', 'Check Out Date', 'DueDate']
        
        for col in date_columns:
            if col in self.df.columns:
                # Try multiple date formats
                self.df[col] = pd.to_datetime(self.df[col], errors='coerce', infer_datetime_format=True)
        
        # Convert numeric columns
        numeric_columns = ['Cost', 'Recovery Period in Years', 'Scrap Value', 
                          'Depreciated Value', 'Amount Depreciated']
        
        for col in numeric_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
    
    def render_overview_metrics(self):
        """Render key overview metrics."""
        col1, col2, col3, col4 = st.columns(4)
        
        total_assets = len(self.df)
        
        with col1:
            st.metric("Total Assets", f"{total_assets:,}")
        
        with col2:
            if 'Building' in self.df.columns:
                unique_buildings = self.df['Building'].nunique()
                st.metric("Buildings", f"{unique_buildings}")
            else:
                st.metric("Buildings", "N/A")
        
        with col3:
            if 'Status' in self.df.columns:
                active_count = self.df['Status'].notna().sum()
                st.metric("With Status", f"{active_count:,}")
            else:
                st.metric("With Status", "N/A")
        
        with col4:
            if 'Cost' in self.df.columns:
                total_cost = self.df['Cost'].sum()
                if pd.notna(total_cost):
                    st.metric("Total Cost", f"${total_cost:,.2f}")
                else:
                    st.metric("Total Cost", "N/A")
            else:
                st.metric("Total Cost", "N/A")
    
    def render_building_distribution(self):
        """Render asset distribution by building."""
        if 'Building' not in self.df.columns:
            st.info("No 'Building' column found.")
            return
        
        building_counts = self.df['Building'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Bar chart
            fig = px.bar(
                x=building_counts.index,
                y=building_counts.values,
                title="Assets by Building",
                labels={'x': 'Building', 'y': 'Number of Assets'},
                color=building_counts.values,
                color_continuous_scale='Blues'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Pie chart
            fig = px.pie(
                values=building_counts.values,
                names=building_counts.index,
                title="Asset Distribution by Building"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render_room_analysis(self):
        """Render room-level analysis."""
        if 'Room Name' not in self.df.columns and 'Room' not in self.df.columns:
            st.info("No room information found.")
            return
        
        room_col = 'Room Name' if 'Room Name' in self.df.columns else 'Room'
        room_counts = self.df[room_col].value_counts().head(20)
        
        fig = px.bar(
            x=room_counts.values,
            y=room_counts.index,
            orientation='h',
            title="Top 20 Rooms by Asset Count",
            labels={'x': 'Number of Assets', 'y': 'Room'},
            color=room_counts.values,
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def render_status_analysis(self):
        """Render status distribution analysis."""
        if 'Status' not in self.df.columns:
            st.info("No 'Status' column found.")
            return
        
        status_counts = self.df['Status'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Asset Status Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                x=status_counts.index,
                y=status_counts.values,
                title="Asset Status Counts",
                labels={'x': 'Status', 'y': 'Count'},
                color=status_counts.values,
                color_continuous_scale='Set3'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    
    def render_condition_analysis(self):
        """Render condition distribution."""
        if 'Condition' not in self.df.columns:
            st.info("No 'Condition' column found.")
            return
        
        condition_counts = self.df['Condition'].value_counts()
        
        fig = px.bar(
            x=condition_counts.index,
            y=condition_counts.values,
            title="Assets by Condition",
            labels={'x': 'Condition', 'y': 'Count'},
            color=condition_counts.values,
            color_continuous_scale='RdYlGn'
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    def render_timeline_analysis(self):
        """Render timeline analysis for acquisition and updates."""
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Acquisition Date' in self.df.columns:
                acquisition_dates = self.df['Acquisition Date'].dropna()
                if len(acquisition_dates) > 0:
                    acquisition_dates = pd.to_datetime(acquisition_dates)
                    monthly_counts = acquisition_dates.dt.to_period('M').value_counts().sort_index()
                    
                    fig = px.line(
                        x=monthly_counts.index.astype(str),
                        y=monthly_counts.values,
                        title="Assets Acquired Over Time (Monthly)",
                        labels={'x': 'Month', 'y': 'Number of Assets'}
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No acquisition date data available.")
        
        with col2:
            if 'Last Updated' in self.df.columns:
                update_dates = self.df['Last Updated'].dropna()
                if len(update_dates) > 0:
                    update_dates = pd.to_datetime(update_dates)
                    monthly_updates = update_dates.dt.to_period('M').value_counts().sort_index()
                    
                    fig = px.line(
                        x=monthly_updates.index.astype(str),
                        y=monthly_updates.values,
                        title="Assets Updated Over Time (Monthly)",
                        labels={'x': 'Month', 'y': 'Number of Updates'},
                        color_discrete_sequence=['green']
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No update date data available.")
    
    def render_financial_analysis(self):
        """Render financial analysis charts."""
        if 'Cost' not in self.df.columns:
            st.info("No financial data (Cost) available.")
            return
        
        financial_df = self.df[self.df['Cost'].notna()].copy()
        
        if len(financial_df) == 0:
            st.info("No cost data available for analysis.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Cost distribution
            fig = px.histogram(
                financial_df,
                x='Cost',
                nbins=50,
                title="Cost Distribution",
                labels={'Cost': 'Cost ($)', 'count': 'Number of Assets'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Cost by building
            if 'Building' in financial_df.columns:
                cost_by_building = financial_df.groupby('Building')['Cost'].sum().sort_values(ascending=False)
                fig = px.bar(
                    x=cost_by_building.index,
                    y=cost_by_building.values,
                    title="Total Cost by Building",
                    labels={'x': 'Building', 'y': 'Total Cost ($)'},
                    color=cost_by_building.values,
                    color_continuous_scale='Greens'
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
        
        # Depreciation analysis
        if 'Depreciated Value' in financial_df.columns and 'Amount Depreciated' in financial_df.columns:
            st.subheader("Depreciation Analysis")
            dep_df = financial_df[
                (financial_df['Depreciated Value'].notna()) & 
                (financial_df['Amount Depreciated'].notna())
            ].copy()
            
            if len(dep_df) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.scatter(
                        dep_df,
                        x='Cost',
                        y='Depreciated Value',
                        size='Amount Depreciated',
                        title="Cost vs Depreciated Value",
                        labels={'Cost': 'Original Cost ($)', 'Depreciated Value': 'Depreciated Value ($)'},
                        hover_data=['Building'] if 'Building' in dep_df.columns else None
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    total_depreciation = dep_df['Amount Depreciated'].sum()
                    total_cost = dep_df['Cost'].sum()
                    total_dep_value = dep_df['Depreciated Value'].sum()
                    
                    fig = go.Figure(data=[
                        go.Bar(name='Original Cost', x=['Total'], y=[total_cost], marker_color='blue'),
                        go.Bar(name='Depreciated Value', x=['Total'], y=[total_dep_value], marker_color='green'),
                        go.Bar(name='Amount Depreciated', x=['Total'], y=[total_depreciation], marker_color='red')
                    ])
                    fig.update_layout(
                        title="Total Financial Summary",
                        yaxis_title="Amount ($)",
                        barmode='group'
                    )
                    st.plotly_chart(fig, use_container_width=True)
    
    def render_building_room_heatmap(self):
        """Render heatmap of assets by building and room."""
        if 'Building' not in self.df.columns:
            st.info("No 'Building' column found.")
            return
        
        room_col = 'Room Name' if 'Room Name' in self.df.columns else 'Room'
        if room_col not in self.df.columns:
            st.info("No room information found.")
            return
        
        # Create pivot table
        heatmap_data = self.df.groupby(['Building', room_col]).size().reset_index(name='Count')
        pivot_data = heatmap_data.pivot(index='Building', columns=room_col, values='Count').fillna(0)
        
        # Limit to top rooms for readability
        top_rooms = heatmap_data.groupby(room_col)['Count'].sum().nlargest(15).index
        pivot_data = pivot_data[top_rooms]
        
        fig = px.imshow(
            pivot_data,
            labels=dict(x="Room", y="Building", color="Asset Count"),
            title="Asset Distribution: Building × Room Heatmap",
            color_continuous_scale='YlOrRd',
            aspect="auto"
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    def render_active_status(self):
        """Render active vs inactive assets."""
        if 'Active' not in self.df.columns:
            st.info("No 'Active' column found.")
            return
        
        active_counts = self.df['Active'].value_counts()
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(
                values=active_counts.values,
                names=active_counts.index,
                title="Active vs Inactive Assets"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if 'Building' in self.df.columns:
                active_by_building = self.df.groupby(['Building', 'Active']).size().unstack(fill_value=0)
                fig = px.bar(
                    active_by_building,
                    title="Active/Inactive by Building",
                    labels={'value': 'Count', 'index': 'Building'},
                    barmode='group'
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
    
    def render_manufacturer_analysis(self):
        """Render manufacturer distribution."""
        if 'Manufacturer' not in self.df.columns:
            st.info("No 'Manufacturer' column found.")
            return
        
        manufacturer_counts = self.df['Manufacturer'].dropna().value_counts().head(15)
        
        if len(manufacturer_counts) > 0:
            fig = px.bar(
                x=manufacturer_counts.values,
                y=manufacturer_counts.index,
                orientation='h',
                title="Top 15 Manufacturers",
                labels={'x': 'Number of Assets', 'y': 'Manufacturer'},
                color=manufacturer_counts.values,
                color_continuous_scale='Purples'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def render_asset_type_analysis(self):
        """Render asset type distribution."""
        if 'Asset Type' not in self.df.columns:
            st.info("No 'Asset Type' column found.")
            return
        
        asset_type_counts = self.df['Asset Type'].dropna().value_counts()
        
        if len(asset_type_counts) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    values=asset_type_counts.values,
                    names=asset_type_counts.index,
                    title="Asset Type Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(
                    x=asset_type_counts.index,
                    y=asset_type_counts.values,
                    title="Asset Type Counts",
                    labels={'x': 'Asset Type', 'y': 'Count'},
                    color=asset_type_counts.values,
                    color_continuous_scale='Set2'
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
    
    def render_full_dashboard(self):
        """Render the complete visualization dashboard."""
        st.header("📊 Asset Visualization Dashboard")
        
        # Overview metrics
        self.render_overview_metrics()
        st.divider()
        
        # Building and Room Analysis
        st.subheader("📍 Location Analysis")
        self.render_building_distribution()
        st.divider()
        
        self.render_room_analysis()
        st.divider()
        
        self.render_building_room_heatmap()
        st.divider()
        
        # Status and Condition
        st.subheader("📋 Status & Condition Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            self.render_status_analysis()
        
        with col2:
            self.render_condition_analysis()
        
        st.divider()
        
        # Active Status
        self.render_active_status()
        st.divider()
        
        # Timeline Analysis
        st.subheader("📅 Timeline Analysis")
        self.render_timeline_analysis()
        st.divider()
        
        # Financial Analysis
        st.subheader("💰 Financial Analysis")
        self.render_financial_analysis()
        st.divider()
        
        # Asset Type and Manufacturer
        st.subheader("🏷️ Asset Classification")
        self.render_asset_type_analysis()
        st.divider()
        
        self.render_manufacturer_analysis()


def render_asset_visualization_dashboard(df: pd.DataFrame):
    """Convenience function to render the full visualization dashboard."""
    dashboard = AssetVisualizationDashboard(df)
    dashboard.render_full_dashboard()

