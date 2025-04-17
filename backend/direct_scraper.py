import requests
from bs4 import BeautifulSoup
import logging
import json
import os
from datetime import datetime
import sys
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("direct_scraper.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def save_html(html, filename):
    """Save HTML content to a file for analysis."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    logging.info(f"Saved HTML to {filename}")

def analyze_website():
    """Analyze the actuarylist.com website structure."""
    logging.info("Starting website analysis")
    
    # URLs to check
    urls = [
        "https://www.actuarylist.com/",
        "https://www.actuarylist.com/jobs",
        "https://www.actuarylist.com/job-listings",
        "https://www.actuarylist.com/actuarial-jobs",
        "https://www.actuarylist.com/search"
    ]
    
    # Use a realistic user agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for url in urls:
        try:
            logging.info(f"Checking URL: {url}")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                logging.info(f"Successfully accessed {url}")
                
                # Save the HTML for analysis
                filename = f"analysis_{url.replace('https://', '').replace('http://', '').replace('/', '_')}.html"
                save_html(response.text, filename)
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Log the page title
                page_title = soup.title.text if soup.title else "No title found"
                logging.info(f"Page title: {page_title}")
                
                # Look for common job listing elements
                tables = soup.find_all('table')
                logging.info(f"Found {len(tables)} tables")
                
                job_related_divs = soup.find_all('div', class_=lambda c: c and ('job' in c.lower() or 'listing' in c.lower()))
                logging.info(f"Found {len(job_related_divs)} job-related divs")
                
                # Look for links that might point to job listings
                job_links = soup.find_all('a', href=lambda href: href and ('job' in href.lower() or 'position' in href.lower() or 'career' in href.lower()))
                logging.info(f"Found {len(job_links)} job-related links")
                
                # Check for forms that might be search forms
                forms = soup.find_all('form')
                logging.info(f"Found {len(forms)} forms")
                
                # Check for iframes that might contain job listings
                iframes = soup.find_all('iframe')
                logging.info(f"Found {len(iframes)} iframes")
                
                # Look for script tags that might load job data
                scripts = soup.find_all('script', type="application/json")
                logging.info(f"Found {len(scripts)} JSON script tags")
                
                # Check for any JSON data in script tags
                for script in scripts:
                    try:
                        script_content = script.string
                        if script_content:
                            # Try to parse as JSON
                            try:
                                json_data = json.loads(script_content)
                                logging.info(f"Found JSON data in script: {json.dumps(json_data)[:200]}...")
                                
                                # Save the JSON data for analysis
                                with open(f"json_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
                                    json.dump(json_data, f, indent=2)
                            except json.JSONDecodeError:
                                pass
                    except Exception as e:
                        logging.error(f"Error processing script tag: {str(e)}")
                
                # Look for any text that might indicate job listings
                text = soup.get_text()
                job_related_text = re.findall(r'(?i)(?:job|position|career|opening|vacancy)(?:[^\n.]{0,50})', text)
                if job_related_text:
                    logging.info(f"Found {len(job_related_text)} job-related text snippets")
                    for i, snippet in enumerate(job_related_text[:10]):  # Log first 10 snippets
                        logging.info(f"Text snippet {i+1}: {snippet.strip()}")
            else:
                logging.warning(f"Failed to access {url}, status code: {response.status_code}")
        except Exception as e:
            logging.error(f"Error checking {url}: {str(e)}")
    
    logging.info("Website analysis completed")

if __name__ == "__main__":
    analyze_website()
