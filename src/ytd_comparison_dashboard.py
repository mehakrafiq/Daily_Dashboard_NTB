import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')
from datetime import datetime, date
import os
import gc
from io import BytesIO
import xlsxwriter
import base64

# Page configuration
st.set_page_config(
    page_title="iNET YTD Analytics Dashboard",
    page_icon="📱",
    layout="wide"
)

# Title and description
st.title("📱 iNET Mobile Banking Year-to-Date Analytics")
st.markdown("**Complete Dataset Analysis with YTD Comparisons**")

# Initialize session state for data persistence
if 'full_data' not in st.session_state:
    st.session_state.full_data = None
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None

# File loading section
st.sidebar.header("📁 Data Loading")

# For your specific file
default_path = r"C:\Users\mehak.rafiq.ASKARIBANK\Documents\Projects\model_data\Daily_Dashboard_NTB\Data\Customer-Level-Account Holder Detail Report -2603_Report2 (6).csv"

file_path = st.sidebar.text_input(
    "File path:",
    value=default_path if os.path.exists(default_path) else "",
    help="Enter the full path to your CSV file"
)

# Load data button
if st.sidebar.button("Load Complete Dataset", type="primary"):
    if os.path.exists(file_path):
        with st.spinner("Loading complete dataset... This may take a few minutes for large files"):
            try:
                # Load data efficiently
                @st.cache_data(persist=True)
                def load_complete_data(path):
                    # Read in chunks for memory efficiency
                    chunks = []
                    chunk_size = 100000
                    
                    total_rows = sum(1 for line in open(path, 'r', encoding='utf-8')) - 1
                    progress_bar = st.progress(0)
                    rows_processed = 0
                    
                    for chunk in pd.read_csv(path, chunksize=chunk_size):
                        chunks.append(chunk)
                        rows_processed += len(chunk)
                        progress = min(rows_processed / total_rows, 1.0)
                        progress_bar.progress(progress, f"Loading: {rows_processed:,} / {total_rows:,} rows")
                    
                    progress_bar.empty()
                    df = pd.concat(chunks, ignore_index=True)
                    return df, total_rows
                
                st.session_state.full_data, total_rows = load_complete_data(file_path)
                st.success(f"✅ Successfully loaded {total_rows:,} rows!")
                
                # Clear processed data to force reprocessing
                st.session_state.processed_data = None
                
            except Exception as e:
                st.error(f"Error loading file: {str(e)}")
    else:
        st.error("File not found. Please check the path.")

# Process data if loaded
if st.session_state.full_data is not None and st.session_state.processed_data is None:
    with st.spinner("Processing data for YTD analysis..."):
        @st.cache_data(persist=True)
        def process_for_ytd(df):
            df_processed = df.copy()
            
            # Convert date columns
            date_columns = ['CIF_CREATION_DATE', 'CUSTOMER_RELATIONSHIP_DATE', 'AC_OPEN_DATE', 
                           'MOBILE_APP_REGISTRATION_DATE', 'LAST_TRX_DATE']
            
            for col in date_columns:
                if col in df_processed.columns:
                    df_processed[col] = pd.to_datetime(df_processed[col], errors='coerce')
            
            # Add date components
            df_processed['AC_OPEN_YEAR'] = df_processed['AC_OPEN_DATE'].dt.year
            df_processed['AC_OPEN_MONTH'] = df_processed['AC_OPEN_DATE'].dt.month
            df_processed['AC_OPEN_DAY'] = df_processed['AC_OPEN_DATE'].dt.day
            df_processed['AC_OPEN_DOY'] = df_processed['AC_OPEN_DATE'].dt.dayofyear  # Day of year
            
            # Registration status
            def get_registration_status(row):
                if pd.isna(row['MOBILE_APP_REGISTRATION_DATE']):
                    return 'Not Registered'
                elif row['MOBILE_APP_REGISTRATION_DATE'] < row['AC_OPEN_DATE']:
                    return 'Already Registered'
                else:
                    return 'Registered'
            
            df_processed['iNET_Registration_status'] = df_processed.apply(get_registration_status, axis=1)
            
            # Days to onboard
            df_processed['days_to_onboard'] = (
                df_processed['MOBILE_APP_REGISTRATION_DATE'] - df_processed['AC_OPEN_DATE']
            ).dt.days
            
            # Activity status
            current_date = pd.Timestamp.now()
            df_processed['days_since_last_trx'] = (current_date - df_processed['LAST_TRX_DATE']).dt.days
            
            # Activity categories
            conditions = [
                (df_processed['days_since_last_trx'] <= 7),
                (df_processed['days_since_last_trx'] <= 30),
                (df_processed['days_since_last_trx'] <= 90),
                (df_processed['days_since_last_trx'] > 90)
            ]
            
            choices = ['Weekly Active', 'Monthly Active', 'Quarterly Active', 'Inactive']
            
            df_processed['Activity_Status'] = np.select(conditions, choices, default='Unknown')
            
            return df_processed
        
        st.session_state.processed_data = process_for_ytd(st.session_state.full_data)

