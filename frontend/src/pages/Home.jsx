import { Link } from 'react-router-dom';
import { Upload, Search, Award } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-[calc(100vh-73px)] bg-gradient-to-br from-purple-50 to-white flex flex-col justify-center">
      <div className="max-w-6xl mx-auto px-6 text-center py-12">
        <h1 className="text-6xl font-bold text-gray-900 mb-6 leading-tight">
          Tìm việc làm <span className="text-purple-600">thông minh</span> hơn
        </h1>
        <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
          Upload CV một lần • AI phân tích • Ghép đôi tự động với việc làm phù hợp nhất
        </p>

        <div className="flex gap-4 justify-center mb-16">
          <Link to="/register" className="bg-purple-600 hover:bg-purple-700 text-white px-8 py-4 rounded-2xl text-lg font-semibold transition">
            Bắt đầu ngay
          </Link>
          <Link to="/login" className="border border-gray-300 hover:bg-gray-50 px-8 py-4 rounded-2xl text-lg font-semibold transition">
            Đăng nhập
          </Link>
        </div>

        <div className="grid md:grid-cols-3 gap-10 text-left max-w-5xl mx-auto">
          <div className="bg-white p-6 rounded-2xl border shadow-sm text-center">
            <div className="mx-auto w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-4">
              <Upload className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Upload CV nhanh</h3>
            <p className="text-gray-500 text-sm">Hỗ trợ PDF, DOCX. AI tự động trích xuất dữ liệu có cấu trúc.</p>
          </div>
          <div className="bg-white p-6 rounded-2xl border shadow-sm text-center">
            <div className="mx-auto w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-4">
              <Search className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Match thông minh</h3>
            <p className="text-gray-500 text-sm">Sử dụng thuật toán Cosine Similarity kết hợp Gemini AI tiên tiến.</p>
          </div>
          <div className="bg-white p-6 rounded-2xl border shadow-sm text-center">
            <div className="mx-auto w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-4">
              <Award className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Giải thích rõ ràng</h3>
            <p className="text-gray-500 text-sm">Giúp bạn nắm bắt lý do chi tiết tại sao bạn phù hợp với vị trí đó.</p>
          </div>
        </div>
      </div>
    </div>
  );
}