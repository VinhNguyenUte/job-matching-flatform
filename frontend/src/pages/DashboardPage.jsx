import { useEffect, useState } from 'react'
import { useAuthStore } from '../lib/store'
import { useNavigate, Link } from 'react-router-dom' 
import apiClient from '../lib/api'
import { Briefcase, Sparkles, MapPin, ArrowRight, RefreshCw } from 'lucide-react'

export default function DashboardPage() {
  const { user } = useAuthStore()
  const navigate = useNavigate()
  
  // Lấy cv_id trực tiếp từ localStorage (giả định key lưu trữ là 'cv_id')
  const cvIdFromStorage = localStorage.getItem('cvId')

  const [recommendedJobs, setRecommendedJobs] = useState([])
  const [isRecommendationLoading, setIsRecommendationLoading] = useState(false)

  useEffect(() => {
    if (!user) {
      navigate('/login')
    } else {
      fetchAIRecommendations()
    }
  }, [user, cvIdFromStorage]) // Bám theo sự thay đổi của cvId từ storage nếu có re-render

  const fetchAIRecommendations = async () => {
    setIsRecommendationLoading(true)
    try {
      let response;
      // Kiểm tra nếu có cv_id trong localStorage thì gọi endpoint match-cv
      if (cvIdFromStorage) {
        response = await apiClient.get(`/recommend/match-cv/${cvIdFromStorage}`)
      } else {
        response = await apiClient.get('/recommend/jobs')
      }
      
      if (response && response.data && response.data.length > 0) {
        const rawJobs = response.data;

        // Bù đắp dữ liệu (Hydration) từ API detail của từng Job
        const hydratedJobsPromises = rawJobs.map(async (rawJob) => {
          try {
            const detailResponse = await apiClient.get(`/jobs/${rawJob.id}`)
            if (detailResponse && detailResponse.data) {
              return {
                ...detailResponse.data,
                match_score: rawJob.match_score 
              }
            }
            return rawJob;
          } catch (err) {
            console.error(`Không thể bù đắp dữ liệu cho Job ID: ${rawJob.id}`, err)
            return rawJob;
          }
        })

        const fullRecommendedJobs = await Promise.all(hydratedJobsPromises)
        setRecommendedJobs(fullRecommendedJobs)
      } else {
        setRecommendedJobs([])
      }
    } catch (err) {
      console.error('Lỗi khi lấy dữ liệu gợi ý từ AI:', err)
      setRecommendedJobs([])
    } finally {
      setIsRecommendationLoading(false)
    }
  }

  if (!user) return null

  return (
    <div className="space-y-8 px-4 py-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-4xl font-bold text-gray-900">Gợi ý công việc</h1>
          <p className="text-gray-600 mt-1">Chào mừng trở lại, {user.name || user.email}!</p>
        </div>
        <Link to="/profile" className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition shadow-sm">
          Cập nhật CV / Kỹ năng AI
        </Link>
      </div>

      <div className="bg-gradient-to-r from-indigo-50 to-blue-50 p-6 rounded-xl shadow-sm border border-indigo-100">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-2">
          <div className="flex items-center gap-2">
            <Sparkles className="text-indigo-600 animate-pulse fill-indigo-200" size={24} />
            <div>
              <h2 className="text-2xl font-bold text-gray-800">AI Job Match Recommendations</h2>
              {cvIdFromStorage && (
                <p className="text-xs text-indigo-700 font-medium">📍 Đang hiển thị kết quả phân tích theo CV trong hệ thống của bạn</p>
              )}
            </div>
          </div>
          <button 
            onClick={fetchAIRecommendations}
            disabled={isRecommendationLoading}
            className="text-sm font-semibold text-indigo-600 hover:text-indigo-800 flex items-center gap-1.5 transition disabled:opacity-50"
          >
            <RefreshCw size={14} className={isRecommendationLoading ? 'animate-spin' : ''} />
            Tự động cập nhật gợi ý
          </button>
        </div>

        {isRecommendationLoading ? (
          <div className="text-center py-12 text-indigo-600 font-medium flex items-center justify-center gap-2">
            <RefreshCw className="animate-spin" size={18} />
            AI đang đồng bộ dữ liệu thực tế và đối soát dữ liệu CV...
          </div>
        ) : recommendedJobs.length === 0 ? (
          <div className="bg-white p-8 rounded-lg text-center text-gray-500 border border-dashed border-gray-200">
            Chưa tìm được gợi ý chính xác phù hợp với trọng số kỹ năng của bạn. Vui lòng <Link to="/profile" className="text-indigo-600 font-semibold underline hover:text-indigo-800">Upload CV mới nhất</Link> để AI có dữ liệu phân tích.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendedJobs.map((job) => {
              const displayScore = job.match_score 
                ? (job.match_score <= 1 ? Math.round(job.match_score * 100) : Math.round(job.match_score))
                : null;

              return (
                <div key={job.id} className="bg-white p-5 rounded-lg shadow-sm border border-gray-100 flex flex-col justify-between hover:shadow-md transition">
                  <div>
                    <div className="flex justify-between items-start gap-2 mb-2">
                      <h3 className="font-bold text-lg text-gray-900 line-clamp-1 hover:text-blue-600 transition">
                        <Link to={`/jobs/${job.id}`}>{job.title}</Link>
                      </h3>
                      {displayScore !== null && (
                        <span className="whitespace-nowrap bg-green-50 text-green-700 border border-green-200 text-xs px-2.5 py-0.5 rounded-full font-bold flex items-center gap-1 shadow-sm">
                          <Sparkles size={12} className="fill-green-200" />
                          Match {displayScore}%
                        </span>
                      )}
                    </div>
                    
                    <p className="text-sm font-medium text-gray-600 mb-3">
                      {job.company?.name || 'Doanh nghiệp chưa cập nhật tên'}
                    </p>
                    
                    <div className="flex gap-4 text-xs text-gray-500 mb-4">
                      <span className="flex items-center gap-1">
                        <MapPin size={14} className="text-gray-400" />
                        {job.locations && job.locations.length > 0 && job.locations[0].city 
                          ? job.locations[0].city 
                          : (job.work_mode || 'Toàn quốc')}
                      </span>
                      <span className="flex items-center gap-1">
                        <Briefcase size={14} className="text-gray-400" />
                        {job.job_type || 'Toàn thời gian'}
                      </span>
                    </div>
                  </div>
                  
                  <Link to={`/jobs/${job.id}`} className="text-sm font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1 self-end mt-2 group transition">
                    Xem chi tiết <ArrowRight size={14} className="group-hover:translate-x-1 transition" />
                  </Link>
                </div>
              )
            })}
          </div>
        )}
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
        <h2 className="text-2xl font-bold mb-4 text-gray-900">Đơn ứng tuyển gần đây</h2>
        <p className="text-gray-500 text-sm">Bạn chưa gửi đơn ứng tuyển nào thông qua hệ thống AI. Hãy bắt đầu tìm kiếm việc làm!</p>
      </div>
    </div>
  )
}