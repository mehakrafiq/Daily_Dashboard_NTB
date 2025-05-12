fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly_data['Period'],
        y=monthly_data['Registrations'],
        mode='lines+markers',
        name='Registrations',
        line=dict(color=colors['primary'], width=3),
        marker=dict(size=8, color=colors['secondary'])
    ))
    
    fig.update_layout(
        height=400,
        margin=dict(l=40, r=40, t=10, b=60),
        plot_bgcolor='white',
        xaxis=dict(
            tickangle=-45,
            tickmode='array',
            tickvals=monthly_data['Period'],
            title="Month"
        ),
        yaxis=dict(title="Number of Registrations")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Calculate trend metrics
    if len(monthly_data) >= 3:
        last_month = monthly_data.iloc[-1]['Registrations']
        prev_month = monthly_data.iloc[-2]['Registrations']
        month_change = ((last_month - prev_month) / prev_month * 100) if prev_month > 0 else 0
        
        last_3_avg = monthly_data.iloc[-3:]['Registrations'].mean()
        prev_3_avg = monthly_data.iloc[-6:-3]['Registrations'].mean() if len(monthly_data) >= 6 else None
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Last Month Registrations", f"{last_month:,}", f"{month_change:.1f}% vs previous month")
        
        with col2:
            if prev_3_avg is not None:
                trend_3m = ((last_3_avg - prev_3_avg) / prev_3_avg * 100) if prev_3_avg > 0 else 0
                st.metric("3-Month Average", f"{last_3_avg:.0f}", f"{trend_3m:.1f}% vs previous 3 months")
            else:
                st.metric("3-Month Average", f"{last_3_avg:.0f}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_cohort_analysis(metrics):
    """Display cohort analysis"""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">Monthly Cohort Analysis</div>', unsafe_allow_html=True)
    
    # Get the data and take only the last 12 months
    cohort_data = metrics['monthly_cohorts'].tail(12).copy()
    
    # Create a heatmap for 30-day and 90-day registration rates
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("30-Day Registration Rate")
        
        fig = go.Figure(data=go.Heatmap(
            z=cohort_data['30d_Registration_Rate'],
            x=cohort_data['Cohort_Month'],
            y=['Rate'],
            colorscale='Blues',
            showscale=True,
            text=[[f"{x:.1f}%" for x in cohort_data['30d_Registration_Rate']]],
            texttemplate="%{text}",
            textfont={"size":12},
        ))
        
        fig.update_layout(
            height=200,
            margin=dict(l=40, r=40, t=10, b=60),
            xaxis=dict(tickangle=-45)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("90-Day Registration Rate")
        
        fig = go.Figure(data=go.Heatmap(
            z=cohort_data['90d_Registration_Rate'],
            x=cohort_data['Cohort_Month'],
            y=['Rate'],
            colorscale='Greens',
            showscale=True,
            text=[[f"{x:.1f}%" for x in cohort_data['90d_Registration_Rate']]],
            texttemplate="%{text}",
            textfont={"size":12},
        ))
        
        fig.update_layout(
            height=200,
            margin=dict(l=40, r=40, t=10, b=60),
            xaxis=dict(tickangle=-45)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Line chart to show registration rate trends
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=cohort_data['Cohort_Month'],
        y=cohort_data['30d_Registration_Rate'],
        mode='lines+markers',
        name='30-Day Rate',
        line=dict(color=colors['primary'], width=2),
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=cohort_data['Cohort_Month'],
        y=cohort_data['90d_Registration_Rate'],
        mode='lines+markers',
        name='90-Day Rate',
        line=dict(color=colors['tertiary'], width=2),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=40, r=40, t=10, b=60),
        plot_bgcolor='white',
        xaxis=dict(
            tickangle=-45,
            title="Account Opening Month"
        ),
        yaxis=dict(title="Registration Rate (%)"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Data table with cohort data
    with st.expander("View Cohort Data"):
        st.dataframe(cohort_data)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_rgm_performance(metrics):
    """Display RGM performance"""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">RGM Performance</div>', unsafe_allow_html=True)
    
    # Get top 10 RGMs by registration rate
    top_rgms = metrics['rgm_metrics'].sort_values('Registration_Rate', ascending=False).head(10)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Registration Rate',
        y=top_rgms['RGM'],
        x=top_rgms['Registration_Rate'],
        orientation='h',
        marker_color=colors['primary']
    ))
    
    fig.add_trace(go.Bar(
        name='Active Rate',
        y=top_rgms['RGM'],
        x=top_rgms['Active_Rate'],
        orientation='h',
        marker_color=colors['tertiary']
    ))
    
    fig.add_trace(go.Bar(
        name='Weekly Usage Rate',
        y=top_rgms['RGM'],
        x=top_rgms['Weekly_Rate'],
        orientation='h',
        marker_color=colors['accent3']
    ))
    
    fig.update_layout(
        barmode='group',
        height=500,
        margin=dict(l=40, r=40, t=10, b=40),
        plot_bgcolor='white',
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
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Data table with RGM data
    with st.expander("View RGM Performance Data"):
        st.dataframe(metrics['rgm_metrics'].sort_values('Registration_Rate', ascending=False))
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_report_generation(metrics, processed_data):
    """Display report generation section"""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">Generate Reports</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Excel report generation
        st.subheader("Excel Report")
        if st.button("Generate Excel Report"):
            with st.spinner("Generating Excel report..."):
                excel_data = generate_excel_report(metrics, processed_data)
                b64 = base64.b64encode(excel_data).decode()
                dl_link = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="Mobile_Banking_Report.xlsx">Download Excel Report</a>'
                st.markdown(dl_link, unsafe_allow_html=True)
    
    with col2:
        # Chart export options
        st.subheader("Export Charts")
        chart_type = st.selectbox("Select chart to export:", [
            "Customer Journey Funnel",
            "Login Frequency Distribution",
            "Regional Performance",
            "Onboarding Time Distribution",
            "Monthly Registration Trends",
            "RGM Performance"
        ])
        
        if st.button("Generate Chart"):
            with st.spinner("Generating chart..."):
                if chart_type == "Customer Journey Funnel":
                    fig = go.Figure(
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
                        )]
                    )
                
                elif chart_type == "Login Frequency Distribution":
                    fig = go.Figure(
                        data=[go.Bar(
                            x=metrics['login_frequency']['Frequency'],
                            y=metrics['login_frequency']['Count'],
                            marker_color=[
                                colors['accent3'],      # Weekly
                                colors['secondary'],    # Monthly
                                colors['accent4'],      # Quarterly
                                colors['warning'],      # Inactive
                                colors['gray'],         # No Login
                                colors['accent2']       # Not Registered
                            ]
                        )]
                    )
                
                elif chart_type == "Regional Performance":
                    region_metrics = metrics['region_metrics'].sort_values('Registration_Rate', ascending=True)
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        name='Registration Rate',
                        y=region_metrics['REGION_DESC'],
                        x=region_metrics['Registration_Rate'],
                        orientation='h',
                        marker_color=colors['primary']
                    ))
                    fig.add_trace(go.Bar(
                        name='Activation Rate',
                        y=region_metrics['REGION_DESC'],
                        x=region_metrics['Activation_Rate'],
                        orientation='h',
                        marker_color=colors['tertiary']
                    ))
                    fig.update_layout(barmode='group')
                
                elif chart_type == "Onboarding Time Distribution":
                    fig = px.pie(
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
                    )
                
                elif chart_type == "Monthly Registration Trends":
                    monthly_data = metrics['monthly_trends'].copy()
                    monthly_data['Period'] = monthly_data['Registration_Month'].astype(str)
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=monthly_data['Period'],
                        y=monthly_data['Registrations'],
                        mode='lines+markers',
                        name='Registrations',
                        line=dict(color=colors['primary'], width=3),
                        marker=dict(size=8, color=colors['secondary'])
                    ))
                
                elif chart_type == "RGM Performance":
                    top_rgms = metrics['rgm_metrics'].sort_values('Registration_Rate', ascending=False).head(10)
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        name='Registration Rate',
                        y=top_rgms['RGM'],
                        x=top_rgms['Registration_Rate'],
                        orientation='h',
                        marker_color=colors['primary']
                    ))
                    fig.add_trace(go.Bar(
                        name='Active Rate',
                        y=top_rgms['RGM'],
                        x=top_rgms['Active_Rate'],
                        orientation='h',
                        marker_color=colors['tertiary']
                    ))
                    fig.update_layout(barmode='group')
                
                # Set common layout parameters
                fig.update_layout(
                    title=chart_type,
                    height=600,
                    width=800,
                    margin=dict(l=40, r=40, t=40, b=60),
                    plot_bgcolor='white',
                )
                
                # Convert to image
                img_bytes = fig.to_image(format="png", engine="kaleido")
                b64 = base64.b64encode(img_bytes).decode()
                dl_link = f'<a href="data:image/png;base64,{b64}" download="{chart_type.replace(" ", "_")}.png">Download {chart_type} Image</a>'
                st.markdown(dl_link, unsafe_allow_html=True)
                
                # Display the chart
                st.plotly_chart(fig)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_data_explorer(processed_data):
    """Display data explorer section"""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">Data Explorer</div>', unsafe_allow_html=True)
    
    df = processed_data['ntb_reg_tbl_df']
    
    # Show data filtering options
    st.subheader("Filter Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if 'REGION_DESC' in df.columns:
            regions = ['All'] + sorted(df['REGION_DESC'].unique().tolist())
            region_filter = st.selectbox("Region:", regions)
    
    with col2:
        if 'AREA' in df.columns:
            areas = ['All'] + sorted(df['AREA'].unique().tolist())
            area_filter = st.selectbox("Area:", areas)
    
    with col3:
        if 'RGM' in df.columns:
            rgms = ['All'] + sorted(df['RGM'].unique().tolist())
            rgm_filter = st.selectbox("RGM:", rgms)
    
    # Apply filters
    filtered_df = df.copy()
    
    if 'region_filter' in locals() and region_filter != 'All':
        filtered_df = filtered_df[filtered_df['REGION_DESC'] == region_filter]
    
    if 'area_filter' in locals() and area_filter != 'All':
        filtered_df = filtered_df[filtered_df['AREA'] == area_filter]
    
    if 'rgm_filter' in locals() and rgm_filter != 'All':
        filtered_df = filtered_df[filtered_df['RGM'] == rgm_filter]
    
    # Show summary of filtered data
    st.subheader("Filtered Data Summary")
    
    # Calculate key metrics on filtered data
    total_filtered = len(filtered_df)
    registered_filtered = filtered_df['Registration_Remarks'].isin(['Registered', 'Already Registered']).sum()
    registration_rate_filtered = registered_filtered / total_filtered * 100 if total_filtered > 0 else 0
    
    active_30_days_filtered = (filtered_df['Login_Bracket'] == 'Last 30 Days').sum()
    active_rate_filtered = active_30_days_filtered / registered_filtered * 100 if registered_filtered > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Accounts", f"{total_filtered:,}")
    
    with col2:
        st.metric("Registered Accounts", f"{registered_filtered:,}", f"{registration_rate_filtered:.1f}%")
    
    with col3:
        st.metric("Active 30 Days", f"{active_30_days_filtered:,}", f"{active_rate_filtered:.1f}%")
    
    # Show data table with filtered data
    st.subheader("Filtered Data")
    
    # Select columns to display
    if len(filtered_df.columns) > 10:
        default_columns = ['CUSTOMER_NO', 'CUST_AC_NO', 'REGION_DESC', 'BRANCH_NAME', 'Open_Date_', 
                         'Registration_Date', 'Last_Login_Date', 'Login_Bracket', 'Login_Frequency', 
                         'Days_to_Onboard', 'Onboarding_Time_Bracket']
        available_columns = filtered_df.columns.tolist()
        
        # Only keep default columns that exist in the dataframe
        default_columns = [col for col in default_columns if col in available_columns]
        
        selected_columns = st.multiselect("Select columns to display:", 
                                         available_columns, 
                                         default=default_columns)
        
        if selected_columns:
            display_df = filtered_df[selected_columns]
        else:
            display_df = filtered_df
    else:
        display_df = filtered_df
    
    # Allow download of filtered data
    if not display_df.empty:
        csv = display_df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        download_link = f'<a href="data:file/csv;base64,{b64}" download="filtered_data.csv">Download filtered data as CSV</a>'
        st.markdown(download_link, unsafe_allow_html=True)
        
        # Display the table
        st.dataframe(display_df)
    else:
        st.warning("No data matching the selected filters.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main Streamlit app
def main():
    # Initialize session state if needed
    if 'raw_data' not in st.session_state:
        st.session_state.raw_data = None
    
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    
    if 'metrics' not in st.session_state:
        st.session_state.metrics = None# Streamlit app functions
def app_header():
    """Display app header and description"""
    st.set_page_config(
        page_title="Mobile Banking Analytics",
        page_icon="📱",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    st.markdown(
        """
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #6b5b95;
            text-align: center;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.1rem;
            color: #666;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-container {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        .metric-label {
            font-size: 1rem;
            color: #6b5b95;
            margin-bottom: 0.5rem;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: bold;
            color: #333;
        }
        .metric-subtext {
            font-size: 0.8rem;
            color: #666;
            margin-top: 0.2rem;
        }
        .chart-container {
            background-color: white;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
        }
        .chart-title {
            font-size: 1.2rem;
            color: #6b5b95;
            margin-bottom: 1rem;
            text-align: center;
        }
        .tab-content {
            padding: 1rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown('<h1 class="main-header">Mobile Banking Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Comprehensive analytics for monitoring mobile banking adoption and usage</p>', unsafe_allow_html=True)

def display_loading_section():
    """Display the data loading section"""
    st.sidebar.title("Data Loading")
    
    data_option = st.sidebar.radio(
        "Choose data source:",
        ["Load from CSV files", "Connect to Access Database"]
    )
    
    if data_option == "Connect to Access Database":
        st.sidebar.warning("To connect to an Access database, you need pyodbc installed and MS Access ODBC drivers.")
        db_path = st.sidebar.text_input("Enter Access database path:", value=r"C:\path\to\your\database.accdb")
        load_button = st.sidebar.button("Load from Database")
        
        if load_button:
            data = load_data_from_access(db_path)
            if data is not None:
                st.session_state.raw_data = data
                st.session_state.processed_data = process_data(data)
                st.session_state.metrics = calculate_summary_metrics(st.session_state.processed_data)
                st.sidebar.success("Data loaded and processed successfully!")
                st.experimental_rerun()
    else:
        csv_dir = st.sidebar.text_input("CSV files directory:", value="./Data/CSVs")
        load_button = st.sidebar.button("Load from CSV")
        
        if load_button:
            data = load_data_from_csvs(csv_dir)
            if data is not None:
                st.session_state.raw_data = data
                st.session_state.processed_data = process_data(data)
                st.session_state.metrics = calculate_summary_metrics(st.session_state.processed_data)
                st.sidebar.success("Data loaded and processed successfully!")
                st.experimental_rerun()
    
    # Check if we need to show an upload option for CSV file
    show_upload = st.sidebar.checkbox("Upload CSV file directly", value=False)
    
    if show_upload:
        uploaded_file = st.sidebar.file_uploader("Upload NTB_Reg_Summary.csv", type="csv")
        if uploaded_file is not None:
            try:
                # Create directory if it doesn't exist
                os.makedirs("./Data/CSVs", exist_ok=True)
                
                # Save the uploaded file
                with open(os.path.join("./Data/CSVs", "NTB_Reg_Summary.csv"), "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Load data
                data = {'ntb_reg_tbl_df': pd.read_csv(uploaded_file)}
                
                # Process data
                st.session_state.raw_data = data
                st.session_state.processed_data = process_data(data)
                st.session_state.metrics = calculate_summary_metrics(st.session_state.processed_data)
                
                st.sidebar.success("File uploaded and processed successfully!")
                st.experimental_rerun()
            except Exception as e:
                st.sidebar.error(f"Error processing file: {e}")

def display_summary_metrics(metrics):
    """Display summary metrics in top row"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Total Accounts</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{metrics["summary"]["Total_Accounts"]:,}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Registered Accounts</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{metrics["summary"]["Registered_Accounts"]:,}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-subtext">{metrics["summary"]["Registration_Rate"]:.1f}% of total</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Active Users (30 Days)</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{metrics["summary"]["Active_30_Days"]:,}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-subtext">{metrics["summary"]["Active_Rate"]:.1f}% of registered</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Avg Days to Onboard</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-value">{metrics["summary"]["Avg_Days_to_Onboard"]:.1f}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-subtext">Quick onboarding: {metrics["summary"]["Quick_Onboarding_Rate"]:.1f}%</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def display_customer_journey(metrics):
    """Display customer journey funnel"""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">Customer Journey Funnel</div>', unsafe_allow_html=True)
    
    fig = go.Figure(
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
        )]
    )
    
    fig.update_layout(
        height=400,
        margin=dict(l=40, r=40, t=10, b=40),
        plot_bgcolor='white',
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display conversion rates
    col1, col2, col3 = st.columns(3)
    
    with col1:
        conversion_rate = metrics['customer_journey']['Conversion_Rate'][1]
        st.metric("Registration Rate", f"{conversion_rate:.1f}%", 
                 delta=f"{conversion_rate - 50:.1f}pp vs target" if conversion_rate - 50 != 0 else None)
    
    with col2:
        conversion_rate = metrics['customer_journey']['Conversion_Rate'][2]
        st.metric("Activation Rate", f"{conversion_rate:.1f}%", 
                 delta=f"{conversion_rate - 60:.1f}pp vs target" if conversion_rate - 60 != 0 else None)
    
    with col3:
        conversion_rate = metrics['customer_journey']['Conversion_Rate'][3]
        st.metric("Weekly Usage Rate", f"{conversion_rate:.1f}%", 
                 delta=f"{conversion_rate - 40:.1f}pp vs target" if conversion_rate - 40 != 0 else None)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_login_frequency(metrics):
    """Display login frequency chart"""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">Login Frequency Distribution</div>', unsafe_allow_html=True)
    
    fig = go.Figure(
        data=[go.Bar(
            x=metrics['login_frequency']['Frequency'],
            y=metrics['login_frequency']['Count'],
            marker_color=[
                colors['accent3'],      # Weekly
                colors['secondary'],    # Monthly
                colors['accent4'],      # Quarterly
                colors['warning'],      # Inactive
                colors['gray'],         # No Login
                colors['accent2']       # Not Registered
            ]
        )]
    )
    
    fig.update_layout(
        height=400,
        margin=dict(l=40, r=40, t=10, b=40),
        plot_bgcolor='white',
        yaxis_title="Number of Users"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add key metrics below the chart
    col1, col2 = st.columns(2)
    
    with col1:
        weekly_pct = metrics['summary']['Weekly_Users'] / metrics['summary']['Total_Accounts'] * 100
        st.metric("Weekly Active Users %", f"{weekly_pct:.1f}%", 
                 delta=f"{weekly_pct - 15:.1f}pp vs target" if weekly_pct - 15 != 0 else None)
    
    with col2:
        monthly_pct = metrics['summary']['Monthly_Users'] / metrics['summary']['Total_Accounts'] * 100
        st.metric("Monthly Active Users %", f"{monthly_pct:.1f}%", 
                 delta=f"{monthly_pct - 25:.1f}pp vs target" if monthly_pct - 25 != 0 else None)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_regional_performance(metrics):
    """Display regional performance chart"""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">Regional Performance</div>', unsafe_allow_html=True)
    
    # Sort by registration rate
    region_metrics = metrics['region_metrics'].sort_values('Registration_Rate', ascending=True)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Registration Rate',
        y=region_metrics['REGION_DESC'],
        x=region_metrics['Registration_Rate'],
        orientation='h',
        marker_color=colors['primary']
    ))
    
    fig.add_trace(go.Bar(
        name='Activation Rate',
        y=region_metrics['REGION_DESC'],
        x=region_metrics['Activation_Rate'],
        orientation='h',
        marker_color=colors['tertiary']
    ))
    
    fig.update_layout(
        barmode='group',
        height=500,
        margin=dict(l=40, r=40, t=10, b=40),
        plot_bgcolor='white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(title="Rate (%)"),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add a data table with more detailed metrics
    with st.expander("Regional Performance Data"):
        st.dataframe(region_metrics.sort_values('Registration_Rate', ascending=False))
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_onboarding_distribution(metrics):
    """Display onboarding time distribution"""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">Onboarding Time Distribution</div>', unsafe_allow_html=True)
    
    fig = px.pie(
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
    )
    
    fig.update_layout(
        height=400,
        margin=dict(l=40, r=40, t=10, b=40),
        legend=dict(orientation="h"),
        plot_bgcolor='white',
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Add metrics below chart
    col1, col2, col3 = st.columns(3)
    
    with col1:
        already_registered = metrics['summary']['Already_Registered']
        already_registered_pct = already_registered / metrics['summary']['Total_Accounts'] * 100
        st.metric("Already Registered", f"{already_registered:,}", f"{already_registered_pct:.1f}% of total")
    
    with col2:
        quick_onboarding = metrics['summary']['Quick_Onboarding_Rate']
        st.metric("Quick Onboarding (≤10 days)", f"{quick_onboarding:.1f}%", 
                 delta=f"{quick_onboarding - 30:.1f}pp vs target" if quick_onboarding - 30 != 0 else None)
    
    with col3:
        avg_days = metrics['summary']['Avg_Days_to_Onboard']
        st.metric("Avg Days to Onboard", f"{avg_days:.1f}", 
                 delta=f"{30 - avg_days:.1f} days vs target" if 30 - avg_days != 0 else None, 
                 delta_color="inverse")
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_monthly_trends(metrics):
    """Display monthly registration trends"""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown('<div class="chart-title">Monthly Registration Trends</div>', unsafe_allow_html=True)
    
    # Convert period to string for plotting
    monthly_data = metrics['monthly_trends'].copy()
    monthly_data['Period'] = monthly_data['Registration_Month'].astype(str)
    
    fig =import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging
import datetime
import io
import base64
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'streamlit_app_{datetime.datetime.now().strftime("%Y%m%d")}.log')
    ]
)

logger = logging.getLogger('MobileBankingStreamlitApp')

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
    try:
        import pyodbc
        logger.info(f"Connecting to Access database: {db_path}")
        st.info(f"Connecting to Access database: {db_path}")
        
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
                logger.info(f"Found {len(table_names)} tables in the database")
                
                # Load each table into a Pandas DataFrame and save as CSV
                tables_data = {}
                progress_bar = st.progress(0)
                progress_text = st.empty()
                
                for i, table_name in enumerate(table_names):
                    progress_text.text(f"Loading table: {table_name}")
                    logger.info(f"Loading table: {table_name}")
                    query = f"SELECT * FROM [{table_name}]"
                    tables_data[table_name] = pd.read_sql(query, conn)
                    csv_path = os.path.join(csv_output_dir, f"{table_name}.csv")
                    tables_data[table_name].to_csv(csv_path, index=False)
                    logger.info(f"Saved {table_name} with {len(tables_data[table_name])} rows to {csv_path}")
                    
                    # Update progress
                    progress = (i + 1) / len(table_names)
                    progress_bar.progress(progress)
                    progress_text.text(f"Loaded {i+1}/{len(table_names)} tables")
                
                progress_bar.empty()
                progress_text.empty()
                st.success(f"Successfully loaded {len(table_names)} tables from the database")
                return tables_data
        
        except pyodbc.Error as e:
            error_msg = f"Database connection error: {e}"
            logger.error(error_msg)
            st.error(error_msg)
            return None
        except Exception as e:
            error_msg = f"Error: {e}"
            logger.error(error_msg)
            st.error(error_msg)
            return None
            
    except ImportError:
        error_msg = "pyodbc module not found. Please install it to connect to Access databases."
        logger.error(error_msg)
        st.error(error_msg)
        return None

# Function to load data from CSVs
def load_data_from_csvs(csv_dir='./Data/CSVs'):
    """Load data from CSV files"""
    data = {}
    
    try:
        logger.info(f"Loading data from CSV files in {csv_dir}")
        
        # Create directory if it doesn't exist
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir, exist_ok=True)
            logger.info(f"Created directory: {csv_dir}")
        
        # Check for main data file
        ntb_reg_csv_path = os.path.join(csv_dir, 'NTB_Reg_Summary.csv')
        if os.path.exists(ntb_reg_csv_path):
            data['ntb_reg_tbl_df'] = pd.read_csv(ntb_reg_csv_path)
            logger.info(f"Loaded NTB_Reg_Summary.csv with {len(data['ntb_reg_tbl_df'])} records")
            
            # Try to load other CSV files if they exist
            other_tables = []
            for table_name in ['acct_class', 'Acct_holders_tbl', 'Branch_converter_islamic', 
                              'Branch_tbl', 'NTB_DB', 'RGM_tbl']:
                file_path = os.path.join(csv_dir, f"{table_name}.csv")
                if os.path.exists(file_path):
                    data[table_name] = pd.read_csv(file_path)
                    logger.info(f"Loaded {table_name}.csv with {len(data[table_name])} records")
                    other_tables.append(table_name)
            
            if other_tables:
                logger.info(f"Additionally loaded tables: {', '.join(other_tables)}")
            
            return data
        else:
            logger.warning(f"Main data file not found: {ntb_reg_csv_path}")
            return None
    
    except Exception as e:
        error_msg = f"Error loading data: {e}"
        logger.error(error_msg)
        st.error(error_msg)
        return None

