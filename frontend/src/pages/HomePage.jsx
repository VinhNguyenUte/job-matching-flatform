import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useJobStore } from '../lib/store'
import apiClient from '../lib/api'
import { Briefcase, MapPin, DollarSign } from 'lucide-react'

export default function HomePage() {
  const { jobs, setJobs, isLoading, setLoading } = useJobStore()

  useEffect(() => {
    fetchFeaturedJobs()
  }, [])

  const fetchFeaturedJobs = async () => {
    setLoading(true)
    try {
      const response = await apiClient.get('/jobs/search?limit=6')
      setJobs(response.data)
    } catch (err) {
      console.error('Failed to fetch jobs:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-20 px-4 rounded-lg">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-5xl font-bold mb-4">Find Your Dream Job</h1>
          <p className="text-xl mb-8">
            AI-powered job matching that understands your skills and aspirations
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              to="/jobs"
              className="px-8 py-3 bg-white text-blue-600 font-bold rounded-lg hover:bg-gray-100"
            >
              Explore Jobs
            </Link>
          </div>
        </div>
      </section>

      {/* Featured Jobs */}
      <section>
        <h2 className="text-3xl font-bold mb-8">Featured Jobs</h2>
        {isLoading ? (
          <div className="text-center py-12">Loading jobs...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {jobs.map((job) => (
              <Link
                key={job.id}
                to={`/jobs/${job.id}`}
                className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition"
              >
                <h3 className="text-xl font-bold mb-2">{job.title}</h3>
                <p className="text-gray-600 mb-4">{job.company}</p>

                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex items-center gap-2">
                    <MapPin size={16} />
                    {job.location}
                  </div>
                  <div className="flex items-center gap-2">
                    <Briefcase size={16} />
                    {job.job_type || 'Full-time'}
                  </div>
                  {job.salary_min && (
                    <div className="flex items-center gap-2">
                      <DollarSign size={16} />
                      {job.salary_min} - {job.salary_max} {job.currency}
                    </div>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>

      {/* Features */}
      <section className="bg-gray-50 py-12 px-4 rounded-lg">
        <h2 className="text-3xl font-bold mb-8 text-center">Why JobMatch?</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="font-bold mb-2">AI-Powered</h3>
            <p>Smart matching based on your skills and experience</p>
          </div>
          <div className="text-center">
            <div className="text-4xl mb-4">⚡</div>
            <h3 className="font-bold mb-2">Fast & Easy</h3>
            <p>Find relevant opportunities in seconds</p>
          </div>
          <div className="text-center">
            <div className="text-4xl mb-4">🎯</div>
            <h3 className="font-bold mb-2">Accurate</h3>
            <p>Precise matching for better opportunities</p>
          </div>
        </div>
      </section>
    </div>
  )
}
