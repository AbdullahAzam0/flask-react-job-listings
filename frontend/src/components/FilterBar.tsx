"use client"

import { useState, useEffect } from "react"
import type { JobFilters } from "../types"
import { fetchJobs } from "../api"

interface FilterBarProps {
  filters: JobFilters
  onFilterChange: (filters: JobFilters) => void
}

const FilterBar = ({ filters, onFilterChange }: FilterBarProps) => {
  const [locations, setLocations] = useState<string[]>([])
  const [companies, setCompanies] = useState<string[]>([])
  const [location, setLocation] = useState(filters.location || "")
  const [company, setCompany] = useState(filters.company || "")
  const [sortBy, setSortBy] = useState(filters.sort_by || "date")

  useEffect(() => {
    // Fetch unique locations and companies for filter dropdowns
    const fetchFilterOptions = async () => {
      try {
        const jobs = await fetchJobs()

        // Extract unique locations
        const uniqueLocations = Array.from(new Set(jobs.map((job: any) => job.location))).filter(Boolean)

        // Extract unique companies
        const uniqueCompanies = Array.from(new Set(jobs.map((job: any) => job.company))).filter(Boolean)

        setLocations(uniqueLocations)
        setCompanies(uniqueCompanies)
      } catch (error) {
        console.error("Error fetching filter options:", error)
      }
    }

    fetchFilterOptions()
  }, [])

  const handleApplyFilters = () => {
    onFilterChange({
      location,
      company,
      sort_by: sortBy as JobFilters["sort_by"],
    })
  }

  const handleClearFilters = () => {
    setLocation("")
    setCompany("")
    setSortBy("date")
    onFilterChange({
      sort_by: "date",
    })
  }

  return (
    <div className="bg-gray-50 p-4 rounded-lg border border-gray-200 mb-6">
      <h2 className="text-lg font-semibold text-gray-700 mb-4">Filter Jobs</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div>
          <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
            Location
          </label>
          <select
            id="location"
            className="select w-full"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          >
            <option value="">All Locations</option>
            {locations.map((loc) => (
              <option key={loc} value={loc}>
                {loc}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="company" className="block text-sm font-medium text-gray-700 mb-1">
            Company
          </label>
          <select id="company" className="select w-full" value={company} onChange={(e) => setCompany(e.target.value)}>
            <option value="">All Companies</option>
            {companies.map((comp) => (
              <option key={comp} value={comp}>
                {comp}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="sortBy" className="block text-sm font-medium text-gray-700 mb-1">
            Sort By
          </label>
          <select id="sortBy" className="select w-full" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="date">Date Posted</option>
            <option value="company">Company</option>
            <option value="title">Job Title</option>
            <option value="location">Location</option>
          </select>
        </div>
      </div>

      <div className="flex justify-end space-x-2">
        <button onClick={handleClearFilters} className="btn btn-secondary">
          Clear Filters
        </button>
        <button onClick={handleApplyFilters} className="btn btn-primary">
          Apply Filters
        </button>
      </div>
    </div>
  )
}

export default FilterBar
