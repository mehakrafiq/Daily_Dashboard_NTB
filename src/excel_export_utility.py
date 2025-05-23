import pandas as pd
import numpy as np
from io import BytesIO
import xlsxwriter
import plotly.graph_objects as go
import plotly.io as pio
from PIL import Image
import base64

class ExcelExporter:
    """
    Utility class for exporting dashboard data and charts to Excel
    """
    
    def __init__(self, filtered_data, all_data, figures, selected_year, selected_region):
        self.filtered_data = filtered_data
        self.all_data = all_data
        self.figures = figures
        self.selected_year = selected_year
        self.selected_region = selected_region
        self.output = BytesIO()
        
    def create_excel_report(self):
        """Main method to create the Excel report"""
        with pd.ExcelWriter(self.output, engine='xlsxwriter') as writer:
            self.workbook = writer.book
            
            # Create sheets
            self._create_summary_sheet(writer)
            self._create_data_sheets(writer)
            self._create_analysis_sheets(writer)
            self._create_comparison_sheets(writer)
            
        self.output.seek(0)
        return self.output
    
    def _create_summary_sheet(self, writer):
        """Create summary sheet with key metrics and charts"""
        summary_sheet = self.workbook.add_worksheet('Summary')
        writer.sheets['Summary'] = summary_sheet
        
        # Formats
        title_format = self.workbook.add_format({
            'bold': True, 
            'font_size': 18,
            'font_color': '#1f4788',
            'align': 'center'
        })
        
        header_format = self.workbook.add_format({
            'bold': True,
            'font_size': 14,
            'font_color': '#1f4788',
            'bottom': 2
        })
        
        metric_label_format = self.workbook.add_format({
            'bold': True,
            'font_size': 11,
            'bg_color': '#E8F0FE'
        })
        
        metric_value_format = self.workbook.add_format({
            'font_size': 11,
            'num_format': '#,##0'
        })
        
        percentage_format = self.workbook.add_format({
            'font_size': 11,
            'num_format': '0.0%'
        })
        
        # Title
        summary_sheet.merge_range('A1:H1', 
            f'iNET Mobile Banking Adoption Dashboard - {self.selected_year}', 
            title_format)
        
        # Key Metrics Section
        summary_sheet.write('A3', 'Key Performance Indicators', header_format)
        
        # Calculate metrics
        total_customers = len(self.filtered_data)
        inet_eligible = len(self.filtered_data[self.filtered_data['INET_ELIGIBLE'] == 'Y'])
        registered = len(self.filtered_data[self.filtered_data['iNET_Registration_status'] == 'Registered'])
        active_users = len(self.filtered_data[self.filtered_data['Activity_Status'].isin(['Weekly Active', 'Biweekly Active', 'Monthly Active'])])
        
        adoption_rate = registered / inet_eligible if inet_eligible > 0 else 0
        active_rate = active_users / registered if registered > 0 else 0
        
        # Write metrics in a grid layout
        metrics_data = [
            ['Total Customers', total_customers, 'iNET Eligible', inet_eligible],
            ['Registered Users', registered, 'Active Users (30d)', active_users],
            ['Adoption Rate', adoption_rate, 'Active User Rate', active_rate]
        ]
        
        row = 4
        for metric_row in metrics_data:
            summary_sheet.write(row, 0, metric_row[0], metric_label_format)
            if isinstance(metric_row[1], float) and metric_row[1] < 1:
                summary_sheet.write(row, 1, metric_row[1], percentage_format)
            else:
                summary_sheet.write(row, 1, metric_row[1], metric_value_format)
            
            summary_sheet.write(row, 3, metric_row[2], metric_label_format)
            if isinstance(metric_row[3], float) and metric_row[3] < 1:
                summary_sheet.write(row, 4, metric_row[3], percentage_format)
            else:
                summary_sheet.write(row, 4, metric_row[3], metric_value_format)
            row += 1
        
        # Regional Summary
        summary_sheet.write('A9', 'Regional Performance Summary', header_format)
        
        regional_summary = self.filtered_data.groupby('REGION_DESC').agg({
            'CUSTOMER_NO': 'count',
            'INET_ELIGIBLE': lambda x: (x == 'Y').sum(),
            'iNET_Registration_status': lambda x: (x == 'Registered').sum()
        }).rename(columns={
            'CUSTOMER_NO': 'Total',
            'INET_ELIGIBLE': 'Eligible',
            'iNET_Registration_status': 'Registered'
        })
        
        regional_summary['Adoption_Rate'] = regional_summary['Registered'] / regional_summary['Eligible']
        regional_summary = regional_summary.sort_values('Adoption_Rate', ascending=False)
        
        # Write regional summary
        row = 10
        col_headers = ['Region', 'Total Customers', 'Eligible', 'Registered', 'Adoption Rate']
        for col, header in enumerate(col_headers):
            summary_sheet.write(row, col, header, metric_label_format)
        
        row += 1
        for region, data in regional_summary.iterrows():
            summary_sheet.write(row, 0, region)
            summary_sheet.write(row, 1, data['Total'], metric_value_format)
            summary_sheet.write(row, 2, data['Eligible'], metric_value_format)
            summary_sheet.write(row, 3, data['Registered'], metric_value_format)
            summary_sheet.write(row, 4, data['Adoption_Rate'], percentage_format)
            row += 1
        
        # Adjust column widths
        summary_sheet.set_column('A:A', 20)
        summary_sheet.set_column('B:E', 15)
        
    def _create_data_sheets(self, writer):
        """Create sheets with raw and processed data"""
        # Filtered customer data
        self.filtered_data.to_excel(writer, sheet_name='Customer_Data', index=False)
        
        # Format the data sheet
        data_sheet = writer.sheets['Customer_Data']
        header_format = self.workbook.add_format({
            'bold': True,
            'bg_color': '#1f4788',
            'font_color': 'white',
            'align': 'center'
        })
        
        # Apply header format
        for col_num, value in enumerate(self.filtered_data.columns.values):
            data_sheet.write(0, col_num, value, header_format)
    
    def _create_analysis_sheets(self, writer):
        """Create detailed analysis sheets"""
        
        # 1. Onboarding Analysis
        onboarding_data = self.filtered_data[
            self.filtered_data['iNET_Registration_status'] == 'Registered'
        ].copy()
        
        if not onboarding_data.empty:
            # Regional onboarding stats
            regional_onboarding = onboarding_data.groupby('REGION_DESC')['days_to_onboard'].agg([
                'count', 'mean', 'median', 'std', 'min', 'max'
            ]).round(2)
            regional_onboarding.columns = ['Count', 'Mean_Days', 'Median_Days', 'Std_Dev', 'Min_Days', 'Max_Days']
            regional_onboarding.to_excel(writer, sheet_name='Onboarding_Analysis')
            
            # Onboarding time distribution
            time_dist = onboarding_data['onboarding_time_category'].value_counts()
            time_dist.to_excel(writer, sheet_name='Onboarding_Analysis', startrow=len(regional_onboarding) + 3)
        
        # 2. Activity Analysis
        activity_summary = pd.crosstab(
            self.filtered_data['REGION_DESC'],
            self.filtered_data['Activity_Status'],
            margins=True
        )
        activity_summary.to_excel(writer, sheet_name='Activity_Analysis')
        
        # 3. Funnel Analysis
        funnel_data = self._create_funnel_data()
        funnel_data.to_excel(writer, sheet_name='Funnel_Analysis', index=False)
    
    def _create_comparison_sheets(self, writer):
        """Create year-over-year comparison sheets"""
        if self.selected_year == 'All':
            # Get last two years for comparison
            years = sorted(self.all_data['AC_OPEN_YEAR'].dropna().unique())
            if len(years) >= 2:
                comparison_years = years[-2:]
                comparison_data = self.all_data[
                    self.all_data['AC_OPEN_YEAR'].isin(comparison_years)
                ]
                
                # Monthly comparison
                monthly_comp = comparison_data.groupby(['AC_OPEN_YEAR', 'AC_OPEN_MONTH']).agg({
                    'CUSTOMER_NO': 'count',
                    'iNET_Registration_status': lambda x: (x == 'Registered').sum()
                }).rename(columns={
                    'CUSTOMER_NO': 'Total_Accounts',
                    'iNET_Registration_status': 'Registered'
                })
                
                monthly_comp['Registration_Rate'] = (
                    monthly_comp['Registered'] / monthly_comp['Total_Accounts']
                ).round(4)
                
                # Pivot for easier comparison
                monthly_pivot = monthly_comp.unstack(level=0)
                monthly_pivot.to_excel(writer, sheet_name='YoY_Comparison')
    
    def _create_funnel_data(self):
        """Create funnel analysis data"""
        total = len(self.filtered_data)
        eligible = len(self.filtered_data[self.filtered_data['INET_ELIGIBLE'] == 'Y'])
        registered = len(self.filtered_data[self.filtered_data['iNET_Registration_status'] == 'Registered'])
        active_30 = len(self.filtered_data[self.filtered_data['Activity_Status'].isin(['Weekly Active', 'Biweekly Active', 'Monthly Active'])])
        weekly_active = len(self.filtered_data[self.filtered_data['Activity_Status'] == 'Weekly Active'])
        
        funnel_df = pd.DataFrame({
            'Stage': ['Total Customers', 'iNET Eligible', 'Registered', 'Active (30 days)', 'Weekly Active'],
            'Count': [total, eligible, registered, active_30, weekly_active],
            'Percentage_of_Total': [100, eligible/total*100, registered/total*100, active_30/total*100, weekly_active/total*100],
            'Conversion_Rate': [100, eligible/total*100, registered/eligible*100 if eligible > 0 else 0, 
                               active_30/registered*100 if registered > 0 else 0,
                               weekly_active/active_30*100 if active_30 > 0 else 0]
        })
        
        return funnel_df


def export_dashboard_to_excel(filtered_data, all_data, figures, selected_year, selected_region):
    """
    Main function to export dashboard to Excel
    """
    exporter = ExcelExporter(filtered_data, all_data, figures, selected_year, selected_region)
    return exporter.create_excel_report()