import { useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'
import apiClient from '../lib/api'
import { useAuthStore } from '../lib/store'
import { MapPin, DollarSign, Briefcase } from 'lucide-react'

export default function JobDetailPage() {
  const { id } = useParams()
  const { user } = useAuthStore()
  const [job, setJob] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isApplying, setIsApplying] = useState(false)

  useEffect(() => {
    fetchJobDetail()
  }, [id])

  const fetchJobDetail = async () => {
    try {
      const response = await apiClient.get(`/jobs/${id}`)
      setJob(response.data)
    } catch (err) {
      setError('Failed to load job details')
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleApply = async () => {
    if (!user) {
      alert('Please login to apply')
      return
    }

    setIsApplying(true)
    try {
      await apiClient.post(`/jobs/${id}/apply`)
      alert('Application submitted successfully!')
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to apply')
    } finally {
      setIsApplying(false)
    }
  }

  if (isLoading) return <div className="py-12 text-center">Loading...</div>
  if (error) return <div className="py-12 text-center text-red-600">{error}</div>
  if (!job) return <div className="py-12 text-center">Job not found</div>

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Job Header */}
      <div className="bg-white p-8 rounded-lg shadow">
        <h1 className="text-4xl font-bold mb-4">{job.title}</h1>
        <p className="text-2xl text-gray-600 mb-6">{job.company}</p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="flex items-center gap-3">
            <MapPin className="text-blue-600" size={24} />
            <div>
              <p className="text-sm text-gray-600">Location</p>
              <p className="font-semibold">{job.location}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Briefcase className="text-blue-600" size={24} />
            <div>
              <p className="text-sm text-gray-600">Job Type</p>
              <p className="font-semibold">{job.job_type || 'Full-time'}</p>
            </div>
          </div>
          {job.salary_min && (
            <div className="flex items-center gap-3">
              <DollarSign className="text-blue-600" size={24} />
              <div>
                <p className="text-sm text-gray-600">Salary</p>
                <p className="font-semibold">
                  {job.salary_min} - {job.salary_max} {job.currency}
                </p>
              </div>
            </div>
          )}
        </div>

        <button
          onClick={handleApply}
          disabled={isApplying}
          className="px-8 py-3 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
        >
          {isApplying ? 'Applying...' : 'Apply Now'}
        </button>
      </div>

      {/* Description */}
      <div className="bg-white p-8 rounded-lg shadow">
        <h2 className="text-2xl font-bold mb-4">Description</h2>
        <div className="text-gray-700 whitespace-pre-wrap">{job.description}</div>
      </div>

      {/* Requirements */}
      {job.requirements && (
        <div className="bg-white p-8 rounded-lg shadow">
          <h2 className="text-2xl font-bold mb-4">Requirements</h2>
          <ul className="list-disc list-inside space-y-2 text-gray-700">
            {Array.isArray(job.requirements) ? (
              job.requirements.map((req, idx) => <li key={idx}>{req}</li>)
            ) : (
              <li>{job.requirements}</li>
            )}
          </ul>
        </div>
      )}

      {/* Benefits */}
      {job.benefits && (
        <div className="bg-white p-8 rounded-lg shadow">
          <h2 className="text-2xl font-bold mb-4">Benefits</h2>
          <ul className="list-disc list-inside space-y-2 text-gray-700">
            {Array.isArray(job.benefits) ? (
              job.benefits.map((benefit, idx) => <li key={idx}>{benefit}</li>)
            ) : (
              <li>{job.benefits}</li>
            )}
          </ul>
        </div>
      )}
    </div>
  )
}
