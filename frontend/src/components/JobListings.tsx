"use client"

import { useState, useEffect } from "react"
import { fetchJobs, deleteJob } from "../api"
import type { Job, JobFilters } from "../types"
import JobCard from "./JobCard"
import FilterBar from "./FilterBar"

const JobListings = () => {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<JobFilters>({
    sort_by: "date",
  })

  useEffect(() => {
    const getJobs = async () => {
      try {
        setLoading(true)
        const data = await fetchJobs(filters)
        setJobs(data)
        setError(null)
      } catch (err) {
        setError("Failed to fetch jobs. Please try again later.")
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    getJobs()
  }, [filters])

  const handleDeleteJob = async (id: number) => {
    try {
      await deleteJob(id)
      setJobs(jobs.filter((job) => job.id !== id))
    } catch (err) {
      setError("Failed to delete job. Please try again.")
      console.error(err)
    }
  }

  const handleFilterChange = (newFilters: JobFilters) => {
    setFilters({ ...filters, ...newFilters })
  }

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Available Job Listings</h1>

        <FilterBar filters={filters} onFilterChange={handleFilterChange} />

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mt-4" role="alert">
            <p>{error}</p>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
          </div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">
              No job listings found. Try adjusting your filters or check back later.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 mt-6">
            {jobs.map((job) => (
              <JobCard key={job.id} job={job} onDelete={() => handleDeleteJob(job.id)} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default JobListings
