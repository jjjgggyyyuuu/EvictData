# Ethical Web Scraper Agent

An ethical web scraping tool that can authenticate with websites and extract structured data.

## Features

- Website authentication with username/password
- Automatic CSRF token detection
- Structured data extraction using CSS selectors
- Crawling with configurable depth
- Polite scraping with delays between requests
- Data export to JSON and CSV formats
- Detailed logging

## Requirements

- Python 3.6+
- Required packages: requests, beautifulsoup4

## Installation

1. Install the required packages:

```bash
pip install requests beautifulsoup4
```

2. Make the script executable:

```bash
chmod +x webscraper.py
```

## Ethical Usage Guidelines

- Only scrape websites where you have permission or it is allowed by Terms of Service
- Set appropriate delays between requests (default: 2 seconds) 
- Identify your scraper with a proper User-Agent
- Don't overwhelm servers with too many requests
- Respect robots.txt directives
- Don't scrape personal or private information

## Basic Usage

```bash
python webscraper.py https://example.com
```

## Advanced Usage Examples

### Scrape with login

```bash
python webscraper.py https://example.com --login --login-url https://example.com/login --username myuser --password mypass
```

### Extract specific data using CSS selectors

```bash
python webscraper.py https://example.com \
  --selector products ".product-item" \
  --selector prices ".product-price" \
  --selector titles ".product-title"
```

### Control crawling depth and delay

```bash
python webscraper.py https://example.com \
  --max-pages 20 \
  --delay 3.5
```

### Full example with all options

```bash
python webscraper.py https://example.com \
  --login \
  --login-url https://example.com/login \
  --username myuser \
  --password mypass \
  --selector products ".product-item" \
  --selector prices ".product-price" \
  --selector titles ".product-title" \
  --max-pages 50 \
  --delay 3 \
  --output-dir mydata
```

## Output

Data is saved in the specified output directory (default: `scraped_data/`) as:
- JSON files with all extracted data
- CSV files with first-level data
- Detailed logs in `scraper.log`

## Customization

The WebScraperAgent class can be imported and used in your own scripts for more customized scraping:

```python
from webscraper import WebScraperAgent

scraper = WebScraperAgent("https://example.com", delay=3)
scraper.login("https://example.com/login", "username", "password")
data = scraper.crawl("https://example.com/products", max_pages=20,
                    selectors={"products": ".product-item"})
```

## Legal Disclaimer

This tool is provided for educational and ethical research purposes only. Users are responsible for ensuring their use of this tool complies with applicable website terms of service, laws, and regulations. Always obtain proper permission before scraping a website. 