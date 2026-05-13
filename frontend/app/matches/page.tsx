'use client';
import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { toast } from 'sonner';
import { Star, Briefcase, MapPin, Clock } from 'lucide-react';

interface Match {
  id: number;
  job: {
    id: number;
    title: string;
    company: string;
    location: string | null;
    salary: string | null;
  };
  score: number;
  explanation: string;
  created_at: string;
}

export default function MatchesPage() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMatches();
  }, []);

  const fetchMatches = async () => {
    try {
      const res = await api.get('/api/v1/matches/my-matches'); // Sẽ tạo API này
      setMatches(res.data);
    } catch (err) {
      toast.error("Không thể tải danh sách match");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold">Job Matches</h1>
        <button onClick={fetchMatches} className="text-purple-600 hover:underline">
          ↻ Làm mới
        </button>
      </div>

      {loading ? (
        <p>Đang tải...</p>
      ) : matches.length === 0 ? (
        <div className="text-center py-20">
          <Briefcase size={80} className="mx-auto text-gray-300" />
          <p className="text-xl mt-6">Chưa có match nào</p>
          <p className="text-gray-500">Hãy upload CV để hệ thống gợi ý việc làm</p>
        </div>
      ) : (
        <div className="space-y-6">
          {matches.map((match) => (
            <div key={match.id} className="bg-white border border-gray-200 rounded-2xl p-8 hover:shadow-lg transition">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-2xl font-semibold">{match.job.title}</h3>
                  <p className="text-xl text-purple-600 font-medium">{match.job.company}</p>
                </div>
                
                <div className="flex items-center gap-2 bg-green-100 text-green-700 px-5 py-2 rounded-full font-bold text-lg">
                  {match.score.toFixed(0)}%
                  <Star className="fill-current" />
                </div>
              </div>

              <div className="flex gap-6 mt-4 text-gray-600">
                {match.job.location && (
                  <div className="flex items-center gap-2">
                    <MapPin size={18} /> {match.job.location}
                  </div>
                )}
                {match.job.salary && (
                  <div className="flex items-center gap-2">
                    💰 {match.job.salary}
                  </div>
                )}
              </div>

              <div className="mt-6 p-5 bg-gray-50 rounded-xl border">
                <p className="text-gray-700 leading-relaxed">{match.explanation}</p>
              </div>

              <button className="mt-6 w-full bg-purple-600 hover:bg-purple-700 text-white py-4 rounded-xl font-semibold">
                Ứng tuyển ngay
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}