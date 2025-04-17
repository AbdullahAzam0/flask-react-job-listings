import requests
from bs4 import BeautifulSoup
import json
import logging
import sys
from datetime import datetime
from models import db, Job
from flask import Flask
import re
import html

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("json_scraper.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def create_test_app():
    """Create a test Flask app for database operations."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456789@localhost/job_listings'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def extract_json_data():
    """Extract job listings JSON data from actuarylist.com."""
    logging.info("Starting JSON data extraction")
    
    # Use a realistic user agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Fetch the main page
        url = "https://www.actuarylist.com/"
        logging.info(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            logging.info(f"Successfully accessed {url}")
            
            # Save the HTML for reference
            with open("actuarylist_full_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
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
                                    
                                    # Save the filtered jobs for reference
                                    with open("filtered_jobs.json", "w", encoding="utf-8") as f:
                                        json.dump(filtered_jobs, f, indent=2)
                                    
                                    return filtered_jobs
                    except Exception as e:
                        logging.error(f"Error processing JSON script {i}: {str(e)}")
            
            # If we couldn't find JSON data in script tags, try to find it in the page content
            logging.info("Trying to find JSON data in page content")
            
            # Look for patterns that might indicate JSON data
            json_pattern = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.DOTALL)
            match = json_pattern.search(response.text)
            
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
                            
                            # Save the filtered jobs for reference
                            with open("filtered_jobs_next_data.json", "w", encoding="utf-8") as f:
                                json.dump(filtered_jobs, f, indent=2)
                            
                            return filtered_jobs
                except Exception as e:
                    logging.error(f"Error processing __NEXT_DATA__ JSON: {str(e)}")
        else:
            logging.error(f"Failed to access {url}, status code: {response.status_code}")
    
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
        logging.info(f"First job structure: {json.dumps(first_job, indent=2)}")
    
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

def main():
    """Main function to run the scraper."""
    logging.info("Starting JSON scraper")
    
    # Create a Flask app for database operations
    app = create_test_app()
    
    # Clear existing jobs
    clear_all_jobs(app)
    
    # Extract job data
    job_data = extract_json_data()
    
    # Process job data
    if job_data:
        jobs_added = process_job_data(job_data, app)
        logging.info(f"Scraping completed. Added {jobs_added} jobs.")
    else:
        logging.error("Failed to extract job data")
    
    logging.info("JSON scraper completed")

if __name__ == "__main__":
    main()
