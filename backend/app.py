from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from models import db, Job
import os
from dotenv import load_dotenv
from scraper import setup_scheduler, scrape_jobs, clear_all_jobs
import threading
import logging

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:123456789@localhost/job_listings')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/jobs', methods=['GET'])
def get_jobs():
    # Get query parameters for filtering and sorting
    location = request.args.get('location')
    company = request.args.get('company')
    sort_by = request.args.get('sort_by', 'date')  # Default sort by date
    
    # Start with a base query
    query = Job.query
    
    # Apply filters if provided
    if location:
        query = query.filter(Job.location.ilike(f'%{location}%'))
    if company:
        query = query.filter(Job.company.ilike(f'%{company}%'))
    
    # Apply sorting
    if sort_by == 'company':
        query = query.order_by(Job.company)
    elif sort_by == 'title':
        query = query.order_by(Job.title)
    elif sort_by == 'location':
        query = query.order_by(Job.location)
    else:  # Default to date
        query = query.order_by(Job.date_posted.desc())
    
    # Execute query and get results
    jobs = query.all()
    
    # Convert to JSON
    result = []
    for job in jobs:
        result.append({
            'id': job.id,
            'title': job.title,
            'company': job.company,
            'location': job.location,
            'description': job.description,
            'url': job.url,
            'date_posted': job.date_posted.strftime('%Y-%m-%d') if job.date_posted else None
        })
    
    return jsonify(result)

@app.route('/jobs', methods=['POST'])
def add_job():
    data = request.json
    
    # Create new job
    new_job = Job(
        title=data.get('title'),
        company=data.get('company'),
        location=data.get('location'),
        description=data.get('description'),
        url=data.get('url')
    )
    
    # Add to database
    db.session.add(new_job)
    db.session.commit()
    
    return jsonify({
        'id': new_job.id,
        'title': new_job.title,
        'company': new_job.company,
        'location': new_job.location,
        'description': new_job.description,
        'url': new_job.url,
        'date_posted': new_job.date_posted.strftime('%Y-%m-%d') if new_job.date_posted else None
    }), 201

@app.route('/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    db.session.delete(job)
    db.session.commit()
    
    return jsonify({'message': 'Job deleted successfully'}), 200

@app.route('/add-test-data', methods=['GET'])
def add_test_data():
    """Add test data to the database for development purposes."""
    test_jobs = [
        {
            "title": "Actuarial Analyst",
            "company": "Insurance Co",
            "location": "New York, NY",
            "description": "Entry level actuarial position",
            "url": "https://example.com/job1"
        },
        {
            "title": "Senior Actuary",
            "company": "Financial Services Inc",
            "location": "Chicago, IL",
            "description": "Senior actuarial role with 5+ years experience",
            "url": "https://example.com/job2"
        },
        {
            "title": "Actuarial Consultant",
            "company": "Consulting Firm",
            "location": "Remote",
            "description": "Consulting position for qualified actuaries",
            "url": "https://example.com/job3"
        }
    ]
    
    jobs_added = 0
    for job_data in test_jobs:
        # Check if job already exists
        existing_job = Job.query.filter_by(
            title=job_data["title"],
            company=job_data["company"],
            location=job_data["location"]
        ).first()
        
        if not existing_job:
            new_job = Job(
                title=job_data["title"],
                company=job_data["company"],
                location=job_data["location"],
                description=job_data["description"],
                url=job_data["url"]
            )
            db.session.add(new_job)
            jobs_added += 1
    
    db.session.commit()
    
    return jsonify({
        "message": f"Added {jobs_added} test jobs to the database",
        "total_jobs": Job.query.count()
    })

# New endpoints for scraper monitoring and control

@app.route('/scraper/status', methods=['GET'])
def scraper_status():
    """Get the status of the scraper and database."""
    # Count jobs in database
    job_count = Job.query.count()
    
    # Check if scraper log exists
    log_exists = os.path.exists('scraper.log')
    
    # Get the last few lines of the log if it exists
    recent_logs = []
    if log_exists:
        try:
            with open('scraper.log', 'r') as f:
                # Get last 20 lines
                lines = f.readlines()
                recent_logs = lines[-20:] if len(lines) > 20 else lines
        except Exception as e:
            recent_logs = [f"Error reading log: {str(e)}"]
    
    # Check for screenshots and HTML files
    screenshots = [f for f in os.listdir('.') if f.endswith('.png')]
    html_files = [f for f in os.listdir('.') if f.endswith('.html')]
    
    return jsonify({
        "job_count": job_count,
        "log_exists": log_exists,
        "recent_logs": recent_logs,
        "screenshots": screenshots,
        "html_files": html_files
    })

@app.route('/scraper/run', methods=['GET'])
def run_scraper():
    """Manually trigger the scraper."""
    # Run the scraper in a background thread with app context
    def run_with_app_context():
        with app.app_context():
            scrape_jobs(app)
    
    thread = threading.Thread(target=run_with_app_context)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "message": "Scraper started in background. Check /scraper/status for results."
    })

