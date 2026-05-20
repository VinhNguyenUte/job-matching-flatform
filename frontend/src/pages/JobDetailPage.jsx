import { useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'
import apiClient from '../lib/api'
import { useAuthStore } from '../lib/store'
import { MapPin, DollarSign, Briefcase, Building, Award } from 'lucide-react'

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

  // const handleApply = async () => {
  //   window.open(applyUrl, '_blank', 'noopener,noreferrer')
  // }

  if (isLoading) return <div className="py-12 text-center text-gray-500">Loading job details...</div>
  if (error) return <div className="py-12 text-center text-red-600 font-medium">{error}</div>
  if (!job) return <div className="py-12 text-center text-gray-500">Job not found</div>

  return (
    <div className="max-w-4xl mx-auto space-y-8 px-4 py-6">
      <div className="bg-white p-8 rounded-lg shadow border border-gray-100">
        <div className="flex flex-wrap gap-2 mb-3">
          {job.job_level && (
            <span className="bg-blue-50 text-blue-700 text-xs font-semibold px-2.5 py-1 rounded flex items-center gap-1">
              <Award size={12} /> {job.job_level}
            </span>
          )}
          {job.job_type && (
            <span className="bg-gray-100 text-gray-700 text-xs font-semibold px-2.5 py-1 rounded">
              {job.job_type}
            </span>
          )}
        </div>

        <h1 className="text-4xl font-bold mb-3 text-gray-900">{job.title}</h1>
        
        <p className="text-2xl text-blue-600 font-medium mb-6 flex items-center gap-2">
          <Building size={24} className="text-gray-400" />
          {job.company?.name || 'Unknown Company'}
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 border-t border-b border-gray-100 py-6">
          {/* Địa điểm làm việc */}
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-50 rounded-lg">
              <MapPin className="text-blue-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Location</p>
              <p className="font-semibold text-gray-800">
                {job.locations && job.locations.length > 0 
                  ? `${job.locations[0].city}${job.locations[0].address ? `, ${job.locations[0].address}` : ''}`
                  : (job.work_mode || 'Remote')}
              </p>
            </div>
          </div>
          
          {/* Hình thức làm việc */}
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-50 rounded-lg">
              <Briefcase className="text-blue-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Job Type</p>
              <p className="font-semibold text-gray-800">{job.job_type || 'Full-time'}</p>
            </div>
          </div>

          {/* Mức lương (Xử lý khi min/max lương bị null) */}
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-50 rounded-lg">
              <DollarSign className="text-green-600" size={24} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Salary</p>
              <p className="font-semibold text-green-600">
                {job.salary_min 
                  ? `${job.salary_min.toLocaleString()} - ${job.salary_max?.toLocaleString()} ${job.currency || 'VND'}`
                  : 'Thỏa thuận'}
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={() => job.source_url && window.open(job.source_url, '_blank', 'noopener,noreferrer')}
          disabled={isApplying}
          className="px-8 py-3 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition shadow-md hover:shadow-lg"
        >
          {isApplying ? 'Applying...' : 'Apply Now'}
        </button>
      </div>

      {/* Chi tiết công việc (Đọc từ description_raw) */}
      <div className="bg-white p-8 rounded-lg shadow border border-gray-100">
        <h2 className="text-2xl font-bold mb-4 text-gray-900 border-b border-gray-100 pb-2">Description</h2>
        <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">
          {job.description_raw || 'No description provided.'}
        </div>
      </div>

      {/* Hiển thị các yêu cầu nếu có mảng dữ liệu đặc thù */}
      {job.requirements && (
        <div className="bg-white p-8 rounded-lg shadow border border-gray-100">
          <h2 className="text-2xl font-bold mb-4 text-gray-900 border-b border-gray-100 pb-2">Requirements</h2>
          <ul className="list-disc list-inside space-y-2 text-gray-700 leading-relaxed">
            {Array.isArray(job.requirements) ? (
              job.requirements.map((req, idx) => <li key={idx}>{req}</li>)
            ) : (
              <li>{job.requirements}</li>
            )}
          </ul>
        </div>
      )}
    </div>
  )
}