# Large Customer Data File Processing
# This notebook helps you work with files > 200MB

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os
import gc

# File path - update this to your file location
FILE_PATH = r"C:\Users\mehak.rafiq.ASKARIBANK\Documents\Projects\model_data\Daily_Dashboard_NTB\Data\Customer-Level-Account Holder Detail Report -2603_Report2 (6).csv"

#%% [markdown]
# ## 1. Quick File Analysis

#%%
# Check file size
file_size_mb = os.path.getsize(FILE_PATH) / (1024**2)
print(f"File size: {file_size_mb:.2f} MB")

# Count rows without loading entire file
print("Counting rows...")
row_count = sum(1 for line in open(FILE_PATH, 'r', encoding='utf-8')) - 1
print(f"Total rows: {row_count:,}")

#%% [markdown]
# ## 2. Option A: Create Smaller Sample File

#%%
# Create a 100k row sample for dashboard
sample_size = 100000
print(f"Creating sample with {sample_size:,} rows...")

# Method 1: Random sampling
skip_rows = sorted(np.random.choice(range(1, row_count), 
                                  row_count - sample_size, 
                                  replace=False))
df_sample = pd.read_csv(FILE_PATH, skiprows=skip_rows)

# Save sample
output_path = FILE_PATH.replace('.csv', '_sample_100k.csv')
df_sample.to_csv(output_path, index=False)
print(f"Sample saved to: {output_path}")
print(f"New file size: {os.path.getsize(output_path) / (1024**2):.2f} MB")

# Clean up memory
del df_sample
gc.collect()

#%% [markdown]
# ## 3. Option B: Split by Year

#%%
# Process file in chunks and split by year
chunk_size = 50000
yearly_files = {}

print(f"Processing file in chunks of {chunk_size:,} rows...")

for i, chunk in enumerate(pd.read_csv(FILE_PATH, chunksize=chunk_size)):
    # Convert date
    chunk['AC_OPEN_DATE'] = pd.to_datetime(chunk['AC_OPEN_DATE'], errors='coerce')
    chunk['year'] = chunk['AC_OPEN_DATE'].dt.year
    
    # Group by year
    for year, year_data in chunk.groupby('year'):
        if pd.notna(year):
            year = int(year)
            if year not in yearly_files:
                yearly_files[year] = []
            yearly_files[year].append(year_data.drop('year', axis=1))
    
    # Progress
    if i % 10 == 0:
        print(f"Processed {(i+1) * chunk_size:,} rows...")

# Save yearly files
output_dir = os.path.dirname(FILE_PATH)
for year, chunks in yearly_files.items():
    year_df = pd.concat(chunks, ignore_index=True)
    year_path = os.path.join(output_dir, f'customer_data_{year}.csv')
    year_df.to_csv(year_path, index=False)
    print(f"Saved {year}: {len(year_df):,} rows ({os.path.getsize(year_path)/(1024**2):.1f} MB)")

#%% [markdown]
# ## 4. Option C: Create Summary Statistics File

#%%
# Create aggregated summary for dashboard
chunk_size = 50000
summary_list = []

print("Creating summary statistics...")

for chunk in pd.read_csv(FILE_PATH, chunksize=chunk_size):
    # Convert dates
    chunk['AC_OPEN_DATE'] = pd.to_datetime(chunk['AC_OPEN_DATE'], errors='coerce')
    chunk['MOBILE_APP_REGISTRATION_DATE'] = pd.to_datetime(chunk['MOBILE_APP_REGISTRATION_DATE'], errors='coerce')
    
    # Add month/year
    chunk['year_month'] = chunk['AC_OPEN_DATE'].dt.to_period('M')
    
    # Calculate registration status
    chunk['is_registered'] = chunk['MOBILE_APP_REGISTRATION_DATE'].notna()
    
    # Aggregate
    summary = chunk.groupby(['REGION_DESC', 'year_month']).agg({
        'CUSTOMER_NO': 'count',
        'INET_ELIGIBLE': lambda x: (x == 'Y').sum(),
        'is_registered': 'sum',
        'AGE': ['mean', 'median'],
        'CUSTOMER_MTD_AVERAGE_ALL_ACTIVE_ELIGIBLE': ['mean', 'median', 'sum']
    }).reset_index()
    
    summary_list.append(summary)

# Combine summaries
final_summary = pd.concat(summary_list)

# Flatten column names
final_summary.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                        for col in final_summary.columns.values]