@app.route('/scraper/log', methods=['GET'])
def get_scraper_log():
    """Get the scraper log file."""
    if os.path.exists('scraper.log'):
        return send_file('scraper.log', mimetype='text/plain')
    else:
        return jsonify({"error": "Log file not found"}), 404

@app.route('/scraper/screenshot/<filename>', methods=['GET'])
def get_screenshot(filename):
    """Get a screenshot file."""
    if os.path.exists(filename) and filename.endswith('.png'):
        return send_file(filename, mimetype='image/png')
    else:
        return jsonify({"error": "Screenshot not found"}), 404

@app.route('/scraper/html/<filename>', methods=['GET'])
def get_html(filename):
    """Get an HTML file."""
    if os.path.exists(filename) and filename.endswith('.html'):
        return send_file(filename, mimetype='text/html')
    else:
        return jsonify({"error": "HTML file not found"}), 404

@app.route('/scraper/clear-jobs', methods=['POST'])
def clear_jobs():
    """Clear all jobs from the database."""
    try:
        success = clear_all_jobs(app)
        if success:
            return jsonify({"message": "All jobs cleared from database"})
        else:
            return jsonify({"error": "Error clearing jobs"}), 500
    except Exception as e:
        return jsonify({"error": f"Error clearing jobs: {str(e)}"}), 500

@app.route('/scraper/force-sample-jobs', methods=['POST'])
def force_sample_jobs():
    """Force add sample jobs regardless of database state."""
    try:
        with app.app_context():
            sample_jobs = [
                {
                    "title": "Actuarial Analyst",
                    "company": "Insurance Co",
                    "location": "New York, NY",
                    "description": "Entry level actuarial position requiring strong analytical skills and knowledge of statistical methods.",
                    "url": "https://www.actuarylist.com/sample-job1"
                },
                {
                    "title": "Senior Actuary",
                    "company": "Financial Services Inc",
                    "location": "Chicago, IL",
                    "description": "Senior actuarial role with 5+ years experience. Responsibilities include risk assessment and financial modeling.",
                    "url": "https://www.actuarylist.com/sample-job2"
                },
                {
                    "title": "Actuarial Consultant",
                    "company": "Consulting Firm",
                    "location": "Remote",
                    "description": "Consulting position for qualified actuaries. Work with clients to solve complex insurance and risk management problems.",
                    "url": "https://www.actuarylist.com/sample-job3"
                },
                {
                    "title": "Risk Analyst",
                    "company": "Global Insurance",
                    "location": "Boston, MA",
                    "description": "Risk analysis role focusing on property and casualty insurance products.",
                    "url": "https://www.actuarylist.com/sample-job4"
                },
                {
                    "title": "Actuarial Director",
                    "company": "Healthcare Solutions",
                    "location": "San Francisco, CA",
                    "description": "Leadership position overseeing actuarial team in healthcare insurance sector.",
                    "url": "https://www.actuarylist.com/sample-job5"
                }
            ]
            
            jobs_added = 0
            for job_data in sample_jobs:
                # Check if job already exists
                existing_job = Job.query.filter_by(
                    title=job_data["title"],
                    company=job_data["company"],
                    location=job_data["location"]
                ).first()
                
                if not existing_job:
                    new_job = Job(
                        title=job_data["title"],
                        company=job_data["company"],
                        location=job_data["location"],
                        description=job_data["description"],
                        url=job_data["url"]
                    )
                    db.session.add(new_job)
                    jobs_added += 1
            
            db.session.commit()
            
            return jsonify({
                "message": f"Added {jobs_added} sample jobs to the database",
                "total_jobs": Job.query.count()
            })
    except Exception as e:
        return jsonify({"error": f"Error adding sample jobs: {str(e)}"}), 500

if __name__ == '__main__':
    # Set up the scheduler after the app is created
    setup_scheduler(app)
    app.run(debug=True)
