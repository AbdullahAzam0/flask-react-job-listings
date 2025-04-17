export interface Job {
  id: number
  title: string
  company: string
  location: string
  description: string
  url: string
  date_posted: string
}

export interface JobFilters {
  location?: string
  company?: string
  sort_by?: "date" | "company" | "title" | "location"
}
