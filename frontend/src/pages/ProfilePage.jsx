import { useState, useEffect } from 'react'
import { useAuthStore, useCVStore } from '../lib/store'
import apiClient from '../lib/api'
import { Upload, FileText, CheckCircle, RefreshCw, User, Briefcase, GraduationCap } from 'lucide-react'

export default function ProfilePage() {
  const { user } = useAuthStore()
  
  // Đưa các state liên quan đến CV lên quản lý tập trung tại useCVStore
  const { cvInfo, cvId, setCvInfo, setCvId } = useCVStore()
  
  const [file, setFile] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isLoadingCv, setIsLoadingCv] = useState(false)
  const [message, setMessage] = useState({ type: '', content: '' })

  // Chạy lần đầu khi user đăng nhập thành công
  useEffect(() => {
    if (user && cvId) {
      fetchDetailCV(cvId)
    }
  }, [user, cvId])

  const fetchDetailCV = async (targetId) => {
    if (!targetId) return
    setIsLoadingCv(true)
    try {
      const response = await apiClient.get(`/cv/${targetId}`)
      setCvInfo(response.data) // Lưu thông tin phân tích vào Store
    } catch (err) {
      console.error('Lỗi khi lấy thông tin chi tiết CV:', err)
      setMessage({ type: 'error', content: 'Không thể tải thông tin chi tiết của CV.' })
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
      const response = await apiClient.post('/cv/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      
      setMessage({ type: 'success', content: 'Upload CV thành công! Hệ thống AI đang phân tích...' })
      setFile(null)

      const uploadedCvId = response.data?.id || response.data?.cv_id
      
      if (uploadedCvId) {
        setCvId(uploadedCvId)
        localStorage.setItem('cvId', uploadedCvId) 
        console.log('Uploaded CV ID:', uploadedCvId)
        fetchDetailCV(uploadedCvId)
      } 

    } catch (err) {
      setMessage({ 
        type: 'error', 
        content: err.response?.data?.detail || 'Có lỗi xảy ra khi upload CV.' 
      })
    } finally {
      setIsUploading(false)
    }
  }

  const handleRefresh = () => {
    const targetId = cvId || cvInfo?.id
    if (targetId) {
      fetchDetailCV(targetId)
    } else {
      setMessage({ type: 'error', content: 'Không tìm thấy ID hồ sơ để làm mới.' })
    }
  }

  if (!user) {
    return (
      <div className="text-center py-12 text-gray-600">
        Vui lòng đăng nhập để quản lý hồ sơ cá nhân.
      </div>
    )
  }

  const parsedData = cvInfo?.parsed_data

  return (
    <div className="max-w-5xl mx-auto space-y-8 p-4">
      <h1 className="text-4xl font-bold text-gray-900">Hồ sơ cá nhân</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="bg-white p-6 rounded-lg shadow space-y-4 h-fit">
          <h2 className="text-xl font-bold flex items-center gap-2 text-gray-800">
            <Upload size={20} className="text-blue-600" />
            Tải lên CV của bạn
          </h2>
          <p className="text-sm text-gray-500">
            Hệ thống AI của chúng tôi sẽ phân tích kỹ năng trong CV để tự động gợi ý công việc phù hợp nhất.
          </p>

          <form onSubmit={handleUploadCV} className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-blue-500 transition relative bg-gray-50/50">
              <input 
                type="file" 
                accept=".pdf,.docx,.doc" 
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <FileText className="mx-auto text-gray-400 mb-2" size={32} />
              <p className="text-xs text-gray-600 font-medium line-clamp-2">
                {file ? file.name : 'Kéo thả hoặc nhấp để chọn file'}
              </p>
              <p className="text-[10px] text-gray-400 mt-1">Hỗ trợ định dạng PDF, DOCX tối đa 5MB</p>
            </div>

            {message.content && (
              <div className={`p-3 rounded text-sm font-medium ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
                {message.content}
              </div>
            )}

            <button
              type="submit"
              disabled={isUploading || !file}
              className="w-full py-2 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400 flex items-center justify-center gap-2 transition"
            >
              {isUploading ? (
                <>
                  <RefreshCw className="animate-spin" size={16} />
                  Đang xử lý dữ liệu AI...
                </>
              ) : 'Xác nhận tải lên'}
            </button>
          </form>
        </div>

        <div className="bg-white p-6 rounded-lg shadow md:col-span-2 space-y-6">
          <div className="flex justify-between items-center border-b border-gray-100 pb-4">
            <h2 className="text-xl font-bold flex items-center gap-2 text-gray-800">
              <CheckCircle size={20} className="text-green-600" />
              Thông tin phân tích từ AI
            </h2>
            <button 
              onClick={handleRefresh} 
              className="text-gray-500 hover:text-blue-600 flex items-center gap-1 text-sm font-medium transition"
            >
              <RefreshCw size={14} className={isLoadingCv ? 'animate-spin' : ''} />
              Làm mới dữ liệu
            </button>
          </div>

          {isLoadingCv ? (
            <div className="text-center py-12 text-gray-400">Đang đồng bộ cấu trúc dữ liệu...</div>
          ) : cvInfo && parsedData ? (
            <div className="space-y-6">
              <div className="bg-gray-50 p-4 rounded-lg space-y-3">
                <div className="flex flex-col sm:flex-row sm:justify-between gap-2 border-b border-gray-200 pb-2">
                  <span className="font-bold text-gray-800 text-base flex items-center gap-1.5">
                    <User size={16} className="text-gray-500" />
                    {parsedData.full_name || cvInfo.title}
                  </span>
                  <span className="text-xs text-gray-500 flex items-center bg-white px-2.5 py-1 rounded border border-gray-200 w-fit">
                    Trạng thái AI: <b className="text-green-600 ml-1 uppercase">{parsedData.status || 'completed'}</b>
                  </span>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm text-gray-600">
                  <p><b>Email:</b> {parsedData.email || 'Chưa cập nhật'}</p>
                  <p><b>Số điện thoại:</b> {parsedData.phone || 'Chưa cập nhật'}</p>
                  {parsedData.cv_urls?.[0] && (
                    <div className="sm:col-span-2 pt-1">
                      <a href={parsedData.cv_urls[0]} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline inline-flex items-center gap-1 font-medium">
                        <FileText size={16} /> Xem bản gốc File PDF/DOCX ứng tuyển
                      </a>
                    </div>
                  )}
                </div>
              </div>

              {parsedData.summary && (
                <div className="space-y-1.5">
                  <p className="text-sm font-bold text-gray-800 uppercase tracking-wide">Mục tiêu nghề nghiệp</p>
                  <div className="text-gray-600 text-sm bg-blue-50/30 p-3 rounded border border-blue-100/50 leading-relaxed italic">
                    "{parsedData.summary}"
                  </div>
                </div>
              )}

              <div>
                <p className="text-sm font-bold text-gray-800 uppercase tracking-wide">Kỹ năng nhận diện (Skills Matrix)</p>
                <div className="flex flex-wrap gap-2 mt-2">
                  {parsedData.skills && parsedData.skills.length > 0 ? (
                    parsedData.skills.map((skill, idx) => (
                      <span key={idx} className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-xs font-semibold border border-blue-100">
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-gray-400 text-sm italic">Chưa phát hiện từ khóa kỹ năng</span>
                  )}
                </div>
              </div>

              {parsedData.education && parsedData.education.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm font-bold text-gray-800 uppercase tracking-wide flex items-center gap-1">
                    <GraduationCap size={18} className="text-gray-600" /> Học vấn
                  </p>
                  {parsedData.education.map((edu, idx) => (
                    <div key={idx} className="text-sm border-l-2 border-blue-500 pl-3 py-0.5">
                      <p className="font-semibold text-gray-800">{edu.school}</p>
                      <p className="text-gray-600 text-xs mt-0.5">{edu.major} • <span className="text-gray-400">{edu.duration}</span></p>
                    </div>
                  ))}
                </div>
              )}

              <div className="space-y-3">
                <p className="text-sm font-bold text-gray-800 uppercase tracking-wide flex items-center gap-1">
                  <Briefcase size={18} className="text-gray-600" /> Kinh nghiệm làm việc & Dự án
                </p>
                <div className="space-y-4">
                  {parsedData.experience && parsedData.experience.length > 0 ? (
                    parsedData.experience.map((exp, idx) => (
                      <div key={idx} className="border-b border-gray-100 pb-3 last:border-0 last:pb-0">
                        <div className="flex justify-between items-start text-sm">
                          <div>
                            <h4 className="font-semibold text-gray-900">{exp.role}</h4>
                            <p className="text-blue-600 font-medium text-xs mt-0.5">{exp.company}</p>
                          </div>
                          {exp.duration && exp.duration !== 'null' && (
                            <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded font-medium">
                              {exp.duration}
                            </span>
                          )}
                        </div>
                        <p className="text-gray-600 text-xs mt-1.5 leading-relaxed whitespace-pre-wrap bg-gray-50/50 p-2.5 rounded border border-gray-100">
                          {exp.description}
                        </p>
                      </div>
                    ))
                  ) : (
                    <span className="text-gray-400 text-sm italic">Chưa có dữ liệu kinh nghiệm</span>
                  )}
                </div>
              </div>

            </div>
          ) : (
            <div className="text-center py-12 text-gray-400 border border-dashed rounded-lg p-6 bg-gray-50/50">
              Bạn chưa đăng tải dữ liệu CV lên hệ thống. Vui lòng upload để AI nhận diện và tối ưu hóa kết quả tìm kiếm công việc.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}