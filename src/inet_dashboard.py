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
import os
import gc

# Page configuration
st.set_page_config(
    page_title="iNET Adoption Analytics Dashboard",
    page_icon="📱",
    layout="wide"
)

# Title and description
st.title("📱 iNET Mobile Banking Adoption Analytics")
st.markdown("**Regional Analysis & Customer Journey Funnel Dashboard**")

# Large file handling options
st.sidebar.header("📁 Data Loading Options")
data_option = st.sidebar.radio(
    "Choose data loading method:",
    ["Upload File (< 200MB)", "Load from Local Path", "Use Sample Data", "Process Large File Locally"]
)

df = None

if data_option == "Upload File (< 200MB)":
    uploaded_file = st.file_uploader(
        "Upload your Customer Data (CSV/Excel)", 
        type=["csv", "xlsx", "xlsb"],
        help="For files larger than 200MB, use 'Load from Local Path' option"
    )
    
    if uploaded_file is not None:
        @st.cache_data
        def load_uploaded_file(file):
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith('.xlsx'):
                df = pd.read_excel(file, engine='openpyxl')
            elif file.name.endswith('.xlsb'):
                df = pd.read_excel(file, engine='pyxlsb')
            return df
        
        df = load_uploaded_file(uploaded_file)

elif data_option == "Load from Local Path":
    st.info("📌 For large files (> 200MB), specify the file path on your local machine")
    
    file_path = st.text_input(
        "Enter the full path to your CSV file:",
        placeholder="C:/Users/YourName/Documents/Customer-Level-Account Holder Detail Report.csv"
    )
    
    if file_path and st.button("Load File"):
        if os.path.exists(file_path):
            with st.spinner("Loading large file... This may take a moment"):
                try:
                    # For very large files, use chunking
                    @st.cache_data
                    def load_large_csv(path, sample_size=None):
                        # First, get the total number of rows
                        total_rows = sum(1 for line in open(path, 'r', encoding='utf-8')) - 1
                        st.info(f"Total rows in file: {total_rows:,}")
                        
                        if sample_size and total_rows > sample_size:
                            # Sample random rows for faster processing
                            skip_rows = sorted(np.random.choice(range(1, total_rows), 
                                                              total_rows - sample_size, 
                                                              replace=False))
                            df = pd.read_csv(path, skiprows=skip_rows)
                            st.warning(f"Loaded {sample_size:,} random samples from {total_rows:,} total rows")
                        else:
                            # Load full file in chunks for memory efficiency
                            chunks = []
                            chunk_size = 50000
                            
                            for chunk in pd.read_csv(path, chunksize=chunk_size):
                                chunks.append(chunk)
                                
                            df = pd.concat(chunks, ignore_index=True)
                            st.success(f"Successfully loaded {len(df):,} rows")
                        
                        return df
                    
                    # Option to sample data for faster processing
                    use_sample = st.checkbox("Use data sampling for faster processing?")
                    if use_sample:
                        sample_size = st.number_input("Sample size (rows):", 
                                                    min_value=10000, 
                                                    max_value=1000000, 
                                                    value=100000, 
                                                    step=10000)
                        df = load_large_csv(file_path, sample_size)
                    else:
                        df = load_large_csv(file_path)
                    
                    # Free up memory
                    gc.collect()
                    
                except Exception as e:
                    st.error(f"Error loading file: {str(e)}")
        else:
            st.error("File not found. Please check the path.")

elif data_option == "Use Sample Data":
    st.info("Loading sample data for demonstration...")
    
    @st.cache_data
    def create_sample_data():
        # Create realistic sample data
        np.random.seed(42)
        n_rows = 50000
        
        regions = ['North', 'South', 'East', 'West', 'Central']
        branches = [f'Branch_{i}' for i in range(1, 101)]
        
        # Generate dates
        start_date = pd.Timestamp('2023-01-01')
        end_date = pd.Timestamp('2025-05-23')
        
        df = pd.DataFrame({
            'UNIQUE_ID_VALUE': range(1, n_rows + 1),
            'UNIQUE_ID_NAME': [f'ID_{i}' for i in range(1, n_rows + 1)],
            'CUSTOMER_NO': np.random.randint(100000, 999999, n_rows),
            'BRANCH_CODE': np.random.randint(1, 101, n_rows),
            'BRANCH_NAME': np.random.choice(branches, n_rows),
            'REGION_DESC': np.random.choice(regions, n_rows),
            'AC_OPEN_DATE': pd.to_datetime(
                np.random.randint(start_date.value, end_date.value, n_rows)
            ),
            'INET_ELIGIBLE': np.random.choice(['Y', 'N'], n_rows, p=[0.8, 0.2]),
            'AGE': np.random.randint(18, 70, n_rows),
            'ACCOUNT_TYPE': np.random.choice(['Savings', 'Current', 'Fixed'], n_rows, p=[0.7, 0.2, 0.1]),
            'ACCOUNT_STATUS': np.random.choice(['Active', 'Inactive'], n_rows, p=[0.9, 0.1]),
            'CURRENCY': 'PKR',
            'CUSTOMER_MTD_AVERAGE_ALL_ACTIVE_ELIGIBLE': np.random.uniform(1000, 100000, n_rows)
        })
        
        # Add mobile app registration dates (70% registered)
        registered_mask = np.random.choice([True, False], n_rows, p=[0.7, 0.3])
        df['MOBILE_APP_REGISTRATION_DATE'] = pd.NaT
        
        for idx in df[registered_mask].index:
            ac_open = df.loc[idx, 'AC_OPEN_DATE']
            # Some registered before account opening (10%), others after
            if np.random.random() < 0.1:
                days_before = np.random.randint(1, 365)
                df.loc[idx, 'MOBILE_APP_REGISTRATION_DATE'] = ac_open - pd.Timedelta(days=days_before)
            else:
                days_after = np.random.exponential(30)  # Most register within 30 days
                df.loc[idx, 'MOBILE_APP_REGISTRATION_DATE'] = ac_open + pd.Timedelta(days=int(days_after))
        
        # Add last transaction dates
        df['LAST_TRX_DATE'] = pd.NaT
        for idx in df[registered_mask].index:
            reg_date = df.loc[idx, 'MOBILE_APP_REGISTRATION_DATE']
            if pd.notna(reg_date):
                days_since = np.random.exponential(15)  # Recent transactions
                df.loc[idx, 'LAST_TRX_DATE'] = end_date - pd.Timedelta(days=int(days_since))
        
        # Add other required columns
        df['CIF_CREATION_DATE'] = df['AC_OPEN_DATE'] - pd.Timedelta(days=np.random.randint(0, 30, n_rows))
        df['CUSTOMER_RELATIONSHIP_DATE'] = df['CIF_CREATION_DATE']
        df['AREA'] = df['REGION_DESC'] + '_Area'
        df['ACCOUNT_CLASS'] = 'Standard'
        df['ACCOUNT_CLASS_DESCRIPTION'] = 'Standard Account'
        df['ELIGIBLE'] = df['INET_ELIGIBLE']
        df['ELIGIBLE_REMARKS'] = 'Eligible for iNET'
        df['INET_ELIGIBLE'] = df['ELIGIBLE']
        
        return df
    
    df = create_sample_data()
    st.success("Sample data loaded successfully!")

