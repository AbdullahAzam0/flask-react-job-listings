from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import schedule
import threading
import logging
from datetime import datetime
from models import db, Job
import os
import traceback
import requests
from bs4 import BeautifulSoup
import json
import re

# Configure logging
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_driver():
    """Set up and return a configured Chrome WebDriver."""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Add user agent to avoid detection
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Install ChromeDriver if not already installed
        service = Service(ChromeDriverManager().install())
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        logging.error(f"Error setting up WebDriver: {str(e)}")
        logging.error(traceback.format_exc())
        return None

def extract_json_data(html_content):
    """Extract job listings JSON data from HTML content."""
    logging.info("Extracting JSON data from HTML")
    
    try:
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find script tags with JSON data
        json_scripts = soup.find_all('script', type="application/json")
        logging.info(f"Found {len(json_scripts)} JSON script tags")
        
        if json_scripts:
            # Process each JSON script
            for i, script in enumerate(json_scripts):
                try:
                    # Extract the JSON content
                    json_content = script.string
                    if json_content:
                        # Try to parse as JSON
                        json_data = json.loads(json_content)
                        
                        # Save the full JSON for reference
                        with open(f"job_data_full_{i}.json", "w", encoding="utf-8") as f:
                            json.dump(json_data, f, indent=2)
                        
                        # Check if this contains job data
                        if "props" in json_data and "pageProps" in json_data["props"]:
                            page_props = json_data["props"]["pageProps"]
                            
                            # Check for job count
                            if "jobCount" in page_props:
                                job_count = page_props["jobCount"]
                                logging.info(f"Found job count: {job_count}")
                            
                            # Check for filtered jobs
                            if "filteredJobs" in page_props:
                                filtered_jobs = page_props["filteredJobs"]
                                logging.info(f"Found {len(filtered_jobs)} filtered jobs")
                                return filtered_jobs
                except Exception as e:
                    logging.error(f"Error processing JSON script {i}: {str(e)}")
        
        # If we couldn't find JSON data in script tags, try to find it in the page content
        logging.info("Trying to find JSON data in page content")
        
        # Look for patterns that might indicate JSON data
        json_pattern = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.DOTALL)
        match = json_pattern.search(html_content)
        
        if match:
            try:
                json_content = match.group(1)
                json_data = json.loads(json_content)
                
                # Save the full JSON for reference
                with open("next_data_full.json", "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=2)
                
                # Try to find job data in the JSON
                if "props" in json_data and "pageProps" in json_data["props"]:
                    page_props = json_data["props"]["pageProps"]
                    
                    # Check for filtered jobs
                    if "filteredJobs" in page_props:
                        filtered_jobs = page_props["filteredJobs"]
                        logging.info(f"Found {len(filtered_jobs)} filtered jobs in __NEXT_DATA__")
                        return filtered_jobs
            except Exception as e:
                logging.error(f"Error processing __NEXT_DATA__ JSON: {str(e)}")
    
    except Exception as e:
        logging.error(f"Error during JSON extraction: {str(e)}")
    
    return None

def clean_html_description(html_content):
    """Clean HTML content for description."""
    if not html_content:
        return "No description available"
    
    # Create a summary from the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract text and remove extra whitespace
    text = soup.get_text(separator=' ', strip=True)
    
    # Limit to a reasonable length for description
    if len(text) > 500:
        text = text[:497] + "..."
    
    return text

def process_job_data(job_data, app):
    """Process job data and add to database."""
    if not job_data:
        logging.error("No job data to process")
        return 0
    
    logging.info(f"Processing {len(job_data)} jobs")
    jobs_added = 0
    
    # First, let's examine the structure of the first job
    if job_data and len(job_data) > 0:
        first_job = job_data[0]
        logging.info(f"First job structure: {json.dumps(first_job, indent=2)[:1000]}...")
    
    with app.app_context():
        for job in job_data:
            try:
                # Extract job details based on the actual JSON structure
                job_id = job.get("id")
                
                # Extract title - it should be directly in the job object
                title = job.get("title")
                if not title or title == "Unknown Title":
                    # Try to find title in other fields
                    if "position" in job:
                        title = job["position"]
                    elif "name" in job:
                        title = job["name"]
                
                # Extract company - it might be nested or a direct field
                company = "Unknown Company"
                company_data = job.get("company")
                if isinstance(company_data, dict) and "name" in company_data:
                    company = company_data["name"]
                elif isinstance(company_data, str):
                    company = company_data
                
                # Extract location - it might be nested or a direct field
                location = "Unknown Location"
                location_data = job.get("location")
                if isinstance(location_data, dict) and "name" in location_data:
                    location = location_data["name"]
                elif isinstance(location_data, str):
                    location = location_data
                
                # Extract and clean description
                description = job.get("description", "")
                if description:
                    # Clean HTML content
                    description = clean_html_description(description)
                else:
                    description = "No description available"
                
                # Build URL
                url = f"https://www.actuarylist.com/jobs/{job_id}" if job_id else "https://www.actuarylist.com/"
                
                logging.info(f"Extracted job: {title} at {company} in {location}")
                
                # Check if job already exists in database
                existing_job = Job.query.filter_by(
                    title=title,
                    company=company,
                    location=location
                ).first()
                
                if not existing_job:
                    # Create new job record
                    new_job = Job(
                        title=title,
                        company=company,
                        location=location,
                        description=description,
                        url=url
                    )
                    
                    # Add to database
                    db.session.add(new_job)
                    jobs_added += 1
            except Exception as e:
                logging.error(f"Error processing job: {str(e)}")
        
        # Commit all new jobs to the database
        if jobs_added > 0:
            db.session.commit()
            logging.info(f"Added {jobs_added} new jobs to the database")
    
    return jobs_added

def scrape_with_requests(app):
    """Try to scrape using requests and BeautifulSoup as a fallback."""
    logging.info("Attempting to scrape with requests/BeautifulSoup")
    
    try:
        # Use a realistic user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make the request
        response = requests.get('https://www.actuarylist.com/', headers=headers)
        
        # Save the HTML for analysis
        with open('requests_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        logging.info(f"Got response with status code: {response.status_code}")
        
        # Extract JSON data from the HTML
        job_data = extract_json_data(response.text)
        
        # Process job data
        if job_data:
            jobs_added = process_job_data(job_data, app)
            return jobs_added > 0
        
        return False
    except Exception as e:
        logging.error(f"Error in requests/BeautifulSoup scraping: {str(e)}")
        logging.error(traceback.format_exc())
        return False

def clear_all_jobs(app):
    """Clear all jobs from the database."""
    with app.app_context():
        try:
            job_count = Job.query.count()
            logging.info(f"Clearing {job_count} jobs from database")
            Job.query.delete()
            db.session.commit()
            logging.info("All jobs cleared from database")
            return True
        except Exception as e:
            logging.error(f"Error clearing jobs: {str(e)}")
            return False

def scrape_jobs(app):
    """Scrape job listings from actuarylist.com."""
    logging.info("Starting job scraping process")
    start_time = datetime.now()
    
    # Clear existing jobs first
    clear_all_jobs(app)
    
    # Try with Selenium first
    driver = setup_driver()
    if not driver:
        logging.error("Failed to set up WebDriver. Trying alternative method.")
        success = scrape_with_requests(app)
        return
    
    try:
        # Navigate to the website
        driver.get("https://www.actuarylist.com/")
        logging.info("Navigated to actuarylist.com")
        
        # Wait for the page to load
        logging.info(f"Page title: {driver.title}")
        
        # Take a screenshot for debugging
        driver.save_screenshot("page_screenshot.png")
        logging.info("Saved page screenshot as page_screenshot.png")
        
        # Wait for the page to fully load
        time.sleep(5)
        
        # Get the page source for analysis
        page_source = driver.page_source
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        logging.info("Saved page source for analysis")
        
        # Extract JSON data from the page source
        job_data = extract_json_data(page_source)
        
        # Process job data
        if job_data:
            jobs_added = process_job_data(job_data, app)
            if jobs_added > 0:
                logging.info(f"Successfully added {jobs_added} jobs from JSON data")
                return
        
        # If JSON extraction failed, try with requests/BeautifulSoup
        logging.info("JSON extraction failed. Trying with requests/BeautifulSoup.")
        success = scrape_with_requests(app)
    
    except Exception as e:
        logging.error(f"Error during scraping: {str(e)}")
        logging.error(traceback.format_exc())
        
        # Try with requests/BeautifulSoup as a fallback
        success = scrape_with_requests(app)
    finally:
        if driver:
            driver.quit()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logging.info(f"Scraping completed in {duration} seconds")

def run_scheduler(app):
    """Run the scheduler in a separate thread."""
    while True:
        schedule.run_pending()
        time.sleep(1)

def scheduled_scrape(app):
    """Function to run the scraper with app context."""
    with app.app_context():
        scrape_jobs(app)

def setup_scheduler(app):
    """Set up the scheduler for periodic scraping."""
    # Schedule scraping every 3 minutes for testing
    schedule.every(3).minutes.do(lambda: scheduled_scrape(app))
    
    # Schedule scraping at specific times
    schedule.every().day.at("00:00").do(lambda: scheduled_scrape(app))  # 12 AM
    schedule.every().day.at("03:00").do(lambda: scheduled_scrape(app))  # 3 AM
    schedule.every().day.at("06:00").do(lambda: scheduled_scrape(app))  # 6 AM
    
    # Run the scheduler in a separate thread
    scheduler_thread = threading.Thread(target=lambda: run_scheduler(app))
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    # Don't run immediately at startup - let the app context initialize first
    logging.info("Scheduler set up successfully")