# Main dashboard
if st.session_state.processed_data is not None:
    df = st.session_state.processed_data
    
    # Current date reference
    current_date = datetime.now()
    current_year = current_date.year
    current_doy = current_date.timetuple().tm_yday  # Day of year
    
    # Sidebar filters
    st.sidebar.header("🔍 Analysis Settings")
    
    # YTD Comparison Settings
    st.sidebar.subheader("Year-to-Date Settings")
    
    # Select years to compare
    available_years = sorted(df['AC_OPEN_YEAR'].dropna().unique())
    selected_years = st.sidebar.multiselect(
        "Select years to compare:",
        available_years,
        default=available_years[-3:] if len(available_years) >= 3 else available_years
    )
    
    # Reference date for YTD
    reference_date = st.sidebar.date_input(
        "YTD up to date:",
        value=current_date.date(),
        max_value=current_date.date()
    )
    reference_doy = reference_date.timetuple().tm_yday
    
    # Region filter
    regions = ['All'] + sorted(df['REGION_DESC'].dropna().unique().tolist())
    selected_region = st.sidebar.selectbox("Region:", regions)
    
    # Apply YTD filter
    ytd_data = {}
    for year in selected_years:
        year_data = df[
            (df['AC_OPEN_YEAR'] == year) & 
            (df['AC_OPEN_DOY'] <= reference_doy)
        ]
        if selected_region != 'All':
            year_data = year_data[year_data['REGION_DESC'] == selected_region]
        ytd_data[year] = year_data
    
    # Header metrics
    st.header(f"📊 Year-to-Date Performance (Jan 1 - {reference_date.strftime('%b %d')})")
    
    # YTD Comparison Metrics
    metric_cols = st.columns(len(selected_years))
    
    for i, year in enumerate(sorted(selected_years, reverse=True)):
        with metric_cols[i]:
            year_total = len(ytd_data[year])
            year_registered = len(ytd_data[year][ytd_data[year]['iNET_Registration_status'] == 'Registered'])
            year_eligible = len(ytd_data[year][ytd_data[year]['INET_ELIGIBLE'] == 'Y'])
            
            # Calculate growth
            if i < len(selected_years) - 1:
                prev_year = sorted(selected_years, reverse=True)[i + 1]
                prev_total = len(ytd_data[prev_year])
                growth = ((year_total - prev_total) / prev_total * 100) if prev_total > 0 else 0
                delta = f"{growth:+.1f}% vs {prev_year}"
            else:
                delta = None
            
            st.metric(f"{year} YTD", f"{year_total:,}", delta)
            
            # Sub-metrics
            col1, col2 = st.columns(2)
            with col1:
                reg_rate = (year_registered / year_eligible * 100) if year_eligible > 0 else 0
                st.metric("Registered", f"{year_registered:,}", f"{reg_rate:.1f}%", delta_color="off")
            with col2:
                st.metric("Eligible", f"{year_eligible:,}", delta_color="off")
    
    # Tabs for different analyses
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 YTD Trends", "📊 Monthly Comparison", "🌍 Regional Analysis", 
        "🔄 Conversion Funnel", "📥 Export Data"
    ])
    
    with tab1:
        st.subheader("Year-to-Date Cumulative Trends")
        
        # Cumulative customer acquisition
        fig_cumulative = go.Figure()
        
        for year in selected_years:
            year_df = df[df['AC_OPEN_YEAR'] == year].copy()
            if selected_region != 'All':
                year_df = year_df[year_df['REGION_DESC'] == selected_region]
            
            # Calculate daily cumulative counts
            daily_counts = year_df.groupby('AC_OPEN_DOY').size().reset_index(name='count')
            daily_counts['cumulative'] = daily_counts['count'].cumsum()
            
            # Filter to reference DOY
            daily_counts = daily_counts[daily_counts['AC_OPEN_DOY'] <= reference_doy]
            
            fig_cumulative.add_trace(go.Scatter(
                x=daily_counts['AC_OPEN_DOY'],
                y=daily_counts['cumulative'],
                mode='lines',
                name=str(year),
                line=dict(width=3)
            ))
        
        fig_cumulative.update_layout(
            title=f'Cumulative Customer Acquisition (YTD to {reference_date.strftime("%b %d")})',
            xaxis_title='Day of Year',
            yaxis_title='Cumulative Customers',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_cumulative, use_container_width=True)
        
        # YTD Growth Rate Comparison
        growth_data = []
        for i, year in enumerate(sorted(selected_years)):
            if i > 0:
                prev_year = sorted(selected_years)[i-1]
                curr_total = len(ytd_data[year])
                prev_total = len(ytd_data[prev_year])
                growth_rate = ((curr_total - prev_total) / prev_total * 100) if prev_total > 0 else 0
                
                growth_data.append({
                    'Period': f'{prev_year} → {year}',
                    'Growth_Rate': growth_rate,
                    'Previous': prev_total,
                    'Current': curr_total,
                    'Absolute_Growth': curr_total - prev_total
                })
        
        if growth_data:
            growth_df = pd.DataFrame(growth_data)
            
            fig_growth = go.Figure()
            fig_growth.add_trace(go.Bar(
                x=growth_df['Period'],
                y=growth_df['Growth_Rate'],
                text=[f"{g:.1f}%" for g in growth_df['Growth_Rate']],
                textposition='auto',
                marker_color=['green' if g > 0 else 'red' for g in growth_df['Growth_Rate']]
            ))
            
            fig_growth.update_layout(
                title='Year-over-Year Growth Rate (YTD)',
                xaxis_title='Period',
                yaxis_title='Growth Rate (%)',
                showlegend=False
            )
            
            st.plotly_chart(fig_growth, use_container_width=True)
    
    with tab2:
        st.subheader("Monthly Performance Comparison")
        
        # Monthly comparison across years
        monthly_data = []
        
        for year in selected_years:
            year_df = ytd_data[year]
            monthly_counts = year_df.groupby('AC_OPEN_MONTH').agg({
                'CUSTOMER_NO': 'count',
                'iNET_Registration_status': lambda x: (x == 'Registered').sum()
            }).reset_index()
            
            monthly_counts['Year'] = year
            monthly_counts.columns = ['Month', 'Total_Customers', 'Registered', 'Year']
            monthly_data.append(monthly_counts)
        
        monthly_df = pd.concat(monthly_data)
        
        # Monthly comparison chart
        fig_monthly = go.Figure()
        
        for year in selected_years:
            year_monthly = monthly_df[monthly_df['Year'] == year]
            fig_monthly.add_trace(go.Bar(
                x=year_monthly['Month'],
                y=year_monthly['Total_Customers'],
                name=str(year),
                text=year_monthly['Total_Customers'],
                textposition='auto'
            ))
        
        fig_monthly.update_layout(
            title='Monthly Customer Acquisition Comparison',
            xaxis_title='Month',
            yaxis_title='Number of Customers',
            xaxis=dict(
                tickmode='array',
                tickvals=list(range(1, 13)),
                ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            ),
            barmode='group'
        )
        
        st.plotly_chart(fig_monthly, use_container_width=True)
        
        # Month-by-month growth table
        if len(selected_years) >= 2:
            st.subheader("Month-by-Month Growth Analysis")
            
            pivot_monthly = monthly_df.pivot(index='Month', columns='Year', values='Total_Customers').fillna(0)
            
            # Calculate growth rates
            for i in range(1, len(pivot_monthly.columns)):
                curr_year = pivot_monthly.columns[i]
                prev_year = pivot_monthly.columns[i-1]
                pivot_monthly[f'Growth_{prev_year}→{curr_year}'] = (
                    (pivot_monthly[curr_year] - pivot_monthly[prev_year]) / pivot_monthly[prev_year] * 100
                ).round(1)
            
            # Format and display
            st.dataframe(
                pivot_monthly.style.format({
                    col: '{:.0f}' for col in pivot_monthly.columns if 'Growth' not in str(col)
                }).format({
                    col: '{:+.1f}%' for col in pivot_monthly.columns if 'Growth' in str(col)
                }).background_gradient(subset=[col for col in pivot_monthly.columns if 'Growth' in str(col)], 
                                     cmap='RdYlGn', vmin=-50, vmax=50)
            )
    
    with tab3:
        st.subheader("Regional Year-to-Date Analysis")
        
        # Regional comparison across years
        regional_comparison = []
        
        for year in selected_years:
            year_df = ytd_data[year]
            regional_stats = year_df.groupby('REGION_DESC').agg({
                'CUSTOMER_NO': 'count',
                'INET_ELIGIBLE': lambda x: (x == 'Y').sum(),
                'iNET_Registration_status': lambda x: (x == 'Registered').sum()
            }).reset_index()
            
            regional_stats['Year'] = year
            regional_stats['Adoption_Rate'] = (
                regional_stats['iNET_Registration_status'] / regional_stats['INET_ELIGIBLE'] * 100
            ).round(1)
            
            regional_comparison.append(regional_stats)
        
        regional_df = pd.concat(regional_comparison)
        
        # Regional performance heatmap
        pivot_regional = regional_df.pivot(
            index='REGION_DESC', 
            columns='Year', 
            values='CUSTOMER_NO'
        ).fillna(0)
        
        fig_heatmap = px.imshow(
            pivot_regional.values,
            labels=dict(x="Year", y="Region", color="Customers"),
            x=pivot_regional.columns,
            y=pivot_regional.index,
            title="Regional Customer Distribution Heatmap (YTD)",
            color_continuous_scale="Blues",
            text_auto=True
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Regional growth leaders
        if len(selected_years) >= 2:
            latest_year = max(selected_years)
            prev_year = sorted(selected_years)[-2]
            
            latest_regional = regional_df[regional_df['Year'] == latest_year].set_index('REGION_DESC')
            prev_regional = regional_df[regional_df['Year'] == prev_year].set_index('REGION_DESC')
            
            growth_by_region = pd.DataFrame({
                'Current_Year': latest_regional['CUSTOMER_NO'],
                'Previous_Year': prev_regional['CUSTOMER_NO'],
                'Growth': latest_regional['CUSTOMER_NO'] - prev_regional['CUSTOMER_NO'],
                'Growth_Rate': ((latest_regional['CUSTOMER_NO'] - prev_regional['CUSTOMER_NO']) / 
                               prev_regional['CUSTOMER_NO'] * 100).round(1)
            }).fillna(0)
            
            growth_by_region = growth_by_region.sort_values('Growth_Rate', ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🏆 Top Growing Regions**")
                top_regions = growth_by_region.head(5)
                for region, data in top_regions.iterrows():
                    st.metric(
                        region,
                        f"{int(data['Current_Year']):,}",
                        f"{data['Growth_Rate']:+.1f}%"
                    )
            
            with col2:
                st.markdown("**📊 Regional Growth Chart**")
                fig_regional_growth = px.bar(
                    growth_by_region.reset_index(),
                    x='REGION_DESC',
                    y='Growth_Rate',
                    title=f'Regional Growth Rate ({prev_year} → {latest_year} YTD)',
                    color='Growth_Rate',
                    color_continuous_scale='RdYlGn',
                    text='Growth_Rate'
                )
                fig_regional_growth.update_traces(texttemplate='%{text:.1f}%')
                fig_regional_growth.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_regional_growth, use_container_width=True)
    
    with tab4:
        st.subheader("Conversion Funnel Comparison")
        
        # Create funnel for each year
        funnel_comparison = []
        
        for year in selected_years:
            year_df = ytd_data[year]
            
            total = len(year_df)
            eligible = len(year_df[year_df['INET_ELIGIBLE'] == 'Y'])
            registered = len(year_df[year_df['iNET_Registration_status'] == 'Registered'])
            active = len(year_df[year_df['Activity_Status'].isin(['Weekly Active', 'Monthly Active'])])
            
            funnel_comparison.append({
                'Year': year,
                'Total_Customers': total,
                'Eligible': eligible,
                'Registered': registered,
                'Active': active,
                'Eligibility_Rate': eligible/total*100 if total > 0 else 0,
                'Registration_Rate': registered/eligible*100 if eligible > 0 else 0,
                'Activation_Rate': active/registered*100 if registered > 0 else 0
            })
        
        funnel_df = pd.DataFrame(funnel_comparison)
        
        # Funnel visualization
        fig_funnels = make_subplots(
            rows=1, cols=len(selected_years),
            subplot_titles=[str(year) for year in selected_years],
            specs=[[{'type': 'funnel'}] * len(selected_years)]
        )
        
        for i, year in enumerate(selected_years):
            year_data = funnel_df[funnel_df['Year'] == year].iloc[0]
            
            fig_funnels.add_trace(
                go.Funnel(
                    y=['Total', 'Eligible', 'Registered', 'Active'],
                    x=[year_data['Total_Customers'], year_data['Eligible'], 
                       year_data['Registered'], year_data['Active']],
                    textinfo="value+percent initial",
                    name=str(year)
                ),
                row=1, col=i+1
            )
        
        fig_funnels.update_layout(height=500, title='Conversion Funnel Comparison (YTD)')
        st.plotly_chart(fig_funnels, use_container_width=True)
        
        # Conversion rates comparison
        st.subheader("Conversion Rate Trends")
        
        conversion_metrics = funnel_df[['Year', 'Eligibility_Rate', 'Registration_Rate', 'Activation_Rate']]
        
        fig_conversion = go.Figure()
        
        for metric in ['Eligibility_Rate', 'Registration_Rate', 'Activation_Rate']:
            fig_conversion.add_trace(go.Scatter(
                x=conversion_metrics['Year'],
                y=conversion_metrics[metric],
                mode='lines+markers',
                name=metric.replace('_', ' ').title(),
                line=dict(width=3),
                marker=dict(size=10)
            ))
        
        fig_conversion.update_layout(
            title='Conversion Rate Trends (YTD)',
            xaxis_title='Year',
            yaxis_title='Rate (%)',
            yaxis=dict(range=[0, 100]),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_conversion, use_container_width=True)
    
    with tab5:
        st.subheader("Export Year-to-Date Analysis")
        
        # Create comprehensive Excel export
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export YTD Summary", type="primary"):
                output = BytesIO()
                
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    # Summary sheet
                    summary_data = []
                    for year in selected_years:
                        year_data = ytd_data[year]
                        summary_data.append({
                            'Year': year,
                            'Total_Customers': len(year_data),
                            'Eligible': len(year_data[year_data['INET_ELIGIBLE'] == 'Y']),
                            'Registered': len(year_data[year_data['iNET_Registration_status'] == 'Registered']),
                            'Active': len(year_data[year_data['Activity_Status'].isin(['Weekly Active', 'Monthly Active'])]),
                            'Avg_Days_to_Onboard': year_data['days_to_onboard'].mean()
                        })
                    
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='YTD_Summary', index=False)
                    
                    # Monthly breakdown
                    monthly_df.to_excel(writer, sheet_name='Monthly_Breakdown', index=False)
                    
                    # Regional analysis
                    regional_df.to_excel(writer, sheet_name='Regional_Analysis', index=False)
                    
                    # Funnel metrics
                    funnel_df.to_excel(writer, sheet_name='Funnel_Metrics', index=False)
                
                output.seek(0)
                b64 = base64.b64encode(output.read()).decode()
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="YTD_Analysis_{reference_date.strftime("%Y%m%d")}.xlsx">Download YTD Analysis</a>'
                st.markdown(href, unsafe_allow_html=True)
        
        with col2:
            if st.button("📈 Export Growth Analysis"):
                output = BytesIO()
                
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    # YoY growth
                    if 'growth_df' in locals():
                        growth_df.to_excel(writer, sheet_name='YoY_Growth', index=False)
                    
                    # Monthly growth
                    if 'pivot_monthly' in locals():
                        pivot_monthly.to_excel(writer, sheet_name='Monthly_Growth')
                    
                    # Regional growth
                    if 'growth_by_region' in locals():
                        growth_by_region.to_excel(writer, sheet_name='Regional_Growth')
                
                output.seek(0)
                b64 = base64.b64encode(output.read()).decode()
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="Growth_Analysis_{reference_date.strftime("%Y%m%d")}.xlsx">Download Growth Analysis</a>'
                st.markdown(href, unsafe_allow_html=True)
        
        with col3:
            # Calculate how much data to include
            total_rows = len(df)
            sample_size = min(50000, total_rows)
            
            if st.button(f"💾 Export Data Sample ({sample_size:,} rows)"):
                # Get sample of filtered data
                sample_data = df.sample(n=sample_size, random_state=42) if total_rows > sample_size else df
                
                csv = sample_data.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="customer_data_sample_{reference_date.strftime("%Y%m%d")}.csv">Download Data Sample</a>'
                st.markdown(href, unsafe_allow_html=True)
    
    # Performance metrics at bottom
    st.markdown("---")
    st.subheader("📊 Dashboard Performance")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", f"{len(df):,}")
    with col2:
        st.metric("Years Analyzed", len(selected_years))
    with col3:
        st.metric("YTD Days", reference_doy)
    with col4:
        memory_usage = df.memory_usage(deep=True).sum() / 1024**2
        st.metric("Memory Usage", f"{memory_usage:.1f} MB")

else:
    st.info("👈 Please load your data using the sidebar to begin Year-to-Date analysis")
    
    st.markdown("""
    ### 📋 Features of this YTD Dashboard:
    
    - **Complete Dataset Analysis**: Works with your full 200MB+ file
    - **True YTD Comparisons**: Compare Jan 1 - May 23 across multiple years
    - **Cumulative Trends**: See how customer acquisition builds throughout the year
    - **Growth Analysis**: Calculate exact growth rates for the same period across years
    - **Regional Insights**: Identify which regions are growing fastest YTD
    - **Conversion Funnels**: Compare funnel performance for the same period each year
    - **Flexible Date Selection**: Choose any date for YTD cutoff
    - **Excel Exports**: Download comprehensive analysis reports
    
    ### 🚀 Getting Started:
    
    1. Enter your file path in the sidebar
    2. Click "Load Complete Dataset"
    3. Select years to compare
    4. Choose your YTD reference date
    5. Explore the analysis tabs
    """)
