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
from urllib.parse import urlparse, urljoin

class WebScraperAgent:
    def __init__(self, base_url, output_dir="scraped_data", delay=2):
        """Initialize the web scraper agent.
        
        Args:
            base_url: The base URL to scrape
            output_dir: Directory to save scraped data
            delay: Seconds to wait between requests (to be respectful)
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
                logging.FileHandler("scraper.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("WebScraperAgent")
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Set a user agent to identify the bot (ethical practice)
        self.session.headers.update({
            "User-Agent": "WebScraperAgent/1.0 (Educational Research Project; +https://yourwebsite.com/contact)",
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Language": "en-US,en;q=0.9",
        })
    
    def login(self, login_url, username, password, username_field="username", password_field="password"):
        """Log in to the website.
        
        Args:
            login_url: URL of the login page
            username: Username to use
            password: Password to use
            username_field: HTML field name for username
            password_field: HTML field name for password
        
        Returns:
            bool: Whether login was successful
        """
        self.logger.info(f"Attempting to log in to {login_url}")
        
        # First, get the login page to capture any CSRF tokens
        response = self.session.get(login_url)
        if response.status_code != 200:
            self.logger.error(f"Failed to access login page: {response.status_code}")
            return False
        
        # Parse the login page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for common CSRF token patterns
        csrf_token = None
        for input_tag in soup.find_all('input'):
            if input_tag.get('name') and ('csrf' in input_tag.get('name').lower() or 
                                         'token' in input_tag.get('name').lower()):
                csrf_token = input_tag.get('value')
                self.logger.info(f"Found CSRF token: {input_tag.get('name')}")
                break
        
        # Prepare login data
        login_data = {
            username_field: username,
            password_field: password
        }
        
        # Add CSRF token if found
        if csrf_token:
            login_data['csrf_token'] = csrf_token
        
        # Attempt login
        time.sleep(self.delay)  # Be respectful with timing
        response = self.session.post(login_url, data=login_data, allow_redirects=True)
        
        # Check if login was successful (this is a simple check, might need customization)
        if response.url != login_url and "login" not in response.url.lower():
            self.logger.info("Login appears successful")
            return True
        else:
            self.logger.error("Login failed")
            return False
    
    def scrape_page(self, url, selectors=None):
        """Scrape data from a specific page.
        
        Args:
            url: URL to scrape
            selectors: Dictionary of CSS selectors to extract specific data
                       Example: {"products": ".product-item", "titles": ".product-title"}
                       
        Returns:
            dict: Scraped data and metadata
        """
        if url in self.visited_urls:
            self.logger.info(f"Already visited {url}, skipping")
            return None
        
        self.visited_urls.add(url)
        
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = urljoin(self.base_url, url)
        
        self.logger.info(f"Scraping {url}")
        
        # Add random delay to be respectful
        time.sleep(self.delay + random.uniform(0, 1))
        
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code != 200:
                self.logger.error(f"Failed to retrieve {url}: {response.status_code}")
                return None
            
            # Parse the page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Basic metadata
            data = {
                "url": url,
                "title": soup.title.string if soup.title else "No title",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            # Extract data based on provided selectors
            if selectors:
                for name, selector in selectors.items():
                    elements = soup.select(selector)
                    if elements:
                        data[name] = [elem.get_text(strip=True) for elem in elements]
                    else:
                        data[name] = []
            
            # Extract links for potential further crawling
            data["links"] = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Filter out external links, anchors, etc.
                if href.startswith('#') or 'javascript:' in href:
                    continue
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(url, href)
                if self.domain in urlparse(href).netloc:  # Only include internal links
                    data["links"].append(href)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            return None
    
    def crawl(self, start_url, max_pages=10, selectors=None, follow_links=True):
        """Crawl the website starting from a specific URL.
        
        Args:
            start_url: URL to start crawling from
            max_pages: Maximum number of pages to crawl
            selectors: Dictionary of CSS selectors for data extraction
            follow_links: Whether to follow links found on pages
            
        Returns:
            list: All scraped data
        """
        to_visit = [start_url]
        results = []
        pages_crawled = 0
        
        self.logger.info(f"Starting crawl from {start_url}, max pages: {max_pages}")
        
        while to_visit and pages_crawled < max_pages:
            url = to_visit.pop(0)
            data = self.scrape_page(url, selectors)
            
            if data:
                results.append(data)
                pages_crawled += 1
                
                self.logger.info(f"Crawled {pages_crawled}/{max_pages} pages")
                
                # Save incremental results
                if pages_crawled % 5 == 0:
                    self.save_data(results, "incremental")
                
                # Follow links if enabled
                if follow_links and "links" in data:
                    # Add new links to visit
                    for link in data["links"]:
                        if link not in self.visited_urls and link not in to_visit:
                            to_visit.append(link)
        
        self.logger.info(f"Crawl completed. Visited {pages_crawled} pages.")
        return results
    
    def save_data(self, data, prefix="scraped"):
        """Save the scraped data in multiple formats.
        
        Args:
            data: List of dictionaries containing scraped data
            prefix: Prefix for output filenames
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON
        json_path = os.path.join(self.output_dir, f"{prefix}_{timestamp}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Data saved to {json_path}")
        
        # Save as CSV (for first level of data only)
        if data and isinstance(data[0], dict):
            # Get all possible keys
            all_keys = set()
            for item in data:
                all_keys.update(k for k, v in item.items() if isinstance(v, (str, int, float, bool)))
            
            if all_keys:
                csv_path = os.path.join(self.output_dir, f"{prefix}_{timestamp}.csv")
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
                    writer.writeheader()
                    for item in data:
                        # Only write simple values, not lists or dicts
                        row = {k: v for k, v in item.items() if k in all_keys}
                        writer.writerow(row)
                
                self.logger.info(f"Data saved to {csv_path}")

def main():
    parser = argparse.ArgumentParser(description="Ethical Web Scraper Agent")
    parser.add_argument("url", help="Base URL to scrape")
    parser.add_argument("--login", action="store_true", help="Perform login before scraping")
    parser.add_argument("--login-url", help="Login page URL")
    parser.add_argument("--username", help="Username for login")
    parser.add_argument("--password", help="Password for login")
    parser.add_argument("--selector", action="append", nargs=2, metavar=("NAME", "SELECTOR"),
                        help="Add a CSS selector to extract (can be used multiple times)")
    parser.add_argument("--max-pages", type=int, default=10, help="Maximum pages to crawl")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between requests in seconds")
    parser.add_argument("--output-dir", default="scraped_data", help="Output directory for scraped data")
    
    args = parser.parse_args()
    
    # Create selector dictionary from arguments
    selectors = {}
    if args.selector:
        for name, selector in args.selector:
            selectors[name] = selector
    
    # Create and configure the scraper
    scraper = WebScraperAgent(args.url, output_dir=args.output_dir, delay=args.delay)
    
    # Perform login if requested
    if args.login:
        if not all([args.login_url, args.username, args.password]):
            print("Error: login-url, username, and password are required for login")
            return
        
        success = scraper.login(args.login_url, args.username, args.password)
        if not success:
            print("Login failed. Exiting.")
            return
    
    # Start crawling
    data = scraper.crawl(args.url, max_pages=args.max_pages, selectors=selectors)
    
    # Save final results
    scraper.save_data(data, "final")
    
    print(f"Scraping completed. Visited {len(scraper.visited_urls)} pages.")
    print(f"Results saved to {args.output_dir} directory.")

if __name__ == "__main__":
    main() 