# Process the data and calculate metrics
def process_data(data):
    """Process the data and prepare metrics"""
    if data is None or 'ntb_reg_tbl_df' not in data:
        logger.error("No data to process")
        return None
    
    logger.info("Starting data processing...")
    ntb_reg_tbl_df = data['ntb_reg_tbl_df'].copy()
    
    # Convert date columns to datetime
    date_columns = ['Registration_Date', 'Open_Date_', 'Last_Login_Date']
    for col in date_columns:
        if col in ntb_reg_tbl_df.columns:
            logger.info(f"Converting column {col} to datetime")
            ntb_reg_tbl_df[col] = pd.to_datetime(ntb_reg_tbl_df[col], errors='coerce')
    
    # 1. Update Registration_Remarks for accounts where Registration_Date is older than Open_Date
    logger.info("Identifying 'Already Registered' accounts...")
    older_reg_mask = ntb_reg_tbl_df['Registration_Date'] < ntb_reg_tbl_df['Open_Date_']
    ntb_reg_tbl_df.loc[older_reg_mask, 'Registration_Remarks'] = 'Already Registered'
    num_updates = older_reg_mask.sum()
    logger.info(f"Number of records updated to 'Already Registered': {num_updates} ({num_updates/len(ntb_reg_tbl_df)*100:.2f}%)")
    
    # 2. Calculate Login Bracket
    logger.info("Calculating Login Brackets...")
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
    
    # 3. Calculate Days to Onboard
    logger.info("Calculating Days to Onboard...")
    valid_onboarding_mask = (
        (ntb_reg_tbl_df['Registration_Remarks'] != 'Already Registered') & 
        (~ntb_reg_tbl_df['Registration_Date'].isna()) & 
        (~ntb_reg_tbl_df['Open_Date_'].isna()) & 
        (ntb_reg_tbl_df['Registration_Date'] >= ntb_reg_tbl_df['Open_Date_'])
    )
    
    ntb_reg_tbl_df.loc[valid_onboarding_mask, 'Days_to_Onboard'] = (
        ntb_reg_tbl_df.loc[valid_onboarding_mask, 'Registration_Date'] - 
        ntb_reg_tbl_df.loc[valid_onboarding_mask, 'Open_Date_']
    ).dt.days
    
    # 4. Calculate Login Frequency
    logger.info("Creating Login Frequency categories...")
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
    
    # 5. Calculate Onboarding Time Brackets
    logger.info("Creating Onboarding Time Brackets...")
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
    
    # 6. Add Open_Month for cohort analysis
    logger.info("Adding Open_Month for cohort analysis...")
    ntb_reg_tbl_df['Open_Month'] = pd.to_datetime(ntb_reg_tbl_df['Open_Date_']).dt.to_period('M')
    
    # 7. Add Registration_Month for trend analysis
    logger.info("Adding Registration_Month for trend analysis...")
    ntb_reg_tbl_df['Registration_Month'] = pd.to_datetime(ntb_reg_tbl_df['Registration_Date']).dt.to_period('M')
    
    logger.info("Data processing complete.")
    return {
        'ntb_reg_tbl_df': ntb_reg_tbl_df,
        **data
    }

