"""
Year-to-Date (YTD) Preprocessor for Large Customer Data Files
This script optimizes large CSV files for YTD analysis
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, date
import argparse
import json

def create_ytd_optimized_file(input_file, output_dir='./ytd_data', reference_date=None):
    """
    Create optimized files for YTD analysis
    """
    print(f"Starting YTD preprocessing for: {input_file}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Set reference date
    if reference_date is None:
        reference_date = datetime.now().date()
    else:
        reference_date = datetime.strptime(reference_date, '%Y-%m-%d').date()
    
    reference_doy = reference_date.timetuple().tm_yday
    print(f"Reference date for YTD: {reference_date} (Day {reference_doy})")
    
    # Process file
    chunk_size = 50000
    ytd_data = {}
    summary_stats = {}
    total_rows = sum(1 for line in open(input_file, 'r', encoding='utf-8')) - 1
    print(f"Total rows to process: {total_rows:,}")
    
    rows_processed = 0
    
    for chunk_num, chunk in enumerate(pd.read_csv(input_file, chunksize=chunk_size)):
        # Convert dates
        chunk['AC_OPEN_DATE'] = pd.to_datetime(chunk['AC_OPEN_DATE'], errors='coerce')
        chunk['MOBILE_APP_REGISTRATION_DATE'] = pd.to_datetime(chunk['MOBILE_APP_REGISTRATION_DATE'], errors='coerce')
        
        # Add date components
        chunk['year'] = chunk['AC_OPEN_DATE'].dt.year
        chunk['month'] = chunk['AC_OPEN_DATE'].dt.month
        chunk['day_of_year'] = chunk['AC_OPEN_DATE'].dt.dayofyear
        
        # Calculate registration status
        chunk['is_registered'] = chunk['MOBILE_APP_REGISTRATION_DATE'].notna()
        chunk['days_to_register'] = (
            chunk['MOBILE_APP_REGISTRATION_DATE'] - chunk['AC_OPEN_DATE']
        ).dt.days
        
        # Process each year's YTD data
        for year in chunk['year'].dropna().unique():
            year = int(year)
            
            # Get YTD data for this year
            year_ytd = chunk[
                (chunk['year'] == year) & 
                (chunk['day_of_year'] <= reference_doy)
            ]
            
            if len(year_ytd) > 0:
                if year not in ytd_data:
                    ytd_data[year] = []
                    summary_stats[year] = {
                        'total_customers': 0,
                        'eligible': 0,
                        'registered': 0,
                        'by_month': {},
                        'by_region': {}
                    }
                
                ytd_data[year].append(year_ytd)
                
                # Update summary stats
                summary_stats[year]['total_customers'] += len(year_ytd)
                summary_stats[year]['eligible'] += (year_ytd['INET_ELIGIBLE'] == 'Y').sum()
                summary_stats[year]['registered'] += year_ytd['is_registered'].sum()
                
                # Monthly breakdown
                for month in year_ytd['month'].dropna().unique():
                    month = int(month)
                    if month not in summary_stats[year]['by_month']:
                        summary_stats[year]['by_month'][month] = 0
                    summary_stats[year]['by_month'][month] += len(year_ytd[year_ytd['month'] == month])
                
                # Regional breakdown
                for region in year_ytd['REGION_DESC'].dropna().unique():
                    if region not in summary_stats[year]['by_region']:
                        summary_stats[year]['by_region'][region] = {
                            'total': 0,
                            'registered': 0
                        }
                    region_data = year_ytd[year_ytd['REGION_DESC'] == region]
                    summary_stats[year]['by_region'][region]['total'] += len(region_data)
                    summary_stats[year]['by_region'][region]['registered'] += region_data['is_registered'].sum()
        
        # Progress update
        rows_processed += len(chunk)
        progress = rows_processed / total_rows * 100
        print(f"Progress: {progress:.1f}% ({rows_processed:,} / {total_rows:,} rows)", end='\r')
    
    print("\nSaving YTD data files...")
    
    # Save YTD data for each year
    for year, chunks in ytd_data.items():
        year_df = pd.concat(chunks, ignore_index=True)
        
        # Save full YTD data
        output_file = os.path.join(output_dir, f'ytd_{year}_to_{reference_date.strftime("%m%d")}.csv')
        year_df.to_csv(output_file, index=False)
        print(f"Saved {year} YTD data: {len(year_df):,} rows -> {output_file}")
    
    # Save summary statistics
    summary_file = os.path.join(output_dir, f'ytd_summary_{reference_date.strftime("%Y%m%d")}.json')
    with open(summary_file, 'w') as f:
        json.dump(summary_stats, f, indent=2)
    print(f"Saved summary statistics -> {summary_file}")
    
    # Create comparison file
    create_ytd_comparison_file(ytd_data, summary_stats, output_dir, reference_date)
    
    print("\n✅ YTD preprocessing complete!")
    return summary_stats


def create_ytd_comparison_file(ytd_data, summary_stats, output_dir, reference_date):
    """
    Create a consolidated comparison file for all years
    """
    print("\nCreating YTD comparison file...")
    
    # Create comparison dataframes
    comparison_data = []
    
    for year in sorted(summary_stats.keys()):
        # Overall metrics
        comparison_data.append({
            'Year': year,
            'Metric': 'Total_Customers',
            'Value': summary_stats[year]['total_customers']
        })
        comparison_data.append({
            'Year': year,
            'Metric': 'Eligible_Customers',
            'Value': summary_stats[year]['eligible']
        })
        comparison_data.append({
            'Year': year,
            'Metric': 'Registered_Customers',
            'Value': summary_stats[year]['registered']
        })
        
        # Calculate rates
        if summary_stats[year]['eligible'] > 0:
            reg_rate = summary_stats[year]['registered'] / summary_stats[year]['eligible'] * 100
            comparison_data.append({
                'Year': year,
                'Metric': 'Registration_Rate',
                'Value': round(reg_rate, 2)
            })
    
    comparison_df = pd.DataFrame(comparison_data)
    pivot_comparison = comparison_df.pivot(index='Metric', columns='Year', values='Value')
    
    # Calculate YoY growth
    years = sorted(summary_stats.keys())
    if len(years) >= 2:
        for i in range(1, len(years)):
            curr_year = years[i]
            prev_year = years[i-1]
            
            curr_total = summary_stats[curr_year]['total_customers']
            prev_total = summary_stats[prev_year]['total_customers']
            
            if prev_total > 0:
                growth = (curr_total - prev_total) / prev_total * 100
                pivot_comparison.loc[f'Growth_{prev_year}_to_{curr_year}', curr_year] = round(growth, 2)
    
    # Save comparison file
    comparison_file = os.path.join(output_dir, f'ytd_comparison_{reference_date.strftime("%Y%m%d")}.csv')
    pivot_comparison.to_csv(comparison_file)
    print(f"Saved comparison file -> {comparison_file}")
    
    # Create monthly comparison
    monthly_comparison = []
    for year, stats in summary_stats.items():
        for month, count in stats['by_month'].items():
            monthly_comparison.append({
                'Year': year,
                'Month': month,
                'Customers': count
            })
    
    monthly_df = pd.DataFrame(monthly_comparison)
    if not monthly_df.empty:
        monthly_pivot = monthly_df.pivot(index='Month', columns='Year', values='Customers').fillna(0)
        monthly_file = os.path.join(output_dir, f'ytd_monthly_comparison_{reference_date.strftime("%Y%m%d")}.csv')
        monthly_pivot.to_csv(monthly_file)
        print(f"Saved monthly comparison -> {monthly_file}")


def analyze_ytd_patterns(input_file, years_to_analyze=3, output_report='ytd_analysis_report.txt'):
    """
    Analyze YTD patterns and trends
    """
    print(f"\nAnalyzing YTD patterns for last {years_to_analyze} years...")
    
    # Get current date info
    current_date = datetime.now()
    current_doy = current_date.timetuple().tm_yday
    
    # Dictionary to store daily patterns
    daily_patterns = {}
    
    chunk_size = 50000
    for chunk in pd.read_csv(input_file, chunksize=chunk_size):
        chunk['AC_OPEN_DATE'] = pd.to_datetime(chunk['AC_OPEN_DATE'], errors='coerce')
        chunk['year'] = chunk['AC_OPEN_DATE'].dt.year
        chunk['day_of_year'] = chunk['AC_OPEN_DATE'].dt.dayofyear
        
        # Get recent years
        recent_years = sorted(chunk['year'].dropna().unique())[-years_to_analyze:]
        
        for year in recent_years:
            if year not in daily_patterns:
                daily_patterns[year] = {}
            
            year_data = chunk[chunk['year'] == year]
            daily_counts = year_data.groupby('day_of_year').size()
            
            for doy, count in daily_counts.items():
                if doy <= current_doy:  # Only YTD
                    if doy not in daily_patterns[year]:
                        daily_patterns[year][doy] = 0
                    daily_patterns[year][doy] += count
    
    # Generate report
    with open(output_report, 'w') as f:
        f.write(f"Year-to-Date Analysis Report\n")
        f.write(f"Generated: {current_date.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"YTD through day {current_doy} ({current_date.strftime('%B %d')})\n")
        f.write("="*60 + "\n\n")
        
        # YTD totals
        f.write("YTD Customer Acquisition Summary:\n")
        f.write("-"*40 + "\n")
        
        ytd_totals = {}
        for year, daily_data in sorted(daily_patterns.items()):
            total = sum(daily_data.values())
            ytd_totals[year] = total
            f.write(f"{year}: {total:,} customers\n")
        
        # Growth rates
        f.write("\nYear-over-Year Growth Rates:\n")
        f.write("-"*40 + "\n")
        
        years = sorted(ytd_totals.keys())
        for i in range(1, len(years)):
            curr_year = years[i]
            prev_year = years[i-1]
            
            growth = (ytd_totals[curr_year] - ytd_totals[prev_year]) / ytd_totals[prev_year] * 100
            f.write(f"{prev_year} → {curr_year}: {growth:+.1f}%\n")
        
        # Peak acquisition days
        f.write("\nPeak Customer Acquisition Days (YTD):\n")
        f.write("-"*40 + "\n")
        
        for year, daily_data in sorted(daily_patterns.items()):
            # Get top 5 days
            top_days = sorted(daily_data.items(), key=lambda x: x[1], reverse=True)[:5]
            f.write(f"\n{year}:\n")
            for doy, count in top_days:
                date = datetime(year, 1, 1) + pd.Timedelta(days=doy-1)
                f.write(f"  Day {doy} ({date.strftime('%b %d')}): {count:,} customers\n")
    
    print(f"Analysis report saved -> {output_report}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Preprocess data for YTD analysis')
    parser.add_argument('input_file', help='Path to the large CSV file')
    parser.add_argument('--output-dir', default='./ytd_data', 
                       help='Output directory for YTD files')
    parser.add_argument('--reference-date', default=None,
                       help='Reference date for YTD (YYYY-MM-DD). Default is today.')
    parser.add_argument('--analyze', action='store_true',
                       help='Perform YTD pattern analysis')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: File not found - {args.input_file}")
        exit(1)
    
    # Create YTD optimized files
    summary = create_ytd_optimized_file(
        args.input_file, 
        args.output_dir,
        args.reference_date
    )
    
    # Print summary
    print("\nYTD Summary:")
    for year in sorted(summary.keys()):
        print(f"\n{year}:")
        print(f"  Total customers: {summary[year]['total_customers']:,}")
        print(f"  Eligible: {summary[year]['eligible']:,}")
        print(f"  Registered: {summary[year]['registered']:,}")
        if summary[year]['eligible'] > 0:
            reg_rate = summary[year]['registered'] / summary[year]['eligible'] * 100
            print(f"  Registration rate: {reg_rate:.1f}%")
    
    # Optional: Analyze patterns
    if args.analyze:
        analyze_ytd_patterns(args.input_file)

# Example usage:
# python ytd_preprocessor.py "Customer-Level-Account Holder Detail Report.csv"
# python ytd_preprocessor.py "data.csv" --reference-date "2025-05-23"
# python ytd_preprocessor.py "data.csv" --analyze