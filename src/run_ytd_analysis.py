"""
YTD Analysis Runner for iNET Dashboard
Run this script to automatically process and analyze YTD data
"""

import os
import sys
import subprocess
from datetime import datetime
import time

# Configuration
PROJECT_DIR = r"C:\Users\mehak.rafiq.ASKARIBANK\Documents\Projects\model_data\Daily_Dashboard_NTB"
DATA_FILE = os.path.join(PROJECT_DIR, "Data", "Customer-Level-Account Holder Detail Report -2603_Report2 (6).csv")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "Data", "ytd_analysis")
SRC_DIR = os.path.join(PROJECT_DIR, "src")

def print_header():
    """Print script header"""
    print("\n" + "="*60)
    print("iNET Year-to-Date Analysis Runner")
    print("="*60)
    print(f"Current Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")

def check_requirements():
    """Check if all required files exist"""
    print("Checking requirements...")
    
    # Check data file
    if not os.path.exists(DATA_FILE):
        print(f"❌ Data file not found: {DATA_FILE}")
        return False
    else:
        file_size = os.path.getsize(DATA_FILE) / (1024**3)
        print(f"✅ Data file found ({file_size:.2f} GB)")
    
    # Check src directory
    if not os.path.exists(SRC_DIR):
        print(f"❌ Source directory not found: {SRC_DIR}")
        return False
    else:
        print(f"✅ Source directory found")
    
    # Check Python packages
    required_packages = ['pandas', 'numpy', 'streamlit', 'plotly']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing Python packages: {', '.join(missing_packages)}")
        print(f"   Install with: pip install {' '.join(missing_packages)}")
        return False
    else:
        print("✅ All required packages installed")
    
    return True

def run_preprocessing():
    """Run the YTD preprocessing script"""
    print("\n" + "-"*60)
    print("Step 1: Preprocessing data for YTD analysis")
    print("-"*60)
    
    preprocessor_script = os.path.join(SRC_DIR, "ytd_preprocessor.py")
    
    if not os.path.exists(preprocessor_script):
        print("Creating YTD preprocessor script...")
        # Here you would copy or create the script
        print("❌ Preprocessor script not found. Please ensure ytd_preprocessor.py is in the src folder")
        return False
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Run preprocessing
    current_date = datetime.now().strftime('%Y-%m-%d')
    cmd = [
        sys.executable,
        preprocessor_script,
        DATA_FILE,
        "--output-dir", OUTPUT_DIR,
        "--reference-date", current_date,
        "--analyze"
    ]
    
    print(f"Running: {' '.join(cmd[:2])}...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Preprocessing completed successfully!")
            
            # Show created files
            print("\nCreated files:")
            for file in os.listdir(OUTPUT_DIR):
                file_path = os.path.join(OUTPUT_DIR, file)
                file_size = os.path.getsize(file_path) / (1024**2)
                print(f"  - {file} ({file_size:.1f} MB)")
            
            return True
        else:
            print(f"❌ Preprocessing failed with error:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running preprocessing: {str(e)}")
        return False

def run_dashboard():
    """Launch the Streamlit dashboard"""
    print("\n" + "-"*60)
    print("Step 2: Launching YTD Dashboard")
    print("-"*60)
    
    # Try different dashboard scripts
    dashboard_scripts = [
        "ytd_comparison_dashboard.py",
        "inet_dashboard_enhanced.py",
        "inet_dashboard.py"
    ]
    
    dashboard_script = None
    for script in dashboard_scripts:
        script_path = os.path.join(SRC_DIR, script)
        if os.path.exists(script_path):
            dashboard_script = script_path
            break
    
    if not dashboard_script:
        print("❌ No dashboard script found in src folder")
        return False
    
    print(f"Using dashboard: {os.path.basename(dashboard_script)}")
    print("\n🌐 Dashboard will open in your browser at: http://localhost:8501")
    print("📌 Press Ctrl+C to stop the dashboard\n")
    
    # Launch streamlit
    cmd = ["streamlit", "run", dashboard_script]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\n✅ Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error running dashboard: {str(e)}")
        return False
    
    return True

def main():
    """Main execution function"""
    print_header()
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed. Please fix the issues above.")
        input("\nPress Enter to exit...")
        return
    
    # Ask user for options
    print("\nSelect operation mode:")
    print("1. Run full YTD analysis (preprocessing + dashboard)")
    print("2. Only preprocess data")
    print("3. Only run dashboard (use existing processed data)")
    print("4. Quick analysis (sample data)")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        # Full analysis
        if run_preprocessing():
            time.sleep(2)  # Brief pause
            run_dashboard()
    
    elif choice == "2":
        # Only preprocessing
        run_preprocessing()
        print("\n✅ Preprocessing complete. You can now run the dashboard separately.")
    
    elif choice == "3":
        # Only dashboard
        run_dashboard()
    
    elif choice == "4":
        # Quick analysis with sample
        print("\nRunning dashboard with sample data...")
        dashboard_script = os.path.join(SRC_DIR, "ytd_comparison_dashboard.py")
        if os.path.exists(dashboard_script):
            subprocess.run(["streamlit", "run", dashboard_script])
        else:
            print("❌ Dashboard script not found")
    
    else:
        print("Invalid choice. Exiting...")
    
    print("\n" + "="*60)
    print("Analysis session completed")
    print("="*60)
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()