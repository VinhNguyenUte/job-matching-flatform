import { useEffect, useState } from 'react';
import api from '../lib/api';
import { toast } from 'sonner';
import { Star, Briefcase, MapPin } from 'lucide-react';

export default function Matches() {
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchMatches = async () => {
    setLoading(true);
    try {
      const res = await api.get('/api/v1/jobs/'); 
      setMatches(res.data);
    } catch (err) {
      toast.error("Không thể tải danh sách phân tích việc làm.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMatches();
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold text-gray-800">Cơ hội việc làm lý tưởng</h1>
        <button onClick={fetchMatches} className="text-purple-600 hover:text-purple-800 font-medium transition flex items-center gap-1">
          ↻ Làm mới dữ liệu
        </button>
      </div>

      {loading ? (
        <p className="text-gray-500">Hệ thống AI đang tính toán độ tương thích...</p>
      ) : matches.length === 0 ? (
        <div className="text-center py-20 bg-white border rounded-2xl shadow-sm">
          <Briefcase size={64} className="mx-auto text-gray-300" />
          <p className="text-xl font-medium mt-4 text-gray-600">Chưa tìm thấy kết quả phù hợp</p>
          <p className="text-gray-400 text-sm mt-1">Hãy tải lên một bản CV chi tiết hơn để kích hoạt bộ lọc AI.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {matches.map((item) => (
            <div key={item.id} className="bg-white border rounded-2xl p-6 hover:shadow-md transition">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-xl font-bold text-gray-900">{item.title}</h3>
                  <p className="text-lg text-purple-600 font-semibold mt-1">{item.company}</p>
                </div>
                <div className="flex items-center gap-1 bg-green-100 text-green-700 px-4 py-1.5 rounded-full font-bold">
                  92% <Star className="w-4 h-4 fill-current" />
                </div>
              </div>

              <div className="flex gap-6 mt-4 text-sm text-gray-500">
                <div className="flex items-center gap-1"><MapPin size={16} /> {item.location || 'Toàn quốc'}</div>
                <div className="flex items-center gap-1">💰 {item.salary || 'Thỏa thuận'}</div>
              </div>

              <div className="mt-4 p-4 bg-gray-50 rounded-xl border border-gray-100 text-sm text-gray-600">
                {item.description || 'CV của bạn sở hữu các nhóm kỹ năng Python/AI tương thích cao với yêu cầu tuyển dụng.'}
              </div>

              <button className="mt-4 bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-6 rounded-lg transition text-sm">
                Ứng tuyển ngay
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}