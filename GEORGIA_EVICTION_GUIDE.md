# Georgia Eviction Tracking Guide

This guide will help you use the Eviction Data Tracker tool to monitor marshal's office timelines and eviction status in Georgia using public court records.

## Prerequisites

1. Python 3.6 or later
2. Required Python packages:
   ```
   pip install requests beautifulsoup4 pandas
   ```
3. A Georgia court records account (if you don't have one, you'll need to register at the Tyler Technologies portal)

## Step 1: Analyze the Login Page

We've already completed this step. The analysis revealed that the login form requires:
- Email address
- Password
- CSRF token (automatically handled)

## Step 2: Login and Navigate to the Case Search

1. Visit the login page:
   ```
   https://georgia.tylertech.cloud/idp/account/signin
   ```

2. Log in with your credentials.

3. After login, you'll be redirected to the Research GA portal. Navigate to case search, which is typically found in the main menu.

4. For eviction cases, search for:
   - Case Type: "Dispossessory Warrant" or "Eviction"
   - Filing Date Range: Set appropriate dates (e.g., last 30-90 days)
   - County: Select your county of interest

## Step 3: Save the Search Results

1. After your search returns results, you'll need to save the HTML:
   - In Chrome: Right-click → View Page Source → Select All (Ctrl+A) → Copy (Ctrl+C) → Paste into a text file and save as `georgia_evictions.html`
   - In Firefox: Right-click → View Page Source → Save Page As... → Save as `georgia_evictions.html`

2. Make sure to save this file in the same directory as the eviction_tracker.py script.

## Step 4: Extract and Analyze the Data

1. Run the extraction script with our custom selectors:
   ```
   python eviction_tracker.py https://researchga.tylerhost.net --selector-file georgia_selectors.json
   ```

2. When prompted, enter the path to the HTML file you saved:
   ```
   georgia_evictions.html
   ```

3. The script will:
   - Extract all eviction case data
   - Analyze filing dates, hearing dates, and case statuses
   - Generate a report on eviction timelines
   - Save the data in CSV and JSON formats for further analysis

## Step 5: Interpret the Results

The generated report will provide:

1. **Current Case Status Breakdown**: Shows how many cases are at each stage (e.g., Filed, Hearing Scheduled, Judgment Issued, Writ Issued)

2. **Timeline Analysis**: 
   - Average days from filing to hearing
   - Average days from judgment to eviction
   - Most recent marshal's office activity

3. **Predicting Future Activity**:
   - Based on current processing times, you can estimate when a newly filed case might reach the eviction stage
   - Identify patterns in how the marshal's office is handling evictions

## How to Track Marshal's Office Timelines

The key fields for tracking marshal's office activity are:

1. **Filing Date**: When the eviction case was initially filed
2. **Judgment Date**: When the court ruled in favor of the landlord
3. **Last Event**: Latest activity in the case
4. **Last Event Date**: When the latest activity occurred
5. **Next Event**: Upcoming activity (if scheduled)
6. **Next Event Date**: When the next activity is scheduled

For cases with a judgment in favor of the landlord, the time between judgment and actual eviction execution represents the marshal's office processing time.

## Regular Monitoring

For continuous monitoring:

1. Perform searches weekly or bi-weekly
2. Save new results each time
3. Run the analyzer with each new dataset
4. Compare timelines across different time periods to identify trends

This will help you understand:
- If the marshal's office is speeding up or slowing down
- How many cases are in the pipeline
- Approximately when pending evictions might be executed

## Need Help?

If you encounter issues with the data extraction or have questions about interpreting the results, review the detailed documentation in the eviction_tracker_README.md file. 