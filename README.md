# Redbeam Data Scraper

Automated scraper to extract data from your Redbeam account and save it to an Excel file on your desktop.

## Features

- Automated login to Redbeam
- Data extraction from the data page
- Saves data to Excel file on desktop with timestamp
- Can be scheduled to run daily
- Comprehensive logging

## Prerequisites

1. **Python 3.8+** installed on your system
2. **Google Chrome** browser installed
3. **ChromeDriver** - The script will attempt to use the system ChromeDriver, or you can install it separately

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install ChromeDriver (if not already installed):
   - Option 1: Download from https://chromedriver.chromium.org/ and add to PATH
   - Option 2: The script will attempt to use the system Chrome installation

## Usage

### Run Once

Simply run the script:
```bash
python redbeam_scraper.py
```

The script will:
1. Log in to Redbeam
2. Navigate to the data page
3. Extract all available data
4. Save it to an Excel file on your desktop with format: `redbeam_data_YYYYMMDD_HHMMSS.xlsx`

### Schedule Daily Execution (Windows)

#### Option 1: Windows Task Scheduler (Recommended)

1. Open Task Scheduler (search for "Task Scheduler" in Windows)
2. Click "Create Basic Task"
3. Name it "Redbeam Daily Scraper"
4. Set trigger to "Daily" and choose your preferred time
5. Action: "Start a program"
6. Program/script: `python` (or full path to python.exe)
7. Add arguments: `"C:\Users\natec\redbeam_scraper\redbeam_scraper.py"` (use full path to the script)
8. Start in: `"C:\Users\natec\redbeam_scraper"` (directory containing the script)
9. Click Finish

#### Option 2: Python Schedule Library

If you prefer to keep the script running continuously, you can modify it to use the `schedule` library. Install it first:
```bash
pip install schedule
```

Then modify the script to include scheduling logic.

## Logging

The script creates a log file `redbeam_scraper.log` in the same directory with detailed information about each run, including any errors.

## Troubleshooting

1. **ChromeDriver not found**: Make sure Chrome is installed and ChromeDriver is in your PATH, or download ChromeDriver separately.

2. **Login fails**: 
   - Check the credentials in the script
   - The script saves screenshots (`login_error.png`, `login_failed.png`) for debugging
   - Check the log file for detailed error messages

3. **No data extracted**: 
   - The script saves a screenshot (`data_page_screenshot.png`) and page source (`data_page_source.html`) for debugging
   - Check if the data page URL is correct
   - Verify you have access to the data page after login

4. **Excel file not created**: 
   - Check that you have write permissions to your Desktop
   - Verify the `openpyxl` package is installed correctly

## Security Note

The credentials are currently hardcoded in the script. For production use, consider:
- Using environment variables
- Using a configuration file with proper permissions
- Using a secrets management system

## Files Generated

- `redbeam_data_YYYYMMDD_HHMMSS.xlsx` - Excel file with scraped data (on Desktop)
- `redbeam_scraper.log` - Log file with execution details
- `*.png` - Screenshots (only created on errors)
- `data_page_source.html` - HTML source (only created if no data found)

