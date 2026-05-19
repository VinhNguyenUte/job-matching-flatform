import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useJobStore } from '../lib/store'
import apiClient from '../lib/api'
import { Search, MapPin, Briefcase, DollarSign } from 'lucide-react'

export default function JobsPage() {
  // Lấy dữ liệu từ zustand store (Đảm bảo store khởi tạo filters mặc định là { search: '', city: '' })
  const { jobs, filters, setJobs, setFilters, isLoading, setLoading } = useJobStore()
  
  // SỬA LỖI ĐỀ PHÒNG: Đảm bảo local state không bị undefined khi store chưa kịp load
  const [localSearch, setLocalSearch] = useState(filters?.search || '')
  const [localCity, setLocalCity] = useState(filters?.city || '')

  useEffect(() => {
    fetchJobs()
  }, [filters])

  const fetchJobs = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      // Kiểm tra an toàn trước khi append query string
      if (filters?.search) params.append('q', filters.search)
      if (filters?.city) params.append('city', filters.city)

      const response = await apiClient.get(`/jobs/search?${params.toString()}`)
      
      if (response && response.data) {
        setJobs(response.data)
      }
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
      <form onSubmit={handleSearch} className="bg-white p-6 rounded-lg shadow border border-gray-100">
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
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center gap-2 font-medium transition"
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
          <div className="text-center py-12 text-gray-500">Loading jobs...</div>
        ) : !jobs || jobs.length === 0 ? (
          <div className="text-center py-12 text-gray-500 bg-white rounded-lg shadow">
            No jobs found. Try adjusting your search criteria.
          </div>
        ) : (
          jobs.map((job) => (
            <Link
              key={job.id}
              to={`/jobs/${job.id}`}
              className="block bg-white p-6 rounded-lg shadow hover:shadow-lg transition border border-gray-50"
            >
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-4 gap-2">
                <div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-1 hover:text-blue-600 transition">{job.title}</h3>
                  {/* FIX LỖI 1: job.company từ backend trả về một Object (CompanyResponse) */}
                  <p className="text-gray-600 text-lg font-medium">{job.company?.name || 'Unknown Company'}</p>
                </div>
                {job.salary_min && (
                  <div className="text-xl font-bold text-green-600 flex items-center gap-1">
                    <DollarSign size={20} />
                    {job.salary_min.toLocaleString()} - {job.salary_max?.toLocaleString()} {job.currency || 'VND'}
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-gray-500 border-b border-gray-100 pb-4">
                <div className="flex items-center gap-1.5">
                  <MapPin size={16} className="text-gray-400" />
                  {/* FIX LỖI 2: Backend trả về danh sách mảng `locations`. Ta lấy thành phố đầu tiên */}
                  {job.locations && job.locations.length > 0 
                    ? job.locations[0].city 
                    : 'Remote'}
                </div>
                <div className="flex items-center gap-1.5">
                  <Briefcase size={16} className="text-gray-400" />
                  {job.job_type || 'Full-time'}
                </div>
                <div className="bg-gray-100 px-2.5 py-0.5 rounded text-xs font-medium text-gray-600">
                  {job.experience_level || 'Not specified'}
                </div>
              </div>

              <p className="text-gray-600 mt-4 line-clamp-2 text-sm leading-relaxed">
                {job.description}
              </p>
            </Link>
          ))
        )}
      </div>
    </div>
  )
}