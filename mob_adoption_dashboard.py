import pandas as pd
import numpy as np
import os
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Define color scheme
colors = {
    'primary': '#6b5b95',    # Purple
    'secondary': '#3ba3a0',  # Teal
    'tertiary': '#f9a261',   # Orange
    'accent1': '#4682b4',    # Steel Blue
    'accent2': '#f08080',    # Light Coral
    'accent3': '#7ac142',    # Green
    'accent4': '#f9c74f',    # Yellow
    'background': '#f8f9fa',
    'success': '#28a745',
    'warning': '#ffc107',
    'danger': '#dc3545',
    'text': '#333333',
    'gray': '#d3d3d3'
}

# Function to load data from Access database and save as CSVs
def load_data_from_access(db_path, csv_output_dir='./Data/CSVs'):
    """
    Load data from Access database and save as CSVs
    This is only needed when running the first time or when updating the database
    """
    import pyodbc
    
    # Create output directory if it doesn't exist
    os.makedirs(csv_output_dir, exist_ok=True)
    
    # Connection string
    conn_str = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={db_path};"
    )
    
    try:
        # Establish a connection
        with pyodbc.connect(conn_str) as conn:
            cursor = conn.cursor()
            
            # Retrieve table names
            cursor.tables()
            table_names = [row.table_name for row in cursor if row.table_type == 'TABLE']
            print("Tables in the database:", table_names)
            
            # Load each table into a Pandas DataFrame and save as CSV
            tables_data = {}
            for table_name in table_names:
                query = f"SELECT * FROM [{table_name}]"
                tables_data[table_name] = pd.read_sql(query, conn)
                csv_path = os.path.join(csv_output_dir, f"{table_name}.csv")
                tables_data[table_name].to_csv(csv_path, index=False)
                print(f"Saved {table_name} to {csv_path}")
                
        return tables_data
    
    except pyodbc.Error as e:
        print("Database connection error:", e)
        return None
    except Exception as e:
        print("Error:", e)
        return None

# Function to load data from CSVs
def load_data_from_csvs(csv_dir='./Data/CSVs'):
    """Load data from CSV files"""
    data = {}
    
    try:
        # Load main data file
        ntb_reg_csv_path = os.path.join(csv_dir, 'NTB_Reg_Summary.csv')
        if os.path.exists(ntb_reg_csv_path):
            data['ntb_reg_tbl_df'] = pd.read_csv(ntb_reg_csv_path)
            print(f"Loaded NTB_Reg_Summary.csv with {len(data['ntb_reg_tbl_df'])} records")
        else:
            print(f"Warning: {ntb_reg_csv_path} not found!")
        
        # Try to load other CSV files if they exist
        for table_name in ['acct_class', 'Acct_holders_tbl', 'Branch_converter_islamic', 
                          'Branch_tbl', 'NTB_DB', 'RGM_tbl']:
            file_path = os.path.join(csv_dir, f"{table_name}.csv")
            if os.path.exists(file_path):
                data[table_name] = pd.read_csv(file_path)
                print(f"Loaded {table_name}.csv")
        
        return data
    
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

