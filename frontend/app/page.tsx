'use client';
import Link from 'next/link';
import { Upload, Search, Award } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-white">
      {/* Hero Section */}
      <div className="max-w-6xl mx-auto px-6 pt-24 pb-16 text-center">
        <h1 className="text-6xl font-bold text-gray-900 mb-6">
          Tìm việc làm <span className="text-purple-600">thông minh</span> hơn
        </h1>
        <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
          Upload CV một lần • AI phân tích • Ghép đôi tự động với việc làm phù hợp nhất
        </p>

        <div className="flex gap-4 justify-center">
          <Link
            href="/register"
            className="bg-purple-600 hover:bg-purple-700 text-white px-8 py-4 rounded-2xl text-lg font-semibold transition"
          >
            Bắt đầu ngay
          </Link>
          <Link
            href="/login"
            className="border border-gray-300 hover:bg-gray-50 px-8 py-4 rounded-2xl text-lg font-semibold transition"
          >
            Đăng nhập
          </Link>
        </div>
      </div>

      {/* Features */}
      <div className="max-w-6xl mx-auto px-6 py-20 grid md:grid-cols-3 gap-10">
        <div className="text-center">
          <div className="mx-auto w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mb-6">
            <Upload className="w-8 h-8 text-purple-600" />
          </div>
          <h3 className="text-xl font-semibold mb-3">Upload CV nhanh</h3>
          <p className="text-gray-600">Hỗ trợ PDF, DOCX. AI tự động trích xuất thông tin</p>
        </div>

        <div className="text-center">
          <div className="mx-auto w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mb-6">
            <Search className="w-8 h-8 text-purple-600" />
          </div>
          <h3 className="text-xl font-semibold mb-3">Match thông minh</h3>
          <p className="text-gray-600">Cosine Similarity + Gemini AI giúp tìm việc phù hợp nhất</p>
        </div>

        <div className="text-center">
          <div className="mx-auto w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mb-6">
            <Award className="w-8 h-8 text-purple-600" />
          </div>
          <h3 className="text-xl font-semibold mb-3">Giải thích rõ ràng</h3>
          <p className="text-gray-600">Hiểu tại sao bạn phù hợp với từng công việc</p>
        </div>
      </div>
    </div>
  );
}