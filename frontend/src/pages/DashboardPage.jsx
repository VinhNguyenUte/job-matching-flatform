import { useEffect, useState } from 'react'
import { useAuthStore } from '../lib/store'
import { useNavigate, Link } from 'react-router-dom'
import apiClient from '../lib/api'
import { Briefcase, Sparkles, MapPin, ArrowRight } from 'lucide-react'

export default function DashboardPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  const [recommendedJobs, setRecommendedJobs] = useState([])
  const [isRecommendationLoading, setIsRecommendationLoading] = useState(false)
  const [stats, setStats] = useState({ applications: 0, savedJobs: 0, profileViews: 0 })

  useEffect(() => {
    if (!user) {
      navigate('/login')
    } else {
      fetchDashboardStats()
      fetchAIRecommendations()
    }
  }, [user])

  const fetchDashboardStats = async () => {
    try {
      const response = await apiClient.get('/users/dashboard-stats')
      setStats(response.data)
    } catch (err) {
      console.error('Không thể lấy thống kê tổng quan:', err)
    }
  }

  const fetchAIRecommendations = async () => {
    setIsRecommendationLoading(true)
    try {
      // Gọi service AI matching, lấy danh sách công việc dựa trên cấu trúc vector/graph của CV
      const response = await apiClient.get('/recommend/jobs')
      setRecommendedJobs(response.data)
    } catch (err) {
      console.error('Lỗi khi lấy dữ liệu gợi ý từ AI:', err)
    } finally {
      setIsRecommendationLoading(false)
    }
  }

  if (!user) return null

  return (
    <div className="space-y-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-4xl font-bold">Bảng điều khiển</h1>
          <p className="text-gray-600 mt-1">Chào mừng trở lại, {user.name || user.email}!</p>
        </div>
        <Link to="/profile" className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition">
          Cập nhật CV / Kỹ năng
        </Link>
      </div>

      {/* Thẻ Thống kê */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow border-l-4 border-blue-500">
          <p className="text-gray-600 text-sm font-medium">Đơn ứng tuyển</p>
          <p className="text-4xl font-bold mt-2">{stats.applications}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border-l-4 border-green-500">
          <p className="text-gray-600 text-sm font-medium">Công việc đã lưu</p>
          <p className="text-4xl font-bold mt-2">{stats.savedJobs}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow border-l-4 border-purple-500">
          <p className="text-gray-600 text-sm font-medium">Lượt xem hồ sơ</p>
          <p className="text-4xl font-bold mt-2">{stats.profileViews}</p>
        </div>
      </div>

      {/* Phân vùng tính năng thông minh: Gợi ý việc làm từ AI */}
      <div className="bg-gradient-to-r from-indigo-50 to-blue-50 p-6 rounded-lg shadow border border-indigo-100">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-2">
            <Sparkles className="text-indigo-600 animate-pulse" size={24} />
            <h2 className="text-2xl font-bold text-gray-800">AI Job Match Recommendations</h2>
          </div>
          <button 
            onClick={fetchAIRecommendations}
            className="text-sm font-medium text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
          >
            Tự động cập nhật gợi ý
          </button>
        </div>

        {isRecommendationLoading ? (
          <div className="text-center py-8 text-indigo-600 font-medium">AI đang đối soát dữ liệu CV của bạn...</div>
        ) : recommendedJobs.length === 0 ? (
          <div className="bg-white p-6 rounded-lg text-center text-gray-500 border border-dashed">
            Chưa tìm được gợi ý chính xác. Vui lòng <Link to="/profile" className="text-indigo-600 underline">Upload CV mới nhất</Link> để AI có dữ liệu phân tích.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendedJobs.map((job) => (
              <div key={job.id} className="bg-white p-5 rounded-lg shadow-sm border border-gray-100 flex flex-col justify-between hover:shadow-md transition">
                <div>
                  <div className="flex justify-between items-start">
                    <h3 className="font-bold text-lg text-gray-900 line-clamp-1">{job.title}</h3>
                    {job.match_score && (
                      <span className="bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded-full font-semibold">
                        Match {job.match_score}%
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{job.company}</p>
                  <div className="flex gap-4 text-xs text-gray-500 mb-4">
                    <span className="flex items-center gap-1"><MapPin size={14} />{job.location}</span>
                    <span className="flex items-center gap-1"><Briefcase size={14} />{job.job_type || 'Full-time'}</span>
                  </div>
                </div>
                <Link to={`/jobs/${job.id}`} className="text-sm font-medium text-blue-600 hover:text-blue-800 flex items-center gap-1 self-end mt-2">
                  Xem chi tiết <ArrowRight size={14} />
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Lịch sử ứng tuyển cũ */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-2xl font-bold mb-4">Đơn ứng tuyển gần đây</h2>
        <p className="text-gray-600">Bạn chưa gửi đơn ứng tuyển nào. Hãy bắt đầu tìm kiếm việc làm!</p>
      </div>
    </div>
  )
}