# Process the data and calculate metrics
def process_data(data):
    """Process the data and calculate metrics"""
    if data is None or 'ntb_reg_tbl_df' not in data:
        print("No data to process")
        return None
    
    ntb_reg_tbl_df = data['ntb_reg_tbl_df'].copy()
    
    # Convert date columns to datetime
    date_columns = ['Registration_Date', 'Open_Date_', 'Last_Login_Date']
    for col in date_columns:
        if col in ntb_reg_tbl_df.columns:
            ntb_reg_tbl_df[col] = pd.to_datetime(ntb_reg_tbl_df[col], errors='coerce')
    
    # --- 1. Update Registration_Remarks for accounts where Registration_Date is older than Open_Date ---
    older_reg_mask = ntb_reg_tbl_df['Registration_Date'] < ntb_reg_tbl_df['Open_Date_']
    ntb_reg_tbl_df.loc[older_reg_mask, 'Registration_Remarks'] = 'Already Registered'
    
    # --- 2. Calculate Login Bracket based on Last_Login_Date ---
    current_date = pd.Timestamp.now()
    last_30_days = current_date - pd.Timedelta(days=30)
    last_90_days = current_date - pd.Timedelta(days=90) 
    last_year = current_date - pd.Timedelta(days=365)
    
    def get_login_bracket(login_date, registration_date):
        if pd.isna(login_date):
            if pd.notna(registration_date):
                return 'More than a Year'
            return 'Not Registered'
        elif login_date >= last_30_days:
            return 'Last 30 Days'
        elif login_date >= last_90_days:
            return 'Last 90 Days'
        elif login_date >= last_year:
            return 'Previous Year'
        else:
            return 'More than a Year'
    
    ntb_reg_tbl_df['Login_Bracket'] = ntb_reg_tbl_df.apply(
        lambda x: get_login_bracket(x['Last_Login_Date'], x['Registration_Date']), 
        axis=1
    )
    
    # --- 3. Calculate Days to Onboard ---
    # Create mask for valid onboarding calculation
    valid_onboarding_mask = (~ntb_reg_tbl_df['Registration_Date'].isna()) & (~ntb_reg_tbl_df['Open_Date_'].isna()) & (ntb_reg_tbl_df['Registration_Date'] >= ntb_reg_tbl_df['Open_Date_'])
    
    # Calculate days to onboard
    ntb_reg_tbl_df.loc[valid_onboarding_mask, 'Days_to_Onboard'] = (
        ntb_reg_tbl_df.loc[valid_onboarding_mask, 'Registration_Date'] - 
        ntb_reg_tbl_df.loc[valid_onboarding_mask, 'Open_Date_']
    ).dt.days
    
    # --- 4. Calculate Login Frequency ---
    login_mask = ~ntb_reg_tbl_df['Last_Login_Date'].isna()
    
    # Calculate days since last login
    ntb_reg_tbl_df.loc[login_mask, 'Days_Since_Last_Login'] = (
        current_date - ntb_reg_tbl_df.loc[login_mask, 'Last_Login_Date']
    ).dt.days
    
    def get_login_frequency(days):
        if pd.isna(days):
            return 'No Login'
        elif days <= 7:
            return 'Weekly'
        elif days <= 30:
            return 'Monthly'
        elif days <= 90:
            return 'Quarterly'
        else:
            return 'Inactive'
    
    ntb_reg_tbl_df['Login_Frequency'] = ntb_reg_tbl_df['Days_Since_Last_Login'].apply(get_login_frequency)
    
    # Update 'No Login' to 'Not Registered' when Registration_Remarks is 'Not Registered'
    not_registered_mask = (ntb_reg_tbl_df['Login_Frequency'] == 'No Login') & (ntb_reg_tbl_df['Registration_Remarks'] == 'Not Registered')
    ntb_reg_tbl_df.loc[not_registered_mask, 'Login_Frequency'] = 'Not Registered'
    
    # --- 5. Calculate Onboarding Time Brackets ---
    def get_onboarding_bracket(days):
        if pd.isna(days):
            return 'Not Registered'
        elif days <= 5:
            return '5 days or less'
        elif days <= 10:
            return '6-10 days'
        elif days <= 30:
            return '11-30 days'
        elif days <= 180:
            return '1-6 months'
        else:
            return 'More than 6 months'
    
    # Apply the binning function to eligible records
    ntb_reg_tbl_df['Onboarding_Time_Bracket'] = 'Not Registered'  # Default value
    ntb_reg_tbl_df.loc[valid_onboarding_mask, 'Onboarding_Time_Bracket'] = ntb_reg_tbl_df.loc[valid_onboarding_mask, 'Days_to_Onboard'].apply(get_onboarding_bracket)
    
    # Update Onboarding_Time_Bracket to "Already Registered" for customers with Registration_Remarks = "Already Registered"
    already_registered_mask = ntb_reg_tbl_df['Registration_Remarks'] == 'Already Registered'
    ntb_reg_tbl_df.loc[already_registered_mask, 'Onboarding_Time_Bracket'] = 'Already Registered'
    
    # --- 6. Add Open_Month for cohort analysis ---
    ntb_reg_tbl_df['Open_Month'] = pd.to_datetime(ntb_reg_tbl_df['Open_Date_']).dt.to_period('M')
    
    # Return the processed data
    return {
        'ntb_reg_tbl_df': ntb_reg_tbl_df,
        **data
    }

