import axios from "axios"
import type { Job, JobFilters } from "../types"

const API_URL = "http://localhost:5000"

export const fetchJobs = async (filters: JobFilters = {}) => {
  try {
    const params = new URLSearchParams()

    if (filters.location) params.append("location", filters.location)
    if (filters.company) params.append("company", filters.company)
    if (filters.sort_by) params.append("sort_by", filters.sort_by)

    const response = await axios.get(`${API_URL}/jobs`, { params })
    return response.data
  } catch (error) {
    console.error("Error fetching jobs:", error)
    throw error
  }
}

export const addJob = async (job: Omit<Job, "id" | "date_posted">) => {
  try {
    const response = await axios.post(`${API_URL}/jobs`, job)
    return response.data
  } catch (error) {
    console.error("Error adding job:", error)
    throw error
  }
}

export const deleteJob = async (id: number) => {
  try {
    const response = await axios.delete(`${API_URL}/jobs/${id}`)
    return response.data
  } catch (error) {
    console.error("Error deleting job:", error)
    throw error
  }
}
