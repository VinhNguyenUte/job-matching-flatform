import { useEffect, useState } from 'react';
import api from '../lib/api';
import { toast } from 'sonner';
import { Search, Briefcase, MapPin, Calendar, FileText } from 'lucide-react';

export default function Dashboard() {
  const [cvs, setCvs] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loadingCV, setLoadingCV] = useState(true);
  const [loadingJobs, setLoadingJobs] = useState(true);

  useEffect(() => {
    fetchMyCVs();
    fetchJobs();
  }, []);

  const fetchMyCVs = async () => {
    try {
      const res = await api.get('/api/v1/cv/my-cvs');
      setCvs(res.data);
    } catch (err) {
      toast.error("Không thể tải danh sách dữ liệu CV");
    } finally {
      setLoadingCV(false);
    }
  };

  const fetchJobs = async () => {
    try {
      const res = await api.get('/api/v1/jobs/');
      setJobs(res.data);
    } catch (err) {
      toast.error("Không thể tải danh sách công việc");
    } finally {
      setLoadingJobs(false);
    }
  };

  const filteredJobs = jobs.filter(job => 
    job.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    job.company?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 space-y-10">
      
      <div className="bg-white rounded-2xl border shadow-sm p-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800">Khám phá công việc</h1>
          <p className="text-gray-500 mt-1">Tìm kiếm cơ hội nghề nghiệp phù hợp với năng lực của bạn</p>
        </div>

        <div className="relative max-w-xl mb-8">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Nhập vị trí công việc, kỹ năng hoặc tên công ty..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white transition text-sm"
          />
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <Briefcase size={18} className="text-purple-600" />
            Vị trí tuyển dụng có sẵn ({filteredJobs.length})
          </h3>

          {loadingJobs ? (
            <div className="text-gray-500 text-sm animate-pulse">Đang quét danh sách việc làm...</div>
          ) : filteredJobs.length === 0 ? (
            <div className="text-center py-10 border border-dashed rounded-xl bg-gray-50/50">
              <p className="text-gray-400 text-sm">Không tìm thấy công việc nào khớp với từ khóa của bạn.</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-4">
              {filteredJobs.map((job) => (
                <div key={job.id} className="border border-gray-100 rounded-xl p-5 bg-gray-50/50 hover:bg-white hover:shadow-md hover:border-purple-100 transition flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start gap-2">
                      <h4 className="font-bold text-gray-900 text-base line-clamp-1">{job.title}</h4>
                      <span className="text-xs font-semibold px-2.5 py-1 bg-purple-50 text-purple-700 rounded-md shrink-0">
                        {job.salary || 'Thỏa thuận'}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-purple-600 mt-0.5">{job.company}</p>
                    <p className="text-xs text-gray-500 mt-2 flex items-center gap-1">
                      <MapPin size={13} /> {job.location || 'Toàn quốc'}
                    </p>
                  </div>
                  <div className="mt-4 pt-3 border-t border-gray-100 flex justify-end">
                    <button className="text-xs bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-lg transition">
                      Xem chi tiết
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-2xl border shadow-sm p-8">
        <h2 className="text-2xl font-bold mb-6 text-gray-800 flex items-center gap-2">
          <FileText size={22} className="text-purple-600" />
          CV của bạn
        </h2>
        
        {loadingCV ? (
          <div className="text-gray-500 py-4 text-sm">Đang tải tiến trình hồ sơ...</div>
        ) : cvs.length === 0 ? (
          <p className="text-gray-500 text-sm">Bạn chưa sở hữu hồ sơ CV nào trên hệ thống. Vui lòng thực hiện tải lên.</p>
        ) : (
          <div className="space-y-4">
            {cvs.map(cv => (
              <div key={cv.id} className="border border-gray-100 rounded-xl p-5 flex flex-col sm:flex-row justify-between sm:items-center bg-gray-50/50 gap-4">
                <div>
                  <p className="font-semibold text-gray-800 text-base">{cv.original_filename}</p>
                  <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
                    <Calendar size={13} /> Ngày tải lên: {new Date(cv.created_at).toLocaleDateString('vi-VN')}
                  </p>
                </div>
                <div className="flex items-center">
                  <span className={`px-4 py-1.5 rounded-full text-xs font-bold shadow-sm border
                    ${cv.status === 'success' 
                      ? 'bg-green-50 text-green-700 border-green-200' 
                      : 'bg-yellow-50 text-yellow-700 border-yellow-200'}`}>
                    {cv.status === 'success' ? `Match Score: ${cv.match_score}%` : `Trạng thái: ${cv.status}`}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}