# Calculate summary metrics
def calculate_summary_metrics(processed_data):
    """Calculate summary metrics for dashboard"""
    ntb_reg_tbl_df = processed_data['ntb_reg_tbl_df']
    
    # Basic metrics
    total_accounts = len(ntb_reg_tbl_df)
    registered_accounts = ntb_reg_tbl_df['Registration_Remarks'].isin(['Registered', 'Already Registered']).sum()
    registration_rate = registered_accounts / total_accounts * 100
    
    active_30_days = (ntb_reg_tbl_df['Login_Bracket'] == 'Last 30 Days').sum()
    active_rate = active_30_days / registered_accounts * 100 if registered_accounts > 0 else 0
    
    avg_days_to_onboard = ntb_reg_tbl_df['Days_to_Onboard'].mean()
    
    already_registered = (ntb_reg_tbl_df['Registration_Remarks'] == 'Already Registered').sum()
    
    quick_onboarding = ntb_reg_tbl_df['Onboarding_Time_Bracket'].isin(['5 days or less', '6-10 days']).sum()
    quick_onboarding_rate = quick_onboarding / registered_accounts * 100 if registered_accounts > 0 else 0
    
    # Weekly vs monthly active users
    weekly_users = (ntb_reg_tbl_df['Login_Frequency'] == 'Weekly').sum()
    monthly_users = (ntb_reg_tbl_df['Login_Frequency'] == 'Monthly').sum()
    
    # Login frequency distribution
    login_frequency_dist = ntb_reg_tbl_df['Login_Frequency'].value_counts().to_dict()
    
    # Regional metrics
    region_metrics = ntb_reg_tbl_df.groupby('REGION_DESC').agg(
        Total_Accounts=('CUSTOMER_NO', 'count'),
        Registered=('Registration_Date', lambda x: x.notna().sum()),
        Active_30_Days=(('Login_Bracket'), lambda x: (x == 'Last 30 Days').sum()),
        Weekly_Users=(('Login_Frequency'), lambda x: (x == 'Weekly').sum()),
        Avg_Days_to_Onboard=('Days_to_Onboard', 'mean')
    ).reset_index()
    
    region_metrics['Registration_Rate'] = (region_metrics['Registered'] / region_metrics['Total_Accounts'] * 100).round(1)
    region_metrics['Activation_Rate'] = (region_metrics['Active_30_Days'] / region_metrics['Registered'] * 100).round(1)
    region_metrics['Weekly_Usage_Rate'] = (region_metrics['Weekly_Users'] / region_metrics['Active_30_Days'] * 100).round(1)
    
    # RGM Performance
    rgm_metrics = ntb_reg_tbl_df.groupby('RGM').agg(
        Total_Accounts=('CUSTOMER_NO', 'count'),
        Registered_Count=('Registration_Date', lambda x: x.notna().sum()),
        Average_Days_to_Onboard=('Days_to_Onboard', 'mean'),
        Active_30_Days=(('Login_Bracket'), lambda x: (x == 'Last 30 Days').sum()),
        Weekly_Users=(('Login_Frequency'), lambda x: (x == 'Weekly').sum())
    ).reset_index()
    
    rgm_metrics['Registration_Rate'] = (rgm_metrics['Registered_Count'] / rgm_metrics['Total_Accounts'] * 100).round(1)
    rgm_metrics['Active_Rate'] = (rgm_metrics['Active_30_Days'] / rgm_metrics['Registered_Count'] * 100).round(1)
    rgm_metrics['Weekly_Rate'] = (rgm_metrics['Weekly_Users'] / rgm_metrics['Active_30_Days'] * 100).round(1)
    
    # Calculate monthly registration trends
    # Group by month and year of Registration_Date
    ntb_reg_tbl_df['Registration_Month'] = ntb_reg_tbl_df['Registration_Date'].dt.to_period('M')
    monthly_reg = ntb_reg_tbl_df.groupby('Registration_Month').size().reset_index(name='Registrations')
    monthly_reg['Year'] = monthly_reg['Registration_Month'].dt.year
    monthly_reg['Month'] = monthly_reg['Registration_Month'].dt.month
    monthly_reg = monthly_reg.sort_values(['Year', 'Month'])
    
    # Customer Journey Funnel
    customer_journey = pd.DataFrame({
        'Stage': ['Account Opening', 'Mobile Registration', 'Active in Last 30 Days', 'Weekly Active Users'],
        'Count': [
            total_accounts,
            registered_accounts,
            active_30_days,
            weekly_users
        ]
    })
    
    customer_journey['Percentage'] = (customer_journey['Count'] / total_accounts * 100).round(1)
    
    # Calculate conversion rates between stages
    customer_journey['Conversion_Rate'] = 100.0  # Default value
    for i in range(1, len(customer_journey)):
        customer_journey.loc[i, 'Conversion_Rate'] = (
            customer_journey['Count'][i] / customer_journey['Count'][i-1] * 100
        ).round(1)
    
    customer_journey['Drop_Off'] = 100 - customer_journey['Conversion_Rate']
    
    # Onboarding time distribution
    onboarding_dist = ntb_reg_tbl_df['Onboarding_Time_Bracket'].value_counts().reset_index()
    onboarding_dist.columns = ['Bracket', 'Count']
    
    # Return all metrics
    return {
        'summary': {
            'Total_Accounts': total_accounts,
            'Registered_Accounts': registered_accounts,
            'Registration_Rate': registration_rate,
            'Active_30_Days': active_30_days,
            'Active_Rate': active_rate,
            'Avg_Days_to_Onboard': avg_days_to_onboard,
            'Already_Registered': already_registered,
            'Quick_Onboarding_Rate': quick_onboarding_rate,
            'Weekly_Users': weekly_users,
            'Monthly_Users': monthly_users
        },
        'login_frequency': login_frequency_dist,
        'region_metrics': region_metrics,
        'rgm_metrics': rgm_metrics,
        'monthly_trends': monthly_reg,
        'customer_journey': customer_journey,
        'onboarding_dist': onboarding_dist
    }