# Calculate summary metrics
def calculate_summary_metrics(processed_data):
    """Calculate summary metrics for dashboard"""
    if processed_data is None or 'ntb_reg_tbl_df' not in processed_data:
        logger.error("No processed data to calculate metrics")
        return None
    
    logger.info("Calculating summary metrics...")
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
    login_frequency_dist = ntb_reg_tbl_df['Login_Frequency'].value_counts().reset_index()
    login_frequency_dist.columns = ['Frequency', 'Count']
    
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
    monthly_reg = ntb_reg_tbl_df.groupby('Registration_Month').size().reset_index(name='Registrations')
    monthly_reg['Year'] = monthly_reg['Registration_Month'].dt.year
    monthly_reg['Month'] = monthly_reg['Registration_Month'].dt.month
    monthly_reg = monthly_reg.sort_values(['Year', 'Month'])
    
    # Onboarding time distribution
    onboarding_dist = ntb_reg_tbl_df['Onboarding_Time_Bracket'].value_counts().reset_index()
    onboarding_dist.columns = ['Bracket', 'Count']
    
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
    
    # Monthly Cohort Analysis
    monthly_cohorts = []
    
    for month in sorted(ntb_reg_tbl_df['Open_Month'].unique()):
        cohort = ntb_reg_tbl_df[ntb_reg_tbl_df['Open_Month'] == month]
        
        metrics = {
            'Cohort_Month': str(month),
            'Total_Accounts': len(cohort),
            'Registered_30d': cohort[
                (cohort['Registration_Date'].notna()) & 
                ((cohort['Registration_Date'] - cohort['Open_Date_']).dt.days <= 30)
            ].shape[0],
            'Registered_90d': cohort[
                (cohort['Registration_Date'].notna()) & 
                ((cohort['Registration_Date'] - cohort['Open_Date_']).dt.days <= 90)
            ].shape[0]
        }
        
        monthly_cohorts.append(metrics)
    
    monthly_cohort_df = pd.DataFrame(monthly_cohorts)
    monthly_cohort_df['30d_Registration_Rate'] = (monthly_cohort_df['Registered_30d'] / monthly_cohort_df['Total_Accounts'] * 100).round(1)
    monthly_cohort_df['90d_Registration_Rate'] = (monthly_cohort_df['Registered_90d'] / monthly_cohort_df['Total_Accounts'] * 100).round(1)
    
    logger.info("Finished calculating all metrics")
    
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
        'onboarding_dist': onboarding_dist,
        'monthly_cohorts': monthly_cohort_df
    }