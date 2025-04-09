# Eviction Data Tracker

A specialized tool for collecting and analyzing public eviction record data from court websites and public records databases.

## Purpose

This tool helps legal aid organizations, housing advocates, researchers, and concerned citizens:

1. Track the status of eviction cases in their jurisdiction
2. Analyze processing times for eviction filings
3. Identify patterns in eviction proceedings
4. Generate informative reports on eviction activity

## Features

- Analysis of login pages to help with authentication
- Automatic detection of search pages for eviction records
- Extraction of case data from search results
- Timeline analysis of eviction proceedings
- Status tracking across multiple cases
- Export to CSV and JSON formats
- Generation of human-readable reports

## Requirements

- Python 3.6+
- Required packages: requests, beautifulsoup4, pandas

## Installation

1. Install the required packages:

```bash
pip install requests beautifulsoup4 pandas
```

2. Make the script executable:

```bash
chmod +x eviction_tracker.py
```

## Ethical Usage Guidelines

This tool is designed for:
- Academic research
- Legal advocacy
- Public policy development
- Tenant rights education

It should only be used with publicly available records that do not contain private information beyond what is already disclosed in public court documents.

## Basic Usage

### Step 1: Analyze a court records website

```bash
python eviction_tracker.py https://courts.example.gov --analyze-login
```

This generates a report on the login form structure to help you understand how to authenticate.

### Step 2: Manual data collection

After analyzing the site, you'll need to:
1. Manually log in to the court website
2. Navigate to the case search page
3. Perform a search for eviction cases
4. Save the HTML of the search results page

### Step 3: Extract and analyze the data

```bash
python eviction_tracker.py https://courts.example.gov --search-url https://courts.example.gov/search
```

When prompted, provide the path to your saved HTML file.

## Advanced Usage

### Custom CSS selectors

Create a JSON file with CSS selectors for your specific court website:

```json
{
  "record_container": "tr.case-record",
  "case_number": ".case-number",
  "filing_date": ".filing-date",
  "status": ".status",
  "address": ".address",
  "plaintiff": ".plaintiff",
  "defendant": ".defendant"
}
```

Then use it with:

```bash
python eviction_tracker.py https://courts.example.gov --selector-file selectors.json
```

### Customizing output

```bash
python eviction_tracker.py https://courts.example.gov --output-dir my_data --delay 3
```

## Output

The tool generates:
- JSON files with structured eviction data
- CSV files for easy import into spreadsheets
- Markdown reports with analysis and statistics
- Log files tracking the extraction process

## Data Privacy

This tool does not store login credentials and only works with data you manually provide. It's designed to respect privacy while still enabling access to public records.

## Legal Disclaimer

This tool is provided for research and educational purposes only. Users are responsible for ensuring their use complies with applicable laws regarding public records access. Always verify that the data you're collecting is publicly available and that your access method complies with the terms of service of the website you're using. 