elif data_option == "Process Large File Locally":
    st.markdown("""
    ### 📊 Process Large Files Locally
    
    For files larger than 200MB, we recommend preprocessing your data locally before uploading:
    
    **Option 1: Create a smaller sample**
    ```python
    import pandas as pd
    
    # Read large file
    df = pd.read_csv('your_large_file.csv')
    
    # Option A: Take first N rows
    df_sample = df.head(100000)
    
    # Option B: Random sample
    df_sample = df.sample(n=100000, random_state=42)
    
    # Option C: Filter by date range
    df['AC_OPEN_DATE'] = pd.to_datetime(df['AC_OPEN_DATE'])
    df_sample = df[df['AC_OPEN_DATE'].dt.year == 2024]
    
    # Save smaller file
    df_sample.to_csv('customer_data_sample.csv', index=False)
    ```
    
    **Option 2: Split by year/region**
    ```python
    # Split by year
    for year in df['AC_OPEN_DATE'].dt.year.unique():
        year_data = df[df['AC_OPEN_DATE'].dt.year == year]
        year_data.to_csv(f'customer_data_{year}.csv', index=False)
    ```
    
    **Option 3: Aggregate data**
    ```python
    # Create summary statistics
    summary = df.groupby(['REGION_DESC', 'AC_OPEN_DATE']).agg({
        'CUSTOMER_NO': 'count',
        'INET_ELIGIBLE': lambda x: (x == 'Y').sum(),
        # Add more aggregations
    }).reset_index()
    summary.to_csv('customer_summary.csv', index=False)
    ```
    """)

# Continue with the rest of the dashboard only if data is loaded
if df is not None:
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
    with st.spinner("Processing data..."):
        df_processed = preprocess_data(df)
    
    # Show data info
    st.success(f"Data loaded successfully! Total rows: {len(df_processed):,}")
    
    # Memory usage info
    memory_usage = df_processed.memory_usage(deep=True).sum() / 1024**2
    st.info(f"Memory usage: {memory_usage:.2f} MB")
    
    # Continue with the rest of the dashboard code...
    # (Rest of the dashboard code from the previous artifact - filters, tabs, visualizations, etc.)
    
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
    
    # Quick Export Option for Large Files
    st.header("📥 Quick Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Export Summary Statistics"):
            summary_stats = pd.DataFrame({
                'Metric': ['Total Customers', 'iNET Eligible', 'Registered', 'Active Users', 
                          'Adoption Rate', 'Active Rate'],
                'Value': [total_customers, inet_eligible, registered_customers, active_users,
                         f"{adoption_rate:.1f}%" if 'adoption_rate' in locals() else "N/A",
                         f"{active_rate:.1f}%" if 'active_rate' in locals() else "N/A"]
            })
            
            csv = summary_stats.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="summary_stats.csv">Download Summary CSV</a>'
            st.markdown(href, unsafe_allow_html=True)
    
    with col2:
        if st.button("Export Regional Analysis"):
            regional_stats = filtered_df.groupby('REGION_DESC').agg({
                'CUSTOMER_NO': 'count',
                'INET_ELIGIBLE': lambda x: (x == 'Y').sum(),
                'iNET_Registration_status': lambda x: (x == 'Registered').sum()
            }).rename(columns={
                'CUSTOMER_NO': 'Total_Customers',
                'INET_ELIGIBLE': 'Eligible_Customers',
                'iNET_Registration_status': 'Registered_Customers'
            })
            
            csv = regional_stats.to_csv()
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="regional_analysis.csv">Download Regional CSV</a>'
            st.markdown(href, unsafe_allow_html=True)
    
    with col3:
        if st.button("Export Filtered Data Sample"):
            # Export first 10000 rows of filtered data
            sample_size = min(10000, len(filtered_df))
            sample_data = filtered_df.head(sample_size)
            
            csv = sample_data.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="filtered_data_sample.csv">Download Sample CSV ({sample_size} rows)</a>'
            st.markdown(href, unsafe_allow_html=True)

else:
    if data_option != "Process Large File Locally":
        st.warning("Please load data to begin analysis")