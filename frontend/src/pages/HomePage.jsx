import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useJobStore } from '../lib/store'
import apiClient from '../lib/api'
import { Briefcase, MapPin, DollarSign, Sparkles } from 'lucide-react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { faRobot, faBolt, faBullseye } from '@fortawesome/free-solid-svg-icons'

export default function HomePage() {
  const { jobs, setJobs, isLoading, setLoading } = useJobStore()

  useEffect(() => {
    fetchFeaturedJobs()
  }, [])

  const fetchFeaturedJobs = async () => {
    setLoading(true)
    try {
      const response = await apiClient.get('/jobs/search?limit=6')
      
      if (response && response.data) {
        setJobs(response.data)
      }
    } catch (err) {
      console.error('Failed to fetch jobs:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-12">
      <section className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-20 px-4 rounded-lg">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-5xl font-bold mb-4">Find Your Dream Job</h1>
          <p className="text-xl mb-8">
            AI-powered job matching that understands your skills and aspirations
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link
              to="/jobs"
              className="px-8 py-3 bg-white text-blue-600 font-bold rounded-lg hover:bg-gray-100 transition"
            >
              Explore Jobs
            </Link>
            
            <Link
              to="/dashboard"
              className="px-8 py-3 bg-indigo-600 text-white font-bold rounded-lg border border-indigo-500 hover:bg-indigo-700 flex items-center gap-2 transition"
            >
              <Sparkles size={18} className="animate-pulse" />
              AI Job Recommendation
            </Link>
          </div>
        </div>
      </section>

      <section>
        <h2 className="text-3xl font-bold mb-8">Featured Jobs</h2>
        {isLoading ? (
          <div className="text-center py-12 text-gray-500">Loading jobs...</div>
        ) : !jobs || jobs.length === 0 ? (
          <div className="text-center py-12 text-gray-500">No featured jobs found.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {jobs.map((job) => (
              <Link
                key={job.id}
                to={`/jobs/${job.id}`}
                className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition flex flex-col justify-between border border-gray-100"
              >
                <div>
                  <h3 className="text-xl font-bold mb-2 line-clamp-1 text-gray-900">{job.title}</h3>
                  {/* SỬA LỖI 2.1: Truy cập thuộc tính name của object company */}
                  <p className="text-gray-600 mb-4 font-medium">{job.company?.name || 'Unknown Company'}</p>

                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <MapPin size={16} className="text-gray-400" />
                      {/* SỬA LỖI 2.2: Lấy phần tử thành phố từ mảng locations được gửi từ backend */}
                      {job.locations && job.locations.length > 0 
                        ? `${job.locations[0].city}${job.locations[0].building ? ` - ${job.locations[0].building}` : ''}`
                        : 'Remote'}
                    </div>
                    <div className="flex items-center gap-2">
                      <Briefcase size={16} className="text-gray-400" />
                      {job.job_type || 'Full-time'}
                    </div>
                    {job.salary_min && (
                      <div className="flex items-center gap-2 text-green-600 font-medium">
                        <DollarSign size={16} />
                        {job.salary_min.toLocaleString()} - {job.salary_max?.toLocaleString()} {job.currency || 'VND'}
                      </div>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Why JobMatch Section */}
      <section className="bg-gray-50 py-12 px-4 rounded-lg">
        <h2 className="text-3xl font-bold mb-8 text-center">Why JobMatch?</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="text-4xl mb-4 text-blue-600">
              <FontAwesomeIcon icon={faRobot} />
            </div>
            <h3 className="font-bold mb-2">AI-Powered</h3>
            <p className="text-gray-600 text-sm">Smart matching based on your skills and experience</p>
          </div>
          
          <div className="text-center">
            <div className="text-4xl mb-4 text-yellow-500">
              <FontAwesomeIcon icon={faBolt} />
            </div>
            <h3 className="font-bold mb-2">Fast & Easy</h3>
            <p className="text-gray-600 text-sm">Find relevant opportunities in seconds</p>
          </div>
          
          <div className="text-center">
            <div className="text-4xl mb-4 text-red-500">
              <FontAwesomeIcon icon={faBullseye} />
            </div>
            <h3 className="font-bold mb-2">Accurate</h3>
            <p className="text-gray-600 text-sm">Precise matching for better opportunities</p>
          </div>
        </div>
      </section>
    </div>
  )
}