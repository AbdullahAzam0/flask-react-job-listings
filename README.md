# Actuarial Job Listings Application

A full-stack web application that automatically scrapes and displays actuarial job listings from websites like actuarylist.com. The application features a React frontend, Flask backend API, and a Python scraper that runs on a schedule to keep job listings up-to-date.

## Video Walkthrough

For a detailed explanation of the code and functionality, watch this video walkthrough:

[Loom Video: Job Listings Application Code Walkthrough](https://www.loom.com/share/ecd601e7f96143ffbe0ec1d9ab1fa1e1?sid=ae8912da-4fd3-4758-974a-c02ec1fa2cba)

## Architecture

The application follows a standard three-tier architecture:

\`\`\`mermaid
graph TD;
    A["Frontend (React)"] <--> B["Backend (Flask API)"]
    B <--> C["Database (PostgreSQL)"]
    D["Web Scraper"] --> B
    D --> E["External Job Website"]
\`\`\`

## Key Features

- **Automated Job Scraping**: Automatically scrapes job listings from actuarylist.com
- **Job Filtering**: Filter jobs by location, company, and other criteria
- **Responsive UI**: Mobile-friendly interface built with React and Tailwind CSS
- **Scheduled Updates**: Scraper runs every 3 minutes and at scheduled times
- **Manual Controls**: API endpoints to manually trigger scraping and manage jobs
- **Intelligent Data Extraction**: Extracts location data from job descriptions when not available in standard fields

## Technology Stack

### Backend
- **Flask**: Python web framework for the API
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Database for storing job listings
- **Selenium**: Browser automation for scraping
- **BeautifulSoup**: HTML parsing
- **Requests**: HTTP library for web requests
- **Schedule**: Job scheduling library

### Frontend
- **React**: JavaScript library for building the UI
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API requests
- **React Router**: Routing library for React

## File Structure

### Backend

- **app.py**: Main Flask application with API routes
- **models.py**: Database models using SQLAlchemy
- **scraper.py**: Main scraper using Selenium and BeautifulSoup
- **json_scraper.py**: Specialized scraper for JSON data extraction
- **direct_scraper.py**: Standalone scraper for website analysis

### Frontend

- **src/components/JobListings.tsx**: Main component for displaying job listings
- **src/components/JobCard.tsx**: Component for individual job cards
- **src/components/FilterBar.tsx**: Component for filtering jobs
- **src/components/AddJobForm.tsx**: Component for manually adding jobs
- **src/api/index.ts**: API client for communicating with the backend
- **src/types/index.ts**: TypeScript type definitions