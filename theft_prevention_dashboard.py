"""
Theft Prevention Dashboard Module
Provides comprehensive theft prevention analytics and visualizations for asset management data.
Can be imported into Streamlit applications.
"""

import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, Dict, List, Tuple


class TheftPreventionDashboard:
    """Main class for theft prevention analytics and visualizations."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the dashboard with asset data.
        
        Args:
            df: DataFrame containing asset/equipment data
        """
        self.df = df.copy()
        self._normalize_column_names()
        self._identify_columns()
    
    def _normalize_column_names(self):
        """Normalize column names to handle variations."""
        # Create a mapping of common column name variations
        column_mapping = {}
        for col in self.df.columns:
            col_lower = col.lower()
            # Status columns
            if 'status' in col_lower and 'status' not in column_mapping.values():
                column_mapping[col] = 'status'
            # Location/Building columns
            elif any(term in col_lower for term in ['building', 'location', 'site', 'facility']) and 'location' not in column_mapping.values():
                column_mapping[col] = 'location'
            # Check-out date columns
            elif any(term in col_lower for term in ['checkout', 'check-out', 'checked out', 'out date']) and 'checkout_date' not in column_mapping.values():
                column_mapping[col] = 'checkout_date'
            # Due date columns
            elif any(term in col_lower for term in ['due', 'return', 'expected return']) and 'due_date' not in column_mapping.values():
                column_mapping[col] = 'due_date'
            # User/Assignee columns
            elif any(term in col_lower for term in ['user', 'assignee', 'assigned to', 'checked out to']) and 'assigned_to' not in column_mapping.values():
                column_mapping[col] = 'assigned_to'
            # Asset name/ID columns
            elif any(term in col_lower for term in ['asset', 'equipment', 'item', 'tool']) and 'asset_name' not in column_mapping.values():
                column_mapping[col] = 'asset_name'
            # Category/Type columns
            elif any(term in col_lower for term in ['category', 'type', 'class']) and 'category' not in column_mapping.values():
                column_mapping[col] = 'category'
        
        # Rename columns
        self.df.rename(columns=column_mapping, inplace=True)
    
    def _identify_columns(self):
        """Identify and store column names for common fields."""
        self.status_col = self._find_column(['status', 'state', 'condition'])
        self.location_col = self._find_column(['location', 'building', 'site', 'facility'])
        self.checkout_col = self._find_column(['checkout_date', 'checkout', 'checked out'])
        self.due_col = self._find_column(['due_date', 'due', 'return date'])
        self.assigned_col = self._find_column(['assigned_to', 'user', 'assignee'])
        self.asset_col = self._find_column(['asset_name', 'asset', 'equipment', 'item'])
        self.category_col = self._find_column(['category', 'type', 'class'])
    
    def _find_column(self, possible_names: List[str]) -> Optional[str]:
        """Find a column by possible names."""
        for name in possible_names:
            if name in self.df.columns:
                return name
        return None
    
    def calculate_risk_metrics(self) -> Dict:
        """
        Calculate key risk metrics for theft prevention.
        
        Returns:
            Dictionary containing risk metrics
        """
        metrics = {}
        total_assets = len(self.df)
        metrics['total_assets'] = total_assets
        
        # Check for overdue items
        if self.due_col:
            try:
                # Convert to datetime if not already
                if self.df[self.due_col].dtype == 'object':
                    self.df[self.due_col] = pd.to_datetime(self.df[self.due_col], errors='coerce')
                
                today = datetime.now()
                overdue = self.df[self.df[self.due_col] < today]
                metrics['overdue_count'] = len(overdue)
                metrics['overdue_percentage'] = (len(overdue) / total_assets * 100) if total_assets > 0 else 0
            except:
                metrics['overdue_count'] = 0
                metrics['overdue_percentage'] = 0
        else:
            metrics['overdue_count'] = 0
            metrics['overdue_percentage'] = 0
        
        # Check for missing/lost items
        if self.status_col:
            status_lower = self.df[self.status_col].astype(str).str.lower()
            missing_keywords = ['missing', 'lost', 'stolen', 'unaccounted']
            missing = status_lower.str.contains('|'.join(missing_keywords), na=False)
            metrics['missing_count'] = missing.sum()
            metrics['missing_percentage'] = (missing.sum() / total_assets * 100) if total_assets > 0 else 0
        else:
            metrics['missing_count'] = 0
            metrics['missing_percentage'] = 0
        
        # Check for long-term checkouts (over 30 days)
        if self.checkout_col:
            try:
                if self.df[self.checkout_col].dtype == 'object':
                    self.df[self.checkout_col] = pd.to_datetime(self.df[self.checkout_col], errors='coerce')
                
                today = datetime.now()
                checkout_days = (today - self.df[self.checkout_col]).dt.days
                long_term = checkout_days > 30
                metrics['long_term_checkout_count'] = long_term.sum()
                metrics['long_term_checkout_percentage'] = (long_term.sum() / total_assets * 100) if total_assets > 0 else 0
            except:
                metrics['long_term_checkout_count'] = 0
                metrics['long_term_checkout_percentage'] = 0
        else:
            metrics['long_term_checkout_count'] = 0
            metrics['long_term_checkout_percentage'] = 0
        
        # Calculate risk score (0-100)
        risk_score = (
            metrics['overdue_percentage'] * 0.3 +
            metrics['missing_percentage'] * 0.5 +
            metrics['long_term_checkout_percentage'] * 0.2
        )
        metrics['risk_score'] = min(100, risk_score)
        
        return metrics
    
    def get_overdue_assets(self) -> pd.DataFrame:
        """Get list of overdue assets."""
        if not self.due_col:
            return pd.DataFrame()
        
        try:
            if self.df[self.due_col].dtype == 'object':
                self.df[self.due_col] = pd.to_datetime(self.df[self.due_col], errors='coerce')
            
            today = datetime.now()
            overdue = self.df[self.df[self.due_col] < today].copy()
            if len(overdue) > 0:
                overdue['days_overdue'] = (today - overdue[self.due_col]).dt.days
                return overdue.sort_values('days_overdue', ascending=False)
            return pd.DataFrame()
        except:
            return pd.DataFrame()
    
    def get_missing_assets(self) -> pd.DataFrame:
        """Get list of missing/lost/stolen assets."""
        if not self.status_col:
            return pd.DataFrame()
        
        status_lower = self.df[self.status_col].astype(str).str.lower()
        missing_keywords = ['missing', 'lost', 'stolen', 'unaccounted']
        missing = status_lower.str.contains('|'.join(missing_keywords), na=False)
        return self.df[missing].copy()
    
    def get_long_term_checkouts(self, days: int = 30) -> pd.DataFrame:
        """Get assets checked out for longer than specified days."""
        if not self.checkout_col:
            return pd.DataFrame()
        
        try:
            if self.df[self.checkout_col].dtype == 'object':
                self.df[self.checkout_col] = pd.to_datetime(self.df[self.checkout_col], errors='coerce')
            
            today = datetime.now()
            checkout_days = (today - self.df[self.checkout_col]).dt.days
            long_term = self.df[checkout_days > days].copy()
            if len(long_term) > 0:
                long_term['days_checked_out'] = checkout_days[checkout_days > days]
                return long_term.sort_values('days_checked_out', ascending=False)
            return pd.DataFrame()
        except:
            return pd.DataFrame()
    
    def render_metrics_cards(self):
        """Render key metrics as Streamlit metric cards."""
        metrics = self.calculate_risk_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Assets",
                f"{metrics['total_assets']:,}",
                help="Total number of assets in the system"
            )
        
        with col2:
            st.metric(
                "Overdue Items",
                f"{metrics['overdue_count']:,}",
                delta=f"{metrics['overdue_percentage']:.1f}%",
                delta_color="inverse",
                help="Items past their due date"
            )
        
        with col3:
            st.metric(
                "Missing/Lost",
                f"{metrics['missing_count']:,}",
                delta=f"{metrics['missing_percentage']:.1f}%",
                delta_color="inverse",
                help="Assets reported as missing, lost, or stolen"
            )
        
        with col4:
            risk_color = "normal" if metrics['risk_score'] < 30 else "off" if metrics['risk_score'] < 70 else "inverse"
            st.metric(
                "Risk Score",
                f"{metrics['risk_score']:.1f}",
                help="Overall theft risk score (0-100, lower is better)"
            )
    
    def render_status_distribution(self):
        """Render status distribution chart."""
        if not self.status_col:
            st.info("No status column found for status distribution analysis.")
            return
        
        status_counts = self.df[self.status_col].value_counts()
        
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Asset Status Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    
    def render_location_risk_heatmap(self):
        """Render risk heatmap by location."""
        if not self.location_col:
            st.info("No location column found for location risk analysis.")
            return
        
        # Calculate risk by location
        location_metrics = []
        for location in self.df[self.location_col].dropna().unique():
            location_df = self.df[self.df[self.location_col] == location]
            total = len(location_df)
            
            # Count missing
            missing = 0
            if self.status_col:
                status_lower = location_df[self.status_col].astype(str).str.lower()
                missing = status_lower.str.contains('missing|lost|stolen', na=False).sum()
            
            # Count overdue
            overdue = 0
            if self.due_col:
                try:
                    if location_df[self.due_col].dtype == 'object':
                        location_df[self.due_col] = pd.to_datetime(location_df[self.due_col], errors='coerce')
                    today = datetime.now()
                    overdue = len(location_df[location_df[self.due_col] < today])
                except:
                    pass
            
            risk_score = ((missing / total * 0.7) + (overdue / total * 0.3)) * 100 if total > 0 else 0
            location_metrics.append({
                'Location': location,
                'Total Assets': total,
                'Missing': missing,
                'Overdue': overdue,
                'Risk Score': risk_score
            })
        
        risk_df = pd.DataFrame(location_metrics)
        risk_df = risk_df.sort_values('Risk Score', ascending=False)
        
        fig = px.bar(
            risk_df,
            x='Location',
            y='Risk Score',
            color='Risk Score',
            color_continuous_scale='Reds',
            title="Theft Risk by Location",
            labels={'Risk Score': 'Risk Score (%)'}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display table
        st.dataframe(risk_df, use_container_width=True)
    
    def render_user_activity_analysis(self):
        """Render user activity and checkout analysis."""
        if not self.assigned_col:
            st.info("No assigned user column found for user activity analysis.")
            return
        
        user_stats = []
        for user in self.df[self.assigned_col].dropna().unique():
            user_df = self.df[self.df[self.assigned_col] == user]
            total = len(user_df)
            
            # Count overdue
            overdue = 0
            if self.due_col:
                try:
                    if user_df[self.due_col].dtype == 'object':
                        user_df[self.due_col] = pd.to_datetime(user_df[self.due_col], errors='coerce')
                    today = datetime.now()
                    overdue = len(user_df[user_df[self.due_col] < today])
                except:
                    pass
            
            # Average checkout duration
            avg_days = 0
            if self.checkout_col and self.due_col:
                try:
                    if user_df[self.checkout_col].dtype == 'object':
                        user_df[self.checkout_col] = pd.to_datetime(user_df[self.checkout_col], errors='coerce')
                    if user_df[self.due_col].dtype == 'object':
                        user_df[self.due_col] = pd.to_datetime(user_df[self.due_col], errors='coerce')
                    durations = (user_df[self.due_col] - user_df[self.checkout_col]).dt.days
                    avg_days = durations.mean() if not durations.isna().all() else 0
                except:
                    pass
            
            user_stats.append({
                'User': user,
                'Total Checked Out': total,
                'Overdue Items': overdue,
                'Overdue %': (overdue / total * 100) if total > 0 else 0,
                'Avg Checkout Days': round(avg_days, 1) if avg_days > 0 else 'N/A'
            })
        
        user_df = pd.DataFrame(user_stats)
        user_df = user_df.sort_values('Overdue Items', ascending=False)
        
        # Chart
        fig = px.bar(
            user_df.head(20),  # Top 20 users
            x='User',
            y='Overdue Items',
            color='Overdue %',
            color_continuous_scale='Reds',
            title="User Overdue Items (Top 20)",
            labels={'Overdue Items': 'Number of Overdue Items'}
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Table
        st.dataframe(user_df, use_container_width=True)
    
    def render_alerts_table(self):
        """Render alerts for high-risk items."""
        alerts = []
        
        # Overdue alerts
        overdue_df = self.get_overdue_assets()
        if len(overdue_df) > 0:
            for _, row in overdue_df.head(10).iterrows():
                asset_name = row.get(self.asset_col, 'Unknown') if self.asset_col else 'Unknown'
                days = row.get('days_overdue', 0)
                alerts.append({
                    'Type': 'Overdue',
                    'Severity': 'High' if days > 30 else 'Medium',
                    'Asset': asset_name,
                    'Days Overdue': days,
                    'Location': row.get(self.location_col, 'N/A') if self.location_col else 'N/A',
                    'Assigned To': row.get(self.assigned_col, 'N/A') if self.assigned_col else 'N/A'
                })
        
        # Missing alerts
        missing_df = self.get_missing_assets()
        if len(missing_df) > 0:
            for _, row in missing_df.iterrows():
                asset_name = row.get(self.asset_col, 'Unknown') if self.asset_col else 'Unknown'
                alerts.append({
                    'Type': 'Missing/Lost',
                    'Severity': 'Critical',
                    'Asset': asset_name,
                    'Days Overdue': 'N/A',
                    'Location': row.get(self.location_col, 'N/A') if self.location_col else 'N/A',
                    'Assigned To': row.get(self.assigned_col, 'N/A') if self.assigned_col else 'N/A'
                })
        
        # Long-term checkout alerts
        long_term_df = self.get_long_term_checkouts(30)
        if len(long_term_df) > 0:
            for _, row in long_term_df.head(10).iterrows():
                asset_name = row.get(self.asset_col, 'Unknown') if self.asset_col else 'Unknown'
                days = row.get('days_checked_out', 0)
                alerts.append({
                    'Type': 'Long-term Checkout',
                    'Severity': 'Medium' if days < 60 else 'High',
                    'Asset': asset_name,
                    'Days Overdue': days,
                    'Location': row.get(self.location_col, 'N/A') if self.location_col else 'N/A',
                    'Assigned To': row.get(self.assigned_col, 'N/A') if self.assigned_col else 'N/A'
                })
        
        if alerts:
            alerts_df = pd.DataFrame(alerts)
            # Sort by severity
            severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
            alerts_df['severity_order'] = alerts_df['Severity'].map(severity_order)
            alerts_df = alerts_df.sort_values('severity_order')
            alerts_df = alerts_df.drop('severity_order', axis=1)
            
            st.subheader("🚨 Active Alerts")
            st.dataframe(alerts_df, use_container_width=True)
        else:
            st.success("✅ No active alerts! All assets are accounted for.")
    
    def render_full_dashboard(self):
        """Render the complete theft prevention dashboard."""
        st.header("🛡️ Theft Prevention Dashboard")
        
        # Metrics cards
        self.render_metrics_cards()
        
        st.divider()
        
        # Alerts
        self.render_alerts_table()
        
        st.divider()
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            self.render_status_distribution()
        
        with col2:
            self.render_location_risk_heatmap()
        
        st.divider()
        
        # User activity
        self.render_user_activity_analysis()
        
        st.divider()
        
        # Detailed tables
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Overdue Assets")
            overdue_df = self.get_overdue_assets()
            if len(overdue_df) > 0:
                display_cols = []
                if self.asset_col:
                    display_cols.append(self.asset_col)
                if self.location_col:
                    display_cols.append(self.location_col)
                if self.assigned_col:
                    display_cols.append(self.assigned_col)
                if self.due_col:
                    display_cols.append(self.due_col)
                display_cols.append('days_overdue')
                
                st.dataframe(overdue_df[display_cols], use_container_width=True)
            else:
                st.success("No overdue assets!")
        
        with col2:
            st.subheader("Missing/Lost Assets")
            missing_df = self.get_missing_assets()
            if len(missing_df) > 0:
                display_cols = []
                if self.asset_col:
                    display_cols.append(self.asset_col)
                if self.location_col:
                    display_cols.append(self.location_col)
                if self.assigned_col:
                    display_cols.append(self.assigned_col)
                if self.status_col:
                    display_cols.append(self.status_col)
                
                st.dataframe(missing_df[display_cols], use_container_width=True)
            else:
                st.success("No missing assets!")


# Convenience function for easy import
def render_theft_prevention_dashboard(df: pd.DataFrame):
    """
    Convenience function to render the full theft prevention dashboard.
    
    Args:
        df: DataFrame containing asset/equipment data
    """
    dashboard = TheftPreventionDashboard(df)
    dashboard.render_full_dashboard()


def get_theft_prevention_metrics(df: pd.DataFrame) -> Dict:
    """
    Get theft prevention metrics without rendering.
    
    Args:
        df: DataFrame containing asset/equipment data
    
    Returns:
        Dictionary of risk metrics
    """
    dashboard = TheftPreventionDashboard(df)
    return dashboard.calculate_risk_metrics()

