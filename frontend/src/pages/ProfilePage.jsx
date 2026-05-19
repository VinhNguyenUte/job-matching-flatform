// src/pages/ProfilePage.jsx
import { useState, useEffect } from 'react'
import { useAuthStore } from '../lib/store'
import apiClient from '../lib/api'
import { Upload, FileText, CheckCircle, RefreshCw } from 'lucide-react'

export default function ProfilePage() {
  const { user } = useAuthStore()
  const [file, setFile] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [cvInfo, setCvInfo] = useState(null)
  const [isLoadingCv, setIsLoadingCv] = useState(false)
  const [message, setMessage] = useState({ type: '', content: '' })

  useEffect(() => {
    if (user) {
      fetchCurrentCV()
    }
  }, [user])

  const fetchCurrentCV = async () => {
    setIsLoadingCv(true)
    try {
      const response = await apiClient.get('/cv/current')
      setCvInfo(response.data)
    } catch (err) {
      console.error('Chưa có CV được upload hoặc lỗi tải CV:', err)
    } finally {
      setIsLoadingCv(false)
    }
  }

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
    setMessage({ type: '', content: '' })
  }

  const handleUploadCV = async (e) => {
    e.preventDefault()
    if (!file) {
      setMessage({ type: 'error', content: 'Vui lòng chọn một file CV (PDF/DOCX).' })
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    setIsUploading(true)
    try {
      // Endpoint upload CV lên backend, tích hợp lưu trữ MinIO & gửi queue xử lý AI
      const response = await apiClient.post('/cv/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      setMessage({ type: 'success', content: 'Upload CV thành công! Hệ thống AI đang phân tích...' })
      setFile(null)
      // Tải lại thông tin chi tiết CV sau khi cập nhật
      fetchCurrentCV()
    } catch (err) {
      setMessage({ 
        type: 'error', 
        content: err.response?.data?.detail || 'Có lỗi xảy ra khi upload CV.' 
      })
    } finally {
      setIsUploading(false)
    }
  }

  if (!user) {
    return (
      <div className="text-center py-12 text-gray-600">
        Vui lòng đăng nhập để quản lý hồ sơ cá nhân.
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <h1 className="text-4xl font-bold">Hồ sơ cá nhân</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Cột trái: Upload CV */}
        <div className="bg-white p-6 rounded-lg shadow space-y-4 h-fit">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Upload size={20} className="text-blue-600" />
            Tải lên CV của bạn
          </h2>
          <p className="text-sm text-gray-500">
            Hệ thống AI của chúng tôi sẽ phân tích kỹ năng trong CV để tự động gợi ý công việc phù hợp nhất.
          </p>

          <form onSubmit={handleUploadCV} className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-blue-500 transition relative">
              <input 
                type="file" 
                accept=".pdf,.docx,.doc" 
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <FileText className="mx-auto text-gray-400 mb-2" size={32} />
              <p className="text-xs text-gray-600 font-medium">
                {file ? file.name : 'Kéo thả hoặc nhấp để chọn file'}
              </p>
              <p className="text-[10px] text-gray-400 mt-1">Hỗ trợ định dạng PDF, DOCX tối đa 5MB</p>
            </div>

            {message.content && (
              <div className={`p-3 rounded text-sm ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                {message.content}
              </div>
            )}

            <button
              type="submit"
              disabled={isUploading || !file}
              className="w-full py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 disabled:bg-gray-300 flex items-center justify-center gap-2"
            >
              {isUploading ? (
                <>
                  <RefreshCw className="animate-spin" size={16} />
                  Đang xử lý...
                </>
              ) : 'Xác nhận tải lên'}
            </button>
          </form>
        </div>

        {/* Cột phải: Thông tin CV trích xuất từ AI */}
        <div className="bg-white p-6 rounded-lg shadow md:col-span-2 space-y-6">
          <div className="flex justify-between items-center border-b pb-4">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <CheckCircle size={20} className="text-green-600" />
              Thông tin phân tích từ AI
            </h2>
            <button 
              onClick={fetchCurrentCV} 
              className="text-gray-500 hover:text-blue-600 flex items-center gap-1 text-sm"
            >
              <RefreshCw size={14} className={isLoadingCv ? 'animate-spin' : ''} />
              Làm mới
            </button>
          </div>

          {isLoadingCv ? (
            <div className="text-center py-12 text-gray-500">Đang tải thông tin phân tích...</div>
          ) : cvInfo ? (
            <div className="space-y-4">
              <div>
                <p className="text-sm font-semibold text-gray-500">File CV hiện tại:</p>
                <a href={cvInfo.file_url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline flex items-center gap-2 mt-1">
                  <FileText size={16} /> {cvInfo.file_name || "Xem chi tiết file"}
                </a>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-500">Kỹ năng trích xuất (Skills):</p>
                <div className="flex flex-wrap gap-2 mt-2">
                  {cvInfo.skills?.map((skill, idx) => (
                    <span key={idx} className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-xs font-medium">
                      {skill}
                    </span>
                  )) || <span className="text-gray-400 text-sm">Chưa cập nhật kỹ năng</span>}
                </div>
              </div>

              <div>
                <p className="text-sm font-semibold text-gray-500">Kinh nghiệm & Trình độ:</p>
                <p className="text-gray-700 text-sm mt-1">{cvInfo.experience_summary || 'Đang chờ xử lý AI...'}</p>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-400 border border-dashed rounded-lg">
              Bạn chưa đăng tải dữ liệu CV lên hệ thống. Vui lòng upload để AI nhận diện và tối ưu hóa kết quả tìm kiếm công việc.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}