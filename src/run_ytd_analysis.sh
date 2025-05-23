@echo off
REM ========================================
REM YTD Analysis Runner for iNET Dashboard
REM ========================================

echo.
echo ====================================
echo iNET Year-to-Date Analysis Runner
echo ====================================
echo.

REM Set paths
set PROJECT_DIR=C:\Users\mehak.rafiq.ASKARIBANK\Documents\Projects\model_data\Daily_Dashboard_NTB
set DATA_FILE=%PROJECT_DIR%\Data\Customer-Level-Account Holder Detail Report -2603_Report2 (6).csv
set OUTPUT_DIR=%PROJECT_DIR%\Data\ytd_analysis
set PYTHON_SCRIPT=%PROJECT_DIR%\src\ytd_preprocessor.py
set DASHBOARD_SCRIPT=%PROJECT_DIR%\src\ytd_comparison_dashboard.py

REM Get current date for reference
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~0,4%"
set "MM=%dt:~4,2%"
set "DD=%dt:~6,2%"
set CURRENT_DATE=%YY%-%MM%-%DD%

echo Current Date: %CURRENT_DATE%
echo.
echo Step 1: Preprocessing data for YTD analysis...
echo ------------------------------------------------

REM Check if Python script exists
if not exist "%PYTHON_SCRIPT%" (
    echo ERROR: Python script not found at %PYTHON_SCRIPT%
    echo Please ensure ytd_preprocessor.py is in the src folder
    pause
    exit /b 1
)

REM Run preprocessing
python "%PYTHON_SCRIPT%" "%DATA_FILE%" --output-dir "%OUTPUT_DIR%" --reference-date "%CURRENT_DATE%" --analyze

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Preprocessing failed!
    pause
    exit /b 1
)

echo.
echo Step 2: Starting YTD Dashboard...
echo ------------------------------------------------

REM Check if dashboard script exists
if not exist "%DASHBOARD_SCRIPT%" (
    echo Using alternative dashboard script...
    set DASHBOARD_SCRIPT=%PROJECT_DIR%\src\inet_dashboard_enhanced.py
)

REM Start the dashboard
echo.
echo Starting Streamlit dashboard...
echo You can access it at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the dashboard
echo.

streamlit run "%DASHBOARD_SCRIPT%"

pause