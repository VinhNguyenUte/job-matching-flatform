import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useJobStore } from '../lib/store'
import apiClient from '../lib/api'
import { Search, MapPin } from 'lucide-react'

export default function JobsPage() {
  const { jobs, filters, setJobs, setFilters, isLoading, setLoading } = useJobStore()
  const [localSearch, setLocalSearch] = useState(filters.search)
  const [localCity, setLocalCity] = useState(filters.city)

  useEffect(() => {
    fetchJobs()
  }, [filters])

  const fetchJobs = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (filters.search) params.append('q', filters.search)
      if (filters.city) params.append('city', filters.city)

      const response = await apiClient.get(`/jobs/search?${params}`)
      setJobs(response.data)
    } catch (err) {
      console.error('Failed to fetch jobs:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setFilters({ search: localSearch, city: localCity })
  }

  return (
    <div className="space-y-8">
      {/* Search Form */}
      <form onSubmit={handleSearch} className="bg-white p-6 rounded-lg shadow">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Job Title
            </label>
            <input
              type="text"
              value={localSearch}
              onChange={(e) => setLocalSearch(e.target.value)}
              placeholder="e.g. React Developer"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Location
            </label>
            <input
              type="text"
              value={localCity}
              onChange={(e) => setLocalCity(e.target.value)}
              placeholder="e.g. Ho Chi Minh"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2"
            >
              <Search size={20} />
              Search
            </button>
          </div>
        </div>
      </form>

      {/* Jobs List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="text-center py-12">Loading jobs...</div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No jobs found. Try adjusting your search criteria.
          </div>
        ) : (
          jobs.map((job) => (
            <Link
              key={job.id}
              to={`/jobs/${job.id}`}
              className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-2xl font-bold mb-2">{job.title}</h3>
                  <p className="text-gray-600 text-lg">{job.company}</p>
                </div>
                {job.salary_min && (
                  <div className="text-xl font-bold text-blue-600">
                    ${job.salary_min} - ${job.salary_max}
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-4 text-gray-600">
                <div className="flex items-center gap-2">
                  <MapPin size={18} />
                  {job.location}
                </div>
                <div>{job.job_type || 'Full-time'}</div>
                <div>{job.experience_level || 'Not specified'}</div>
              </div>

              <p className="text-gray-600 mt-4 line-clamp-2">{job.description}</p>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}
