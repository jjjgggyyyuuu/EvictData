#!/usr/bin/env python3
import argparse
import requests
from bs4 import BeautifulSoup
import json
import csv
import time
import random
import logging
import os
import datetime
import pandas as pd
import re
from urllib.parse import urlparse, urljoin

class EvictionDataScraper:
    def __init__(self, base_url, output_dir="eviction_data", delay=2):
        """Initialize the eviction data scraper.
        
        Args:
            base_url: The base URL of the court/public records site
            output_dir: Directory to save scraped data
            delay: Seconds to wait between requests
        """
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.session = requests.Session()
        self.output_dir = output_dir
        self.delay = delay
        self.visited_urls = set()
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("eviction_scraper.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("EvictionDataScraper")
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Set a user agent to identify the bot (ethical practice)
        self.session.headers.update({
            "User-Agent": "EvictionDataResearch/1.0 (Public Records Research Project)",
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Language": "en-US,en;q=0.9",
        })
    
    def detect_form_fields(self, form_soup):
        """Detect form fields from a login form to help with manual configuration.
        
        Args:
            form_soup: BeautifulSoup object containing the form
            
        Returns:
            dict: Form field information
        """
        fields = {}
        
        for input_tag in form_soup.find_all(['input', 'select', 'textarea']):
            field_type = input_tag.name
            field_name = input_tag.get('name', '')
            field_id = input_tag.get('id', '')
            field_value = input_tag.get('value', '')
            
            if field_name or field_id:
                fields[field_name or field_id] = {
                    'type': input_tag.get('type', field_type),
                    'value': field_value,
                    'required': input_tag.get('required') is not None,
                    'placeholder': input_tag.get('placeholder', '')
                }
        
        return fields
    
    def analyze_login_page(self, login_url):
        """Analyze the login page to determine form structure.
        
        Args:
            login_url: URL of the login page
            
        Returns:
            dict: Login page analysis
        """
        self.logger.info(f"Analyzing login page at {login_url}")
        
        response = self.session.get(login_url)
        if response.status_code != 200:
            self.logger.error(f"Failed to access login page: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all forms
        forms = []
        for i, form in enumerate(soup.find_all('form')):
            form_data = {
                'form_index': i,
                'action': form.get('action', ''),
                'method': form.get('method', 'get').lower(),
                'fields': self.detect_form_fields(form)
            }
            forms.append(form_data)
        
        # Look for CSRF tokens
        csrf_tokens = []
        for input_tag in soup.find_all('input'):
            if input_tag.get('name') and ('csrf' in input_tag.get('name').lower() or 
                                        'token' in input_tag.get('name').lower()):
                csrf_tokens.append({
                    'name': input_tag.get('name'),
                    'value': input_tag.get('value', '')
                })
        
        result = {
            'url': login_url,
            'title': soup.title.string if soup.title else "No title",
            'forms': forms,
            'csrf_tokens': csrf_tokens,
            'html': response.text  # Include for reference if needed
        }
        
        # Save the analysis
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        analysis_path = os.path.join(self.output_dir, f"login_analysis_{timestamp}.json")
        with open(analysis_path, 'w', encoding='utf-8') as f:
            # Exclude HTML to keep file smaller
            analysis_copy = result.copy()
            analysis_copy.pop('html', None)
            json.dump(analysis_copy, f, indent=2)
        
        self.logger.info(f"Login page analysis saved to {analysis_path}")
        return result
    
    def find_eviction_search_page(self, start_url):
        """Attempt to find the eviction/case search page from a starting point.
        
        Args:
            start_url: URL to start from
            
        Returns:
            str: URL of the likely search page, or None
        """
        self.logger.info(f"Looking for eviction search page from {start_url}")
        
        response = self.session.get(start_url)
        if response.status_code != 200:
            self.logger.error(f"Failed to access start page: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for links that might lead to search pages
        search_keywords = [
            'search', 'case', 'record', 'court', 'docket', 'filing', 
            'eviction', 'tenant', 'landlord', 'property', 'housing',
            'civil', 'dispossessory', 'judgment'
        ]
        
        potential_links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text(strip=True).lower()
            
            # Skip empty or javascript links
            if not href or href.startswith('#') or 'javascript:' in href:
                continue
                
            # Normalize URL
            if not href.startswith(('http://', 'https://')):
                href = urljoin(start_url, href)
            
            # If it's external, skip
            if self.domain not in urlparse(href).netloc:
                continue
            
            # Check if the link text contains search keywords
            score = 0
            for keyword in search_keywords:
                if keyword in link_text:
                    score += 1
                if keyword in href.lower():
                    score += 0.5
            
            if score > 0:
                potential_links.append({
                    'url': href,
                    'text': link_text,
                    'score': score
                })
        
        # Sort by score
        potential_links.sort(key=lambda x: x['score'], reverse=True)
        
        # Save the potential links
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        links_path = os.path.join(self.output_dir, f"potential_search_links_{timestamp}.json")
        with open(links_path, 'w', encoding='utf-8') as f:
            json.dump(potential_links, f, indent=2)
        
        self.logger.info(f"Potential search links saved to {links_path}")
        
        # Return the highest scoring link, or None
        if potential_links:
            self.logger.info(f"Most likely search page: {potential_links[0]['url']} (score: {potential_links[0]['score']})")
            return potential_links[0]['url']
        
        self.logger.warning("No potential search pages found")
        return None
    
    def extract_eviction_data(self, html_content, selectors):
        """Extract eviction data from HTML using provided selectors.
        
        Args:
            html_content: HTML content to parse
            selectors: Dictionary of CSS selectors for different data types
            
        Returns:
            list: Extracted eviction records
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        records = []
        
        # Check if we have a container selector for individual cases/records
        if 'record_container' in selectors and selectors['record_container']:
            containers = soup.select(selectors['record_container'])
            
            for container in containers:
                record = {}
                
                # Extract data from each container using the selectors
                for field, selector in selectors.items():
                    if field == 'record_container':
                        continue
                        
                    elements = container.select(selector)
                    if elements:
                        record[field] = elements[0].get_text(strip=True)
                    else:
                        record[field] = None
                
                records.append(record)
        else:
            # If no container selector, try to extract data directly
            record = {}
            for field, selector in selectors.items():
                elements = soup.select(selector)
                if elements:
                    # If multiple elements match, store as a list
                    values = [el.get_text(strip=True) for el in elements]
                    record[field] = values
                else:
                    record[field] = None
            
            if any(record.values()):  # If any data was found
                records.append(record)
        
        return records
    
    def extract_dates_from_text(self, text):
        """Extract dates from text content using common patterns.
        
        Args:
            text: Text to parse for dates
            
        Returns:
            list: Extracted dates
        """
        # Common date patterns
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY or M/D/YY
            r'\d{1,2}-\d{1,2}-\d{2,4}',  # MM-DD-YYYY or M-D-YY
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
            r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',  # DD Month YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            dates.extend(matches)
        
        return dates
    
    def analyze_eviction_data(self, eviction_records):
        """Analyze eviction data for patterns and statistics.
        
        Args:
            eviction_records: List of eviction record dictionaries
            
        Returns:
            dict: Analysis results
        """
        if not eviction_records:
            return {"error": "No eviction records to analyze"}
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(eviction_records)
        
        # Basic statistics
        record_count = len(df)
        
        # Try to identify date fields
        date_fields = []
        for column in df.columns:
            # Skip columns that are clearly not dates
            if column in ['case_number', 'address', 'plaintiff', 'defendant']:
                continue
                
            # Check if column name suggests it's a date
            if any(kw in column.lower() for kw in ['date', 'filed', 'hearing', 'scheduled', 'judgment']):
                date_fields.append(column)
        
        # If no date fields identified by name, try to detect date patterns in string columns
        if not date_fields:
            for column in df.columns:
                if df[column].dtype == 'object':  # String column
                    # Sample a few values
                    sample = df[column].dropna().sample(min(5, df[column].count()))
                    
                    # Check if any values appear to be dates
                    for value in sample:
                        if isinstance(value, str) and self.extract_dates_from_text(value):
                            date_fields.append(column)
                            break
        
        # Extract timeline information if date fields were found
        timeline_stats = {}
        if date_fields:
            for field in date_fields:
                # Try to convert to datetime
                try:
                    dates = pd.to_datetime(df[field], errors='coerce')
                    valid_dates = dates.dropna()
                    
                    if not valid_dates.empty:
                        timeline_stats[field] = {
                            "min_date": valid_dates.min().strftime("%Y-%m-%d"),
                            "max_date": valid_dates.max().strftime("%Y-%m-%d"),
                            "count": len(valid_dates)
                        }
                except:
                    pass
        
        # Count cases by status if status field exists
        status_stats = {}
        status_fields = [col for col in df.columns if 'status' in col.lower()]
        if status_fields:
            status_field = status_fields[0]
            status_counts = df[status_field].value_counts().to_dict()
            status_stats = status_counts
        
        # Results
        analysis = {
            "record_count": record_count,
            "timeline_stats": timeline_stats,
            "status_stats": status_stats,
            "identified_date_fields": date_fields,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return analysis
    
    def save_eviction_data(self, data, analysis=None, prefix="eviction_data"):
        """Save the scraped eviction data in multiple formats.
        
        Args:
            data: List of dictionaries containing eviction records
            analysis: Optional analysis results
            prefix: Prefix for output filenames
        """
        if not data:
            self.logger.warning("No data to save")
            return
            
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Save raw data as JSON
        json_path = os.path.join(self.output_dir, f"{prefix}_{timestamp}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Eviction data saved to {json_path}")
        
        # Save as CSV
        csv_path = os.path.join(self.output_dir, f"{prefix}_{timestamp}.csv")
        
        # Get all unique keys
        keys = set()
        for record in data:
            keys.update(record.keys())
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(keys))
            writer.writeheader()
            for record in data:
                writer.writerow(record)
        
        self.logger.info(f"Eviction data saved to {csv_path}")
        
        # Save analysis if provided
        if analysis:
            analysis_path = os.path.join(self.output_dir, f"{prefix}_analysis_{timestamp}.json")
            with open(analysis_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Analysis saved to {analysis_path}")
    
    def generate_eviction_report(self, data, analysis):
        """Generate a human-readable report from eviction data and analysis.
        
        Args:
            data: List of eviction records
            analysis: Dictionary of analysis results
            
        Returns:
            str: Formatted report
        """
        report = []
        report.append("# Eviction Data Report")
        report.append(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        report.append("## Summary")
        report.append(f"Total records: {analysis.get('record_count', 'Unknown')}")
        report.append("")
        
        # Timeline
        if analysis.get('timeline_stats'):
            report.append("## Timeline Information")
            for field, stats in analysis['timeline_stats'].items():
                report.append(f"### {field.replace('_', ' ').title()}")
                report.append(f"- Earliest date: {stats.get('min_date', 'Unknown')}")
                report.append(f"- Latest date: {stats.get('max_date', 'Unknown')}")
                report.append(f"- Count: {stats.get('count', 0)}")
                report.append("")
        
        # Status breakdown
        if analysis.get('status_stats'):
            report.append("## Status Breakdown")
            for status, count in analysis['status_stats'].items():
                report.append(f"- {status}: {count}")
            report.append("")
        
        # Sample records
        report.append("## Sample Records")
        for i, record in enumerate(data[:5]):  # Show up to 5 records
            report.append(f"### Record {i+1}")
            for key, value in record.items():
                report.append(f"- {key.replace('_', ' ').title()}: {value}")
            report.append("")
        
        # Recommendations
        report.append("## Recommendations")
        report.append("Based on the data analyzed, here are some insights:")
        
        if analysis.get('timeline_stats'):
            # Find the most recent date field
            latest_dates = {}
            for field, stats in analysis['timeline_stats'].items():
                if 'max_date' in stats:
                    latest_dates[field] = stats['max_date']
            
            if latest_dates:
                most_recent_field, most_recent_date = max(latest_dates.items(), key=lambda x: x[1])
                report.append(f"- The most recent activity was {most_recent_field.replace('_', ' ')} on {most_recent_date}")
                
        if analysis.get('status_stats'):
            # Find most common status
            most_common_status = max(analysis['status_stats'].items(), key=lambda x: x[1])
            report.append(f"- The most common status is '{most_common_status[0]}' with {most_common_status[1]} cases")
            
        report.append("- For more detailed analysis, please review the JSON and CSV data files")
        
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description="Eviction Data Scraper for Public Records")
    parser.add_argument("url", help="Base URL of the public records website")
    parser.add_argument("--analyze-login", action="store_true", 
                        help="Analyze the login page and exit (helpful for configuration)")
    parser.add_argument("--login-url", help="Login page URL (if different from base URL)")
    parser.add_argument("--search-url", help="Direct URL to the case search page (if known)")
    parser.add_argument("--output-dir", default="eviction_data", 
                        help="Output directory for scraped data")
    parser.add_argument("--delay", type=float, default=2.0, 
                        help="Delay between requests in seconds")
    parser.add_argument("--selector-file", help="Path to JSON file with CSS selectors for data extraction")
    
    args = parser.parse_args()
    
    # Create the scraper
    scraper = EvictionDataScraper(args.url, output_dir=args.output_dir, delay=args.delay)
    
    # If analyzing login page, do that and exit
    if args.analyze_login:
        login_url = args.login_url or args.url
        scraper.analyze_login_page(login_url)
        print(f"Login page analysis complete. Check the {args.output_dir} directory for results.")
        return
    
    # Try to find the search page if not provided
    search_url = args.search_url
    if not search_url:
        search_url = scraper.find_eviction_search_page(args.url)
        if not search_url:
            print("Could not find a likely search page. Please provide --search-url directly.")
            return
    
    # Load selectors from file if provided
    selectors = {}
    if args.selector_file:
        try:
            with open(args.selector_file, 'r') as f:
                selectors = json.load(f)
            print(f"Loaded selectors from {args.selector_file}")
        except Exception as e:
            print(f"Error loading selectors: {e}")
            print("Using default selectors instead")
            
            # Define some default selectors for common patterns
            selectors = {
                "record_container": "tr.case-record, div.case-item, .case-result",
                "case_number": ".case-number, .case-id, td:nth-child(1)",
                "filing_date": ".filing-date, .date-filed, td:nth-child(2)",
                "status": ".status, .case-status, td:nth-child(3)",
                "address": ".address, .property-address, td:nth-child(4)",
                "plaintiff": ".plaintiff, .petitioner, td:nth-child(5)",
                "defendant": ".defendant, .respondent, td:nth-child(6)"
            }
    
    print("\nEviction Data Scraper")
    print("====================")
    print(f"Target website: {args.url}")
    print(f"Search page: {search_url}")
    print(f"Output directory: {args.output_dir}")
    print("====================\n")
    
    print("This tool helps you extract public eviction records. Please note:")
    print("1. You will need to manually navigate the site's search interface")
    print("2. The tool will attempt to extract data from the search results")
    print("3. CSS selectors may need adjustment for your specific site\n")
    
    print("Instructions:")
    print("1. If the site requires login, use the --analyze-login option first to understand the login form")
    print("2. Log in to the site manually in your browser")
    print("3. Navigate to the search page and perform a search for eviction records")
    print("4. Save the HTML of the search results page (right-click → Save As or use browser dev tools)")
    print("5. Run this tool again with --selector-file to extract data from the saved HTML\n")
    
    input("Press Enter to continue and open browser instructions, or Ctrl+C to exit...")
    
    print("\nBrowser instructions for manual data capture:")
    print("1. Open the search page: " + search_url)
    print("2. Fill in search criteria for eviction cases (often under 'Civil' or 'Housing' categories)")
    print("3. Execute the search and wait for results")
    print("4. Once results are displayed, save the page HTML:")
    print("   - Chrome: Right-click → View Page Source → Select all → Copy → Save to file")
    print("   - Firefox: Right-click → View Page Source → Save Page As")
    print("5. Save as 'search_results.html' in the current directory")
    
    # Prompt for the HTML file
    html_file = input("\nEnter path to the HTML file with search results (or press Enter for 'search_results.html'): ")
    if not html_file:
        html_file = "search_results.html"
    
    if not os.path.exists(html_file):
        print(f"Error: {html_file} not found. Please save the search results HTML first.")
        return
    
    print(f"Reading data from {html_file}...")
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Extract data using selectors
    eviction_records = scraper.extract_eviction_data(html_content, selectors)
    
    if not eviction_records:
        print("No eviction records found in the HTML. The selectors may need adjustment.")
        print("Try manually inspecting the HTML and create a custom selector file.")
        return
    
    print(f"Found {len(eviction_records)} eviction records!")
    
    # Analyze the data
    analysis = scraper.analyze_eviction_data(eviction_records)
    
    # Save the data
    scraper.save_eviction_data(eviction_records, analysis)
    
    # Generate a report
    report = scraper.generate_eviction_report(eviction_records, analysis)
    report_path = os.path.join(args.output_dir, f"eviction_report_{time.strftime('%Y%m%d_%H%M%S')}.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Report generated: {report_path}")
    print("\nNext steps:")
    print("1. Review the extracted data in the output directory")
    print("2. If needed, adjust the selectors and try again")
    print("3. For more detailed analysis, use the JSON and CSV files with other tools")

if __name__ == "__main__":
    main() 