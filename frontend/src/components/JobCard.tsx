"use client"

import type { Job } from "../types"

interface JobCardProps {
  job: Job
  onDelete: () => void
}

const JobCard = ({ job, onDelete }: JobCardProps) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow">
      <div className="p-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">{job.title || "Untitled Position"}</h2>
            <div className="flex items-center text-gray-600 mb-2">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M10 2a8 8 0 100 16 8 8 0 000-16zm0 14a6 6 0 100-12 6 6 0 000 12z"
                  clipRule="evenodd"
                />
              </svg>
              <span>{job.company || "Unknown Company"}</span>
            </div>
            <div className="flex items-center text-gray-600 mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M5.05 4.05a7 7 0 119.9 9.9L10 18.9l-4.95-4.95a7 7 0 010-9.9zM10 11a2 2 0 100-4 2 2 0 000 4z"
                  clipRule="evenodd"
                />
              </svg>
              <span>{job.location || "Unknown Location"}</span>
            </div>
            <p className="text-gray-700 mb-4">{job.description || "No description available"}</p>
            <div className="text-sm text-gray-500">Posted on: {new Date(job.date_posted).toLocaleDateString()}</div>
          </div>
          <div className="flex space-x-2">
            <a href={job.url} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
              Apply
            </a>
            <button onClick={onDelete} className="btn btn-danger" aria-label="Delete job">
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default JobCard