# Create Plotly Dash dashboard
def create_dashboard(metrics):
    """Create and launch the dashboard"""
    app = dash.Dash(__name__, 
                   meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
                   title="Mobile Banking Dashboard")
    
    # App layout
    app.layout = html.Div([
        # Header
        html.Div([
            html.H1("Mobile Banking Performance Dashboard", className="dashboard-title"),
            html.P(f"Data as of {pd.Timestamp.now().strftime('%Y-%m-%d')}", className="dashboard-date")
        ], className="header"),
        
        # Summary metrics row
        html.Div([
            html.Div([
                html.Div([
                    html.H3("Total Accounts"),
                    html.H2(f"{metrics['summary']['Total_Accounts']:,}")
                ], className="metric-card", style={"backgroundColor": colors['primary']}),
                html.Div([
                    html.H3("Registered Accounts"),
                    html.H2(f"{metrics['summary']['Registered_Accounts']:,}"),
                    html.P(f"{metrics['summary']['Registration_Rate']:.1f}%", className="metric-subtitle")
                ], className="metric-card", style={"backgroundColor": colors['secondary']}),
                html.Div([
                    html.H3("Active Users (30 Days)"),
                    html.H2(f"{metrics['summary']['Active_30_Days']:,}"),
                    html.P(f"{metrics['summary']['Active_Rate']:.1f}% of Registered", className="metric-subtitle")
                ], className="metric-card", style={"backgroundColor": colors['tertiary']}),
                html.Div([
                    html.H3("Weekly Active Users"),
                    html.H2(f"{metrics['summary']['Weekly_Users']:,}"),
                    html.P(f"{metrics['summary']['Weekly_Users']/metrics['summary']['Active_30_Days']*100:.1f}% of Active", className="metric-subtitle")
                ], className="metric-card", style={"backgroundColor": colors['accent1']})
            ], className="summary-row")
        ]),
        
        # First row of charts
        html.Div([
            # Login Frequency Distribution
            html.Div([
                html.H3("Login Frequency Distribution", className="chart-title"),
                dcc.Graph(
                    id='login-frequency-chart',
                    figure=go.Figure(
                        data=[go.Bar(
                            x=list(metrics['login_frequency'].keys()),
                            y=list(metrics['login_frequency'].values()),
                            marker_color=[
                                colors['accent3'],  # Weekly
                                '#8eb343',          # Monthly
                                colors['accent4'],  # Quarterly
                                colors['warning'],  # Inactive
                                colors['gray'],     # No Login
                                colors['accent2']   # Not Registered
                            ]
                        )],
                        layout=go.Layout(
                            title="",
                            plot_bgcolor=colors['background'],
                            paper_bgcolor=colors['background'],
                            font={"color": colors['text']},
                            margin=dict(l=40, r=40, t=10, b=30)
                        )
                    )
                )
            ], className="chart-container"),
            
            # Customer Journey Funnel
            html.Div([
                html.H3("Customer Journey Funnel", className="chart-title"),
                dcc.Graph(
                    id='funnel-chart',
                    figure=go.Figure(
                        data=[go.Funnel(
                            y=metrics['customer_journey']['Stage'],
                            x=metrics['customer_journey']['Count'],
                            textinfo="value+percent initial",
                            marker={"color": [
                                colors['primary'],
                                colors['secondary'],
                                colors['tertiary'],
                                colors['accent3']
                            ]}
                        )],
                        layout=go.Layout(
                            title="",
                            plot_bgcolor=colors['background'],
                            paper_bgcolor=colors['background'],
                            font={"color": colors['text']},
                            margin=dict(l=40, r=40, t=10, b=30)
                        )
                    )
                )
            ], className="chart-container")
        ], className="chart-row"),
        
        # Second row of charts
        html.Div([
            # Regional Performance
            html.Div([
                html.H3("Regional Performance", className="chart-title"),
                dcc.Graph(
                    id='region-performance-chart',
                    figure=go.Figure(
                        data=[
                            go.Bar(
                                name='Registration Rate',
                                y=metrics['region_metrics']['REGION_DESC'],
                                x=metrics['region_metrics']['Registration_Rate'],
                                orientation='h',
                                marker_color=colors['primary']
                            ),
                            go.Bar(
                                name='Activation Rate',
                                y=metrics['region_metrics']['REGION_DESC'],
                                x=metrics['region_metrics']['Activation_Rate'],
                                orientation='h',
                                marker_color=colors['tertiary']
                            )
                        ],
                        layout=go.Layout(
                            barmode='group',
                            title="",
                            plot_bgcolor=colors['background'],
                            paper_bgcolor=colors['background'],
                            font={"color": colors['text']},
                            margin=dict(l=40, r=40, t=10, b=30),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            ),
                            xaxis=dict(title="Rate (%)"),
                            yaxis=dict(autorange="reversed")
                        )
                    )
                )
            ], className="chart-container"),
            
            # Onboarding Time Distribution
            html.Div([
                html.H3("Onboarding Time Distribution", className="chart-title"),
                html.Div([
                    dcc.Graph(
                        id='onboarding-pie-chart',
                        figure=px.pie(
                            metrics['onboarding_dist'],
                            values='Count',
                            names='Bracket',
                            color_discrete_sequence=[
                                colors['success'],        # 5 days or less
                                colors['accent3'],        # 6-10 days
                                colors['accent4'],        # 11-30 days
                                colors['warning'],        # 1-6 months
                                colors['danger'],         # More than 6 months
                                colors['gray'],           # Not Registered
                                colors['secondary']       # Already Registered
                            ],
                            hole=0.4
                        ).update_layout(
                            plot_bgcolor=colors['background'],
                            paper_bgcolor=colors['background'],
                            font={"color": colors['text']},
                            margin=dict(l=40, r=40, t=10, b=30),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=-0.1,
                                xanchor="center",
                                x=0.5
                            )
                        )
                    ),
                    html.Div([
                        html.Div([
                            html.H4("Avg Days to Onboard"),
                            html.H2(f"{metrics['summary']['Avg_Days_to_Onboard']:.1f}", 
                                   style={"color": colors['primary'], "margin": "8px 0"})
                        ], className="onboarding-stat"),
                        html.Div([
                            html.H4("Quick Onboarding Rate"),
                            html.H2(f"{metrics['summary']['Quick_Onboarding_Rate']:.1f}%",
                                   style={"color": colors['success'], "margin": "8px 0"})
                        ], className="onboarding-stat")
                    ], className="onboarding-stats-container")
                ], style={"display": "flex", "flexDirection": "row", "height": "100%"})
            ], className="chart-container")
        ], className="chart-row"),
        
        # Third row of charts
        html.Div([
            # Monthly Registrations Trend
            html.Div([
                html.H3("Monthly Registration Trends", className="chart-title"),
                dcc.Graph(
                    id='monthly-trend-chart',
                    figure=go.Figure(
                        data=[go.Scatter(
                            x=metrics['monthly_trends']['Registration_Month'].astype(str),
                            y=metrics['monthly_trends']['Registrations'],
                            mode='lines+markers',
                            name='Registrations',
                            line=dict(color=colors['primary'], width=3),
                            marker=dict(size=8, color=colors['secondary'])
                        )],
                        layout=go.Layout(
                            title="",
                            plot_bgcolor=colors['background'],
                            paper_bgcolor=colors['background'],
                            font={"color": colors['text']},
                            margin=dict(l=40, r=40, t=10, b=50),
                            xaxis=dict(
                                tickangle=-45,
                                tickmode='auto',
                                nticks=12
                            ),
                            yaxis=dict(title="Number of Registrations")
                        )
                    )
                )
            ], className="chart-container"),
            
            # Top RGM Performance
            html.Div([
                html.H3("Top RGM Performance", className="chart-title"),
                dcc.Graph(
                    id='rgm-performance-chart',
                    figure=go.Figure(
                        data=[
                            go.Bar(
                                name='Registration Rate',
                                y=metrics['rgm_metrics'].sort_values('Registration_Rate', ascending=False).head(5)['RGM'],
                                x=metrics['rgm_metrics'].sort_values('Registration_Rate', ascending=False).head(5)['Registration_Rate'],
                                orientation='h',
                                marker_color=colors['primary']
                            ),
                            go.Bar(
                                name='Active Rate',
                                y=metrics['rgm_metrics'].sort_values('Registration_Rate', ascending=False).head(5)['RGM'],
                                x=metrics['rgm_metrics'].sort_values('Registration_Rate', ascending=False).head(5)['Active_Rate'],
                                orientation='h',
                                marker_color=colors['tertiary']
                            ),
                            go.Bar(
                                name='Weekly Usage Rate',
                                y=metrics['rgm_metrics'].sort_values('Registration_Rate', ascending=False).head(5)['RGM'],
                                x=metrics['rgm_metrics'].sort_values('Registration_Rate', ascending=False).head(5)['Weekly_Rate'],
                                orientation='h',
                                marker_color=colors['accent3']
                            )
                        ],
                        layout=go.Layout(
                            barmode='group',
                            title="",
                            plot_bgcolor=colors['background'],
                            paper_bgcolor=colors['background'],
                            font={"color": colors['text']},
                            margin=dict(l=40, r=40, t=10, b=30),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            ),
                            xaxis=dict(title="Rate (%)"),
                            yaxis=dict(autorange="reversed")
                        )
                    )
                )
            ], className="chart-container")
        ], className="chart-row"),
        
        # Footer
        html.Div([
            html.P(f"Mobile Banking Analytics Dashboard v1.0 | Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
        ], className="footer")
    ], className="dashboard-container")
    
    # Add CSS to the app
    app.css.append_css({
        'external_url': 'https://cdnjs.cloudflare.com/ajax/libs/normalize/7.0.0/normalize.min.css'
    })
    
    # Custom CSS
    app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <style>
                /* Dashboard Container */
                .dashboard-container {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    max-width: 1800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }
                
                /* Header */
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                
                .dashboard-title {
                    color: #6b5b95;
                    margin-bottom: 5px;
                }
                
                .dashboard-date {
                    color: #666;
                    margin-top: 0;
                }
                
                /* Summary Row */
                .summary-row {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 20px;
                }
                
                /* Metric Card */
                .metric-card {
                    color: white;
                    border-radius: 8px;
                    padding: 15px;
                    width: calc(25% - 15px);
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                
                .metric-card h3 {
                    margin-top: 0;
                    margin-bottom: 10px;
                    font-size: 16px;
                    font-weight: 400;
                }
                
                .metric-card h2 {
                    margin: 0;
                    font-size: 28px;
                    font-weight: 600;
                }
                
                .metric-subtitle {
                    margin: 5px 0 0 0;
                    font-size: 14px;
                    opacity: 0.8;
                }
                
                /* Chart Rows */
                .chart-row {
                    display: flex;
                    margin-bottom: 20px;
                }
                
                /* Chart Container */
                .chart-container {
                    background-color: white;
                    border-radius: 8px;
                    padding: 15px;
                    width: calc(50% - 10px);
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    margin-right: 20px;
                    height: 450px;
                    display: flex;
                    flex-direction: column;
                }
                
                .chart-container:last-child {
                    margin-right: 0;
                }
                
                .chart-title {
                    color: #6b5b95;
                    margin-top: 0;
                    margin-bottom: 15px;
                    text-align: center;
                    font-size: 18px;
                }
                
                /* Onboarding Stats */
                .onboarding-stats-container {
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    padding-left: 20px;
                }
                
                .onboarding-stat {
                    margin-bottom: 20px;
                    text-align: center;
                }
                
                .onboarding-stat h4 {
                    margin: 0;
                    color: #666;
                    font-size: 14px;
                    font-weight: 400;
                }
                
                /* Footer */
                .footer {
                    text-align: center;
                    color: #666;
                    margin-top: 30px;
                    font-size: 12px;
                }
                
                /* Responsive Design */
                @media (max-width: 1200px) {
                    .summary-row {
                        flex-wrap: wrap;
                    }
                    
                    .metric-card {
                        width: calc(50% - 10px);
                        margin-bottom: 20px;
                    }
                    
                    .chart-row {
                        flex-direction: column;
                    }
                    
                    .chart-container {
                        width: 100%;
                        margin-right: 0;
                        margin-bottom: 20px;
                        height: 400px;
                    }
                }
                
                @media (max-width: 768px) {
                    .metric-card {
                        width: 100%;
                    }
                }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    '''
    
    return app

# Main function to run the dashboard
def main():
    """Main function to run the dashboard"""
    # Define the path to your Access database
    db_path = r'C:\Users\mehak.rafiq.ASKARIBANK\Documents\Projects\model_data\Daily_Dashboard_NTB\Data\Account_Holders_Weekly_be.accdb'
    
    # Check if CSVs directory exists
    csv_dir = './Data/CSVs'
    if not os.path.exists(csv_dir):
        print(f"Creating directory: {csv_dir}")
        os.makedirs(csv_dir, exist_ok=True)
    
    # Check if we have CSV files
    if not os.path.exists(os.path.join(csv_dir, 'NTB_Reg_Summary.csv')):
        print("CSV files not found. Loading data from Access database...")
        tables_data = load_data_from_access(db_path, csv_dir)
        if tables_data is None:
            print("Failed to load data from Access database.")
            return
    
    # Load data from CSVs
    print("Loading data from CSV files...")
    data = load_data_from_csvs(csv_dir)
    if data is None:
        print("Failed to load data from CSV files.")
        return
    
    # Process data and calculate metrics
    print("Processing data and calculating metrics...")
    processed_data = process_data(data)
    if processed_data is None:
        print("Failed to process data.")
        return
    
    metrics = calculate_summary_metrics(processed_data)
    
    # Create and launch the dashboard
    print("Creating dashboard...")
    app = create_dashboard(metrics)
    
    # Run the server
    print("Starting dashboard server...")
    app.run_server(debug=True)

if __name__ == "__main__":
    main()