"""
Preprocessing script for large customer data CSV files
This script helps prepare large files for the iNET dashboard
"""

import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
import argparse

def preprocess_large_csv(input_file, output_dir='./processed_data'):
    """
    Process large CSV file and create smaller, manageable outputs
    """
    print(f"Starting to process: {input_file}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get file info
    file_size = os.path.getsize(input_file) / (1024**3)  # Size in GB
    print(f"File size: {file_size:.2f} GB")
    
    # Count total rows
    print("Counting rows...")
    total_rows = sum(1 for line in open(input_file, 'r', encoding='utf-8')) - 1
    print(f"Total rows: {total_rows:,}")
    
    # Read column names
    columns = pd.read_csv(input_file, nrows=0).columns.tolist()
    print(f"Columns found: {len(columns)}")
    
    # Option 1: Create yearly files
    print("\n📅 Creating yearly files...")
    create_yearly_files(input_file, output_dir, total_rows)
    
    # Option 2: Create sample file
    print("\n📊 Creating sample file...")
    create_sample_file(input_file, output_dir, sample_size=100000)
    
    # Option 3: Create summary statistics
    print("\n📈 Creating summary statistics...")
    create_summary_stats(input_file, output_dir)
    
    # Option 4: Create filtered file (last 2 years)
    print("\n🔍 Creating recent data file...")
    create_recent_data_file(input_file, output_dir)
    
    print("\n✅ Processing complete! Files saved in:", output_dir)


def create_yearly_files(input_file, output_dir, total_rows):
    """Split data by year"""
    chunk_size = 50000
    yearly_data = {}
    
    # Process in chunks
    for i, chunk in enumerate(pd.read_csv(input_file, chunksize=chunk_size)):
        # Convert date column
        chunk['AC_OPEN_DATE'] = pd.to_datetime(chunk['AC_OPEN_DATE'], errors='coerce')
        chunk['year'] = chunk['AC_OPEN_DATE'].dt.year
        
        # Group by year
        for year, year_data in chunk.groupby('year'):
            if pd.notna(year):
                if year not in yearly_data:
                    yearly_data[year] = []
                yearly_data[year].append(year_data.drop('year', axis=1))
        
        # Progress update
        processed = min((i + 1) * chunk_size, total_rows)
        print(f"  Processed {processed:,} / {total_rows:,} rows ({processed/total_rows*100:.1f}%)", end='\r')
    
    print()  # New line after progress
    
    # Save yearly files
    for year, data_list in yearly_data.items():
        year_df = pd.concat(data_list, ignore_index=True)
        output_file = os.path.join(output_dir, f'customer_data_{int(year)}.csv')
        year_df.to_csv(output_file, index=False)
        print(f"  Saved {int(year)}: {len(year_df):,} rows -> {output_file}")


def create_sample_file(input_file, output_dir, sample_size=100000):
    """Create a random sample of the data"""
    # Read random sample
    # First, get total rows
    total_rows = sum(1 for line in open(input_file, 'r', encoding='utf-8')) - 1
    
    # Calculate skip rows for random sampling
    if total_rows > sample_size:
        skip_rows = sorted(np.random.choice(range(1, total_rows), 
                                          total_rows - sample_size, 
                                          replace=False))
        df_sample = pd.read_csv(input_file, skiprows=skip_rows)
    else:
        df_sample = pd.read_csv(input_file)
    
    # Save sample
    output_file = os.path.join(output_dir, 'customer_data_sample.csv')
    df_sample.to_csv(output_file, index=False)
    print(f"  Saved sample: {len(df_sample):,} rows -> {output_file}")


def create_summary_stats(input_file, output_dir):
    """Create aggregated summary statistics"""
    chunk_size = 50000
    summary_data = []
    
    for chunk in pd.read_csv(input_file, chunksize=chunk_size):
        # Convert dates
        chunk['AC_OPEN_DATE'] = pd.to_datetime(chunk['AC_OPEN_DATE'], errors='coerce')
        chunk['MOBILE_APP_REGISTRATION_DATE'] = pd.to_datetime(chunk['MOBILE_APP_REGISTRATION_DATE'], errors='coerce')
        
        # Create month column
        chunk['year_month'] = chunk['AC_OPEN_DATE'].dt.to_period('M')
        
        # Aggregate by region and month
        summary = chunk.groupby(['REGION_DESC', 'year_month']).agg({
            'CUSTOMER_NO': 'count',
            'INET_ELIGIBLE': lambda x: (x == 'Y').sum(),
            'MOBILE_APP_REGISTRATION_DATE': lambda x: x.notna().sum(),
            'AGE': ['mean', 'median'],
            'CUSTOMER_MTD_AVERAGE_ALL_ACTIVE_ELIGIBLE': ['mean', 'median']
        }).reset_index()
        
        summary_data.append(summary)
    
    # Combine all summaries
    final_summary = pd.concat(summary_data, ignore_index=True)
    
    # Group again to get final aggregation
    final_summary = final_summary.groupby(['REGION_DESC', 'year_month']).sum().reset_index()
    
    # Save summary
    output_file = os.path.join(output_dir, 'customer_summary_stats.csv')
    final_summary.to_csv(output_file, index=False)
    print(f"  Saved summary statistics -> {output_file}")


def create_recent_data_file(input_file, output_dir, years_back=2):
    """Create file with only recent years data"""
    chunk_size = 50000
    recent_data = []
    cutoff_date = pd.Timestamp.now() - pd.DateOffset(years=years_back)
    
    for chunk in pd.read_csv(input_file, chunksize=chunk_size):
        # Convert date
        chunk['AC_OPEN_DATE'] = pd.to_datetime(chunk['AC_OPEN_DATE'], errors='coerce')
        
        # Filter recent data
        recent_chunk = chunk[chunk['AC_OPEN_DATE'] >= cutoff_date]
        if len(recent_chunk) > 0:
            recent_data.append(recent_chunk)
    
    # Combine and save
    if recent_data:
        final_recent = pd.concat(recent_data, ignore_index=True)
        output_file = os.path.join(output_dir, f'customer_data_last_{years_back}_years.csv')
        final_recent.to_csv(output_file, index=False)
        print(f"  Saved recent data: {len(final_recent):,} rows -> {output_file}")


def analyze_file_structure(input_file):
    """Quick analysis of file structure"""
    print("\n📋 File Structure Analysis:")
    
    # Read first 1000 rows
    df_sample = pd.read_csv(input_file, nrows=1000)
    
    print(f"\nColumns ({len(df_sample.columns)}):")
    for col in df_sample.columns:
        dtype = df_sample[col].dtype
        null_count = df_sample[col].isnull().sum()
        print(f"  - {col}: {dtype} (nulls: {null_count})")
    
    # Date columns
    date_cols = ['CIF_CREATION_DATE', 'CUSTOMER_RELATIONSHIP_DATE', 'AC_OPEN_DATE', 
                 'MOBILE_APP_REGISTRATION_DATE', 'LAST_TRX_DATE']
    
    print("\nDate ranges:")
    for col in date_cols:
        if col in df_sample.columns:
            try:
                dates = pd.to_datetime(df_sample[col], errors='coerce')
                print(f"  - {col}: {dates.min()} to {dates.max()}")
            except:
                pass
    
    # Memory estimate
    memory_per_row = df_sample.memory_usage(deep=True).sum() / len(df_sample)
    print(f"\nEstimated memory per row: {memory_per_row:.0f} bytes")
    
    total_rows = sum(1 for line in open(input_file, 'r', encoding='utf-8')) - 1
    estimated_memory = (memory_per_row * total_rows) / (1024**3)
    print(f"Estimated total memory needed: {estimated_memory:.2f} GB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Preprocess large customer CSV files')
    parser.add_argument('input_file', help='Path to the large CSV file')
    parser.add_argument('--output-dir', default='./processed_data', 
                       help='Output directory for processed files')
    parser.add_argument('--analyze-only', action='store_true',
                       help='Only analyze file structure without processing')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: File not found - {args.input_file}")
        sys.exit(1)
    
    if args.analyze_only:
        analyze_file_structure(args.input_file)
    else:
        preprocess_large_csv(args.input_file, args.output_dir)


# Example usage:
# python preprocess_large_csv.py "Customer-Level-Account Holder Detail Report -2603_Report2 (6).csv"
# python preprocess_large_csv.py "your_file.csv" --output-dir "./split_data"
# python preprocess_large_csv.py "your_file.csv" --analyze-only