# Group again for final aggregation
final_summary = final_summary.groupby(['REGION_DESC', 'year_month']).agg({
    'CUSTOMER_NO_count': 'sum',
    'INET_ELIGIBLE_<lambda>': 'sum',
    'is_registered_sum': 'sum',
    'AGE_mean': 'mean',
    'AGE_median': 'mean',
    'CUSTOMER_MTD_AVERAGE_ALL_ACTIVE_ELIGIBLE_mean': 'mean',
    'CUSTOMER_MTD_AVERAGE_ALL_ACTIVE_ELIGIBLE_median': 'mean',
    'CUSTOMER_MTD_AVERAGE_ALL_ACTIVE_ELIGIBLE_sum': 'sum'
}).reset_index()

# Rename columns
final_summary.columns = ['REGION_DESC', 'year_month', 'total_customers', 'inet_eligible',
                        'registered', 'avg_age', 'median_age', 'avg_balance', 
                        'median_balance', 'total_balance']

# Save summary
summary_path = FILE_PATH.replace('.csv', '_summary_stats.csv')
final_summary.to_csv(summary_path, index=False)
print(f"Summary saved to: {summary_path}")
print(f"Summary file size: {os.path.getsize(summary_path) / (1024**2):.2f} MB")

#%% [markdown]
# ## 5. Quick Visualization from Summary

#%%
# Load and visualize summary
summary_df = pd.read_csv(summary_path)
summary_df['year_month'] = pd.to_datetime(summary_df['year_month'])

# Plot monthly trends
plt.figure(figsize=(12, 6))
for region in summary_df['REGION_DESC'].unique():
    region_data = summary_df[summary_df['REGION_DESC'] == region]
    plt.plot(region_data['year_month'], region_data['total_customers'], 
             label=region, marker='o')

plt.title('Monthly Customer Growth by Region')
plt.xlabel('Month')
plt.ylabel('Total Customers')
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Registration rates by region
summary_df['registration_rate'] = summary_df['registered'] / summary_df['total_customers']

plt.figure(figsize=(10, 6))
regional_reg_rate = summary_df.groupby('REGION_DESC')['registration_rate'].mean().sort_values()
regional_reg_rate.plot(kind='barh')
plt.title('Average Registration Rate by Region')
plt.xlabel('Registration Rate')
plt.tight_layout()
plt.show()

#%% [markdown]
# ## 6. Memory-Efficient Analysis Function

#%%
def analyze_large_file_efficiently(file_path, analysis_func, chunk_size=50000):
    """
    Apply analysis function to large file in chunks
    
    Parameters:
    - file_path: path to CSV file
    - analysis_func: function that takes a DataFrame and returns results
    - chunk_size: rows per chunk
    
    Returns combined results
    """
    results = []
    
    for i, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size)):
        # Apply analysis
        chunk_result = analysis_func(chunk)
        results.append(chunk_result)
        
        # Progress
        if i % 10 == 0:
            print(f"Processed chunk {i+1}")
    
    # Combine results (method depends on what analysis_func returns)
    if isinstance(results[0], pd.DataFrame):
        return pd.concat(results, ignore_index=True)
    else:
        return results

# Example: Get registration stats by branch
def get_branch_stats(df):
    df['MOBILE_APP_REGISTRATION_DATE'] = pd.to_datetime(df['MOBILE_APP_REGISTRATION_DATE'], errors='coerce')
    df['is_registered'] = df['MOBILE_APP_REGISTRATION_DATE'].notna()
    
    return df.groupby('BRANCH_NAME').agg({
        'CUSTOMER_NO': 'count',
        'is_registered': 'sum'
    }).reset_index()

# Run analysis
print("Analyzing branch performance...")
branch_stats = analyze_large_file_efficiently(FILE_PATH, get_branch_stats)

# Aggregate results
branch_final = branch_stats.groupby('BRANCH_NAME').sum().reset_index()
branch_final['registration_rate'] = branch_final['is_registered'] / branch_final['CUSTOMER_NO']

# Top performing branches
print("\nTop 10 Branches by Registration Rate:")
top_branches = branch_final.sort_values('registration_rate', ascending=False).head(10)
print(top_branches[['BRANCH_NAME', 'CUSTOMER_NO', 'registration_rate']])

#%% [markdown]
# ## 7. Export Options for Dashboard

#%%
print("\n📊 Files created for dashboard use:")
print(f"1. Sample file (100k rows): {output_path}")
print(f"2. Summary statistics: {summary_path}")
print("3. Yearly files:")
for year in sorted(yearly_files.keys()):
    year_file = os.path.join(output_dir, f'customer_data_{year}.csv')
    if os.path.exists(year_file):
        size_mb = os.path.getsize(year_file) / (1024**2)
        print(f"   - {year}: {size_mb:.1f} MB")

print("\n✅ You can now use any of these smaller files in the Streamlit dashboard!")
