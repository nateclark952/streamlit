# RFID Tool Tracking & Theft Prevention Dashboard

A comprehensive Streamlit dashboard for tracking RFID-tagged tools and assets with theft prevention capabilities.

## Features

- 📍 **Location Overview**: Visualize asset distribution across buildings and rooms
- 📦 **Asset Status**: Monitor check-out status and active/inactive assets
- 👤 **Check-out Analysis**: Track checked-out assets and identify long-term checkouts
- 📊 **Analytics**: Time-based trends and asset update patterns
- 🔍 **Search & Details**: Advanced search functionality and data export
- ⚠️ **Alerts**: Automatic warnings for:
  - Assets checked out for more than 30 days
  - Assets not updated in 90+ days
  - Inactive assets that are checked out

## Installation

1. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run streamlit_app.py
```

2. Upload your CSV file through the sidebar
3. Use the filters to narrow down your view
4. Explore the different dashboard tabs

## Data Format

The dashboard expects a CSV file with the following columns (at minimum):
- Asset ID
- Building
- Room Name
- RFID Tag ID (hex)
- Checked Out To
- Check Out Date
- Date Added
- Last Updated
- Active

## Deployment to Streamlit Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Set the main file path to `streamlit_app.py`
5. Deploy!

## Customization

You can customize the dashboard by:
- Adjusting date thresholds in the alert sections
- Modifying chart colors and styles
- Adding additional filters or metrics
- Customizing the export functionality

## License

MIT

