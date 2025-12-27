# Quick Start Guide

## Step 1: Install Dependencies

Open a terminal/command prompt and run:
```bash
pip install -r requirements.txt
```

## Step 2: Run the Dashboard

```bash
streamlit run streamlit_app.py
```

The dashboard will open in your default web browser at `http://localhost:8501`

## Step 3: Upload Your Data

1. Click on the file uploader in the sidebar
2. Select your `AllAssets_2025Dec27T1225pm.csv` file
3. Wait for the data to load (you'll see a success message)

## Step 4: Explore the Dashboard

### Key Metrics
- View total assets, check-out status, and building counts at a glance

### Location Overview Tab
- See asset distribution by building and room
- View heatmaps of asset locations

### Asset Status Tab
- Monitor check-out vs available assets
- Track active/inactive status

### Check-out Analysis Tab
- Identify long-term checkouts (>30 days)
- View all currently checked-out assets
- Analyze check-out patterns

### Analytics Tab
- View trends over time
- See asset update patterns
- Get summary statistics

### Search & Details Tab
- Search for specific assets by ID, RFID tag, building, room, or person
- Export filtered data to CSV

## Tips

- Use the sidebar filters to focus on specific buildings or asset statuses
- Pay attention to the alerts section for potential issues
- Export data for further analysis in Excel or other tools
- The dashboard automatically calculates days since checkout and last update

## Troubleshooting

**Issue**: Dashboard shows errors when loading data
- **Solution**: Make sure your CSV file has the required columns (see README.md)

**Issue**: Charts are not displaying
- **Solution**: Check that you have plotly installed: `pip install plotly`

**Issue**: Date columns are not parsing correctly
- **Solution**: The dashboard handles various date formats automatically, but if issues persist, check your date format matches: "Sep 22, 2025 5:05 PM"

## Next Steps

1. Customize alert thresholds in the code if needed
2. Add additional visualizations as required
3. Deploy to Streamlit Cloud for team access

