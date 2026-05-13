'use client';
import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { toast } from 'sonner';

interface CV {
  id: number;
  original_filename: string;
  status: string;
  match_score: number | null;
  created_at: string;
}

export default function Dashboard() {
  const [cvs, setCvs] = useState<CV[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMyCVs();
  }, []);

  const fetchMyCVs = async () => {
    try {
      const res = await api.get('/api/v1/cv/my-cvs');
      setCvs(res.data);
    } catch (err) {
      toast.error("Không thể tải danh sách CV");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <h1 className="text-4xl font-bold mb-8">Dashboard</h1>

      <div className="bg-white rounded-2xl shadow p-8">
        <h2 className="text-2xl font-semibold mb-6">CV của bạn</h2>
        
        {loading ? (
          <p>Đang tải...</p>
        ) : cvs.length === 0 ? (
          <p>Bạn chưa có CV nào. Hãy upload CV ngay!</p>
        ) : (
          <div className="space-y-4">
            {cvs.map(cv => (
              <div key={cv.id} className="border rounded-xl p-6 flex justify-between items-center">
                <div>
                  <p className="font-medium">{cv.original_filename}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(cv.created_at).toLocaleDateString('vi-VN')}
                  </p>
                </div>
                <div className="text-right">
                  <span className={`px-4 py-2 rounded-full text-sm font-medium
                    ${cv.status === 'success' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                    {cv.status === 'success' ? `Match Score: ${cv.match_score}%` : cv.status}
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