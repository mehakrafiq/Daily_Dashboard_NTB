import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')
from io import BytesIO
import xlsxwriter
from datetime import datetime
import base64

# Page configuration
st.set_page_config(
    page_title="iNET Adoption Analytics Dashboard",
    page_icon="📱",
    layout="wide"
)

# Title and description
st.title("📱 iNET Mobile Banking Adoption Analytics")
st.markdown("**Regional Analysis & Customer Journey Funnel Dashboard**")

# File upload with increased size limit
uploaded_file = st.file_uploader(
    "Upload your Customer Data CSV", 
    type=["csv", "xlsx", "xlsb"],
    help="Supports files up to 500MB"
)

if uploaded_file is not None:
    # Load data based on file type
    @st.cache_data
    def load_data(file):
        if file.name.endswith('.csv'):
            # For large CSV files, use chunks
            try:
                df = pd.read_csv(file)
            except:
                # If file is too large, read in chunks
                chunks = []
                for chunk in pd.read_csv(file, chunksize=10000):
                    chunks.append(chunk)
                df = pd.concat(chunks, ignore_index=True)
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file, engine='openpyxl')
        elif file.name.endswith('.xlsb'):
            df = pd.read_excel(file, engine='pyxlsb')
        return df
    
    df = load_data(uploaded_file)
    
    # Data preprocessing function
    @st.cache_data
    def preprocess_data(df):
        df_processed = df.copy()
        
        # Convert date columns
        date_columns = ['CIF_CREATION_DATE', 'CUSTOMER_RELATIONSHIP_DATE', 'AC_OPEN_DATE', 
                       'MOBILE_APP_REGISTRATION_DATE', 'LAST_TRX_DATE']
        
        for col in date_columns:
            if col in df_processed.columns:
                df_processed[col] = pd.to_datetime(df_processed[col], errors='coerce')
        
        # Create registration status
        def get_registration_status(row):
            if pd.isna(row['MOBILE_APP_REGISTRATION_DATE']):
                return 'Not Registered'
            elif row['MOBILE_APP_REGISTRATION_DATE'] < row['AC_OPEN_DATE']:
                return 'Already Registered'
            else:
                return 'Registered'
        
        df_processed['iNET_Registration_status'] = df_processed.apply(get_registration_status, axis=1)
        
        # Calculate days to onboard
        df_processed['days_to_onboard'] = (df_processed['MOBILE_APP_REGISTRATION_DATE'] - df_processed['AC_OPEN_DATE']).dt.days
        
        # Onboarding time categories
        def categorize_onboarding_time(row):
            if row['iNET_Registration_status'] in ['Already Registered', 'Not Registered']:
                return None
            days = row['days_to_onboard']
            if pd.isna(days):
                return None
            elif days <= 7:
                return 'Within 1 week'
            elif days <= 15:
                return 'Within 15 days'
            elif days <= 30:
                return '15-30 days'
            elif days <= 60:
                return 'Within 2 months'
            elif days <= 90:
                return 'Within 3 months'
            elif days <= 180:
                return 'Within 6 months'
            else:
                return 'More than 6 months'
        
        df_processed['onboarding_time_category'] = df_processed.apply(categorize_onboarding_time, axis=1)
        
        # Calculate days since last transaction
        current_date = pd.Timestamp.now()
        df_processed['days_since_last_trx'] = (current_date - df_processed['LAST_TRX_DATE']).dt.days
        
        # Create activity status
        conditions = [
            (df_processed['days_since_last_trx'] <= 7),
            (df_processed['days_since_last_trx'] <= 14),
            (df_processed['days_since_last_trx'] <= 30),
            (df_processed['days_since_last_trx'] <= 90),
            (df_processed['days_since_last_trx'] <= 180),
            (df_processed['days_since_last_trx'] <= 365),
            (df_processed['days_since_last_trx'] > 365)
        ]
        
        choices = [
            'Weekly Active',
            'Biweekly Active', 
            'Monthly Active',
            '3 Months Active',
            '6 Months Active',
            '1 Year Active',
            'More than 1 Year'
        ]
        
        df_processed['Activity_Status'] = np.select(conditions, choices, default='Unknown')
        
        # Add year and month columns
        df_processed['AC_OPEN_YEAR'] = df_processed['AC_OPEN_DATE'].dt.year
        df_processed['AC_OPEN_MONTH'] = df_processed['AC_OPEN_DATE'].dt.month
        
        return df_processed
    
    # Process data
    df_processed = preprocess_data(df)
    
    # Sidebar for filters
    st.sidebar.header("🔍 Filters")
    
    # Year filter
    available_years = sorted(df_processed['AC_OPEN_YEAR'].dropna().unique())
    selected_year = st.sidebar.selectbox(
        "Select Account Opening Year",
        ['All'] + [int(year) for year in available_years]
    )
    
    # Regional filter
    regions = ['All'] + sorted(df_processed['REGION_DESC'].dropna().unique().tolist())
    selected_region = st.sidebar.selectbox("Select Region", regions)
    
    # Apply filters
    filtered_df = df_processed.copy()
    if selected_year != 'All':
        filtered_df = filtered_df[filtered_df['AC_OPEN_YEAR'] == selected_year]
    if selected_region != 'All':
        filtered_df = filtered_df[filtered_df['REGION_DESC'] == selected_region]
    
    # Store all figures for Excel export
    figures = {}
    
    # Main dashboard
    st.header("📊 Dashboard Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_customers = len(filtered_df)
        st.metric("Total Customers", f"{total_customers:,}")
    
    with col2:
        inet_eligible = len(filtered_df[filtered_df['INET_ELIGIBLE'] == 'Y'])
        st.metric("iNET Eligible", f"{inet_eligible:,}")
    
    with col3:
        registered_customers = len(filtered_df[filtered_df['iNET_Registration_status'] == 'Registered'])
        if inet_eligible > 0:
            adoption_rate = (registered_customers / inet_eligible) * 100
            st.metric("Adoption Rate", f"{adoption_rate:.1f}%")
        else:
            st.metric("Adoption Rate", "0%")
    
    with col4:
        active_users = len(filtered_df[filtered_df['Activity_Status'].isin(['Weekly Active', 'Biweekly Active', 'Monthly Active'])])
        if registered_customers > 0:
            active_rate = (active_users / registered_customers) * 100
            st.metric("Active User Rate", f"{active_rate:.1f}%")
        else:
            st.metric("Active User Rate", "0%")
    
    # Tab layout
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🌍 Regional Analysis", "📈 Adoption Funnel", "⏱️ Onboarding Timeline", "📊 Activity Analysis", "📈 Trends", "📅 YoY Comparison"])
    
    with tab1:
        st.subheader("Regional iNET Adoption Analysis")
        
        # Regional adoption rates
        regional_stats = filtered_df.groupby('REGION_DESC').agg({
            'CUSTOMER_NO': 'count',
            'INET_ELIGIBLE': lambda x: (x == 'Y').sum(),
            'iNET_Registration_status': lambda x: (x == 'Registered').sum()
        }).rename(columns={
            'CUSTOMER_NO': 'Total_Customers',
            'INET_ELIGIBLE': 'Eligible_Customers',
            'iNET_Registration_status': 'Registered_Customers'
        })
        
        regional_stats['Adoption_Rate'] = (regional_stats['Registered_Customers'] / regional_stats['Eligible_Customers'] * 100).round(2)
        regional_stats['Eligibility_Rate'] = (regional_stats['Eligible_Customers'] / regional_stats['Total_Customers'] * 100).round(2)
        
        # Regional adoption rate chart
        fig_regional = px.bar(
            regional_stats.reset_index(),
            x='REGION_DESC',
            y='Adoption_Rate',
            title='iNET Adoption Rate by Region',
            labels={'Adoption_Rate': 'Adoption Rate (%)', 'REGION_DESC': 'Region'},
            color='Adoption_Rate',
            color_continuous_scale='viridis'
        )
        fig_regional.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_regional, use_container_width=True)
        figures['regional_adoption'] = fig_regional
        
        # Regional statistics table
        st.subheader("Regional Statistics Summary")
        st.dataframe(regional_stats.round(2))
    
    with tab2:
        st.subheader("Customer Adoption Funnel")
        
        # Overall funnel
        total_customers = len(filtered_df)
        eligible_customers = len(filtered_df[filtered_df['INET_ELIGIBLE'] == 'Y'])
        registered_customers = len(filtered_df[filtered_df['iNET_Registration_status'] == 'Registered'])
        active_customers = len(filtered_df[filtered_df['Activity_Status'].isin(['Weekly Active', 'Biweekly Active', 'Monthly Active'])])
        
        funnel_fig = go.Figure(go.Funnel(
            y=['Total Customers', 'iNET Eligible', 'Registered', 'Active Users'],
            x=[total_customers, eligible_customers, registered_customers, active_customers],
            textinfo="value+percent initial",
            marker_color=['lightblue', 'orange', 'green', 'red']
        ))
        
        funnel_fig.update_layout(
            title='iNET Adoption Funnel',
            height=500
        )
        st.plotly_chart(funnel_fig, use_container_width=True)
        figures['adoption_funnel'] = funnel_fig
    
    with tab3:
        st.subheader("Onboarding Timeline Analysis")
        
        # Days to onboard by region
        onboard_data = filtered_df[filtered_df['iNET_Registration_status'] == 'Registered'].copy()
        
        if not onboard_data.empty:
            regional_onboard = onboard_data.groupby('REGION_DESC')['days_to_onboard'].agg(['median', 'mean']).round(2)
            
            fig_onboard = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig_onboard.add_trace(
                go.Bar(name='Median Days', x=regional_onboard.index, y=regional_onboard['median']),
                secondary_y=False,
            )
            
            fig_onboard.add_trace(
                go.Scatter(name='Mean Days', x=regional_onboard.index, y=regional_onboard['mean'], mode='lines+markers'),
                secondary_y=True,
            )
            
            fig_onboard.update_xaxes(title_text="Region", tickangle=-45)
            fig_onboard.update_yaxes(title_text="Median Days", secondary_y=False)
            fig_onboard.update_yaxes(title_text="Mean Days", secondary_y=True)
            fig_onboard.update_layout(title='Days to Onboard by Region')
            
            st.plotly_chart(fig_onboard, use_container_width=True)
            figures['onboarding_by_region'] = fig_onboard
    
    with tab4:
        st.subheader("Customer Activity Analysis")
        
        # Activity status distribution
        activity_counts = filtered_df['Activity_Status'].value_counts()
        fig_activity = px.bar(
            x=activity_counts.values,
            y=activity_counts.index,
            orientation='h',
            title='Customer Activity Distribution',
            labels={'x': 'Number of Customers', 'y': 'Activity Status'}
        )
        st.plotly_chart(fig_activity, use_container_width=True)
        figures['activity_distribution'] = fig_activity
    
    with tab5:
        st.subheader("Trends Analysis")
        
        # Fixed: Monthly registration trends
        if 'AC_OPEN_DATE' in filtered_df.columns:
            monthly_reg = filtered_df.groupby([filtered_df['AC_OPEN_YEAR'], filtered_df['AC_OPEN_MONTH']]).size()
            monthly_reg = monthly_reg.reset_index(name='count')
            monthly_reg['Date'] = pd.to_datetime(monthly_reg[['AC_OPEN_YEAR', 'AC_OPEN_MONTH']].rename(columns={'AC_OPEN_YEAR': 'year', 'AC_OPEN_MONTH': 'month'}).assign(day=1))
            
            fig_trends = px.line(
                monthly_reg,
                x='Date',
                y='count',
                title='Monthly Customer Registration Trends',
                labels={'count': 'Number of Registrations'}
            )
            st.plotly_chart(fig_trends, use_container_width=True)
            figures['monthly_trends'] = fig_trends
    
    with tab6:
        st.subheader("Year-over-Year Comparison")
        
        # Get data for YoY comparison
        if len(available_years) >= 2:
            # Monthly comparison
            yoy_data = df_processed[df_processed['AC_OPEN_YEAR'].isin(available_years[-2:])]
            
            monthly_counts = yoy_data.groupby(['AC_OPEN_YEAR', 'AC_OPEN_MONTH']).size().reset_index(name='Count')
            
            # Create comparison chart
            fig_yoy = go.Figure()
            
            for year in monthly_counts['AC_OPEN_YEAR'].unique():
                year_data = monthly_counts[monthly_counts['AC_OPEN_YEAR'] == year]
                fig_yoy.add_trace(go.Bar(
                    x=year_data['AC_OPEN_MONTH'],
                    y=year_data['Count'],
                    name=str(int(year)),
                    text=year_data['Count'],
                    textposition='auto',
                ))
            
            fig_yoy.update_layout(
                title=f'Monthly Account Opening Comparison: {int(available_years[-2])} vs {int(available_years[-1])}',
                xaxis_title='Month',
                yaxis_title='Number of Accounts',
                xaxis=dict(
                    tickmode='array',
                    tickvals=list(range(1, 13)),
                    ticktext=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                ),
                barmode='group'
            )
            
            st.plotly_chart(fig_yoy, use_container_width=True)
            figures['yoy_comparison'] = fig_yoy
            
            # Growth metrics
            col1, col2 = st.columns(2)
            with col1:
                prev_year_total = monthly_counts[monthly_counts['AC_OPEN_YEAR'] == available_years[-2]]['Count'].sum()
                curr_year_total = monthly_counts[monthly_counts['AC_OPEN_YEAR'] == available_years[-1]]['Count'].sum()
                growth_rate = ((curr_year_total - prev_year_total) / prev_year_total * 100) if prev_year_total > 0 else 0
                st.metric(f"{int(available_years[-1])} Total", f"{curr_year_total:,}", f"{growth_rate:+.1f}%")
            
            with col2:
                st.metric(f"{int(available_years[-2])} Total", f"{prev_year_total:,}")
    
    # Excel Export Function
    def create_excel_download(dataframe, figures, year_filter):
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Create Summary sheet with graphs
            summary_sheet = workbook.add_worksheet('Summary')
            writer.sheets['Summary'] = summary_sheet
            
            # Add title
            title_format = workbook.add_format({'bold': True, 'font_size': 16})
            summary_sheet.write('A1', f'iNET Mobile Banking Adoption Report - {year_filter}', title_format)
            
            # Add key metrics
            metric_format = workbook.add_format({'bold': True, 'font_size': 12})
            summary_sheet.write('A3', 'Key Metrics:', metric_format)
            summary_sheet.write('A4', f'Total Customers: {total_customers:,}')
            summary_sheet.write('A5', f'iNET Eligible: {inet_eligible:,}')
            summary_sheet.write('A6', f'Adoption Rate: {adoption_rate:.1f}%' if 'adoption_rate' in locals() else 'Adoption Rate: N/A')
            summary_sheet.write('A7', f'Active User Rate: {active_rate:.1f}%' if 'active_rate' in locals() else 'Active User Rate: N/A')
            
            # Export figures as images (placeholder for actual implementation)
            summary_sheet.write('A9', 'Visualizations are available in the Streamlit dashboard', metric_format)
            
            # Write filtered data
            dataframe.to_excel(writer, sheet_name='Customer_Data', index=False)
            
            # Regional Stats
            if 'regional_stats' in locals():
                regional_stats.to_excel(writer, sheet_name='Regional_Analysis')
            
            # Add more sheets as needed
            
        output.seek(0)
        return output
    
    # Export button
    st.header("📥 Export Data")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.info(f"Export data for: {selected_year if selected_year != 'All' else 'All Years'}")
    
    with col2:
        if st.button("📊 Export to Excel", type="primary"):
            excel_file = create_excel_download(
                filtered_df, 
                figures, 
                selected_year if selected_year != 'All' else 'All Years'
            )
            
            b64 = base64.b64encode(excel_file.read()).decode()
            filename = f"iNET_Dashboard_{selected_year if selected_year != 'All' else 'All'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download Excel File</a>'
            st.markdown(href, unsafe_allow_html=True)
    
    # Questions Section
    st.header("🔍 Key Questions & Insights")
    
    with st.expander("Regional Performance Questions"):
        st.write("""
        **Key Questions to Explore:**
        1. Which region has the highest iNET adoption rate?
        2. What factors contribute to regional differences in adoption?
        3. Which regions have the fastest onboarding times?
        4. Are there regional patterns in customer activity levels?
        5. How does eligibility rate vary across regions?
        """)
    
    with st.expander("Year-over-Year Insights"):
        if len(available_years) >= 2:
            st.write(f"""
            **YoY Analysis ({int(available_years[-2])} vs {int(available_years[-1])}):**
            - Growth Rate: {growth_rate:.1f}% {'📈' if growth_rate > 0 else '📉'}
            - Best performing months for new accounts
            - Seasonal patterns in customer acquisition
            """)

else:
    st.info("👆 Please upload your customer data file to begin analysis")
    st.markdown("""
    **Supported file types:** CSV, XLSX, XLSB (up to 500MB)
    
    **Expected columns:**
    - REGION_DESC, CUSTOMER_NO, INET_ELIGIBLE
    - AC_OPEN_DATE, MOBILE_APP_REGISTRATION_DATE, LAST_TRX_DATE
    - iNET registration and activity tracking fields
    """)