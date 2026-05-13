'use client';
import { useState } from 'react';
import api from '@/lib/api';
import { toast } from 'sonner';
import { Upload, FileText } from 'lucide-react';

export default function CVUploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await api.post('/api/v1/cv/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      toast.success(res.data.message);
      setFile(null);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Upload thất bại");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto mt-12 px-6">
      <div className="text-center mb-10">
        <FileText className="mx-auto text-purple-600" size={80} />
        <h1 className="text-4xl font-bold mt-4">Upload CV của bạn</h1>
        <p className="text-gray-600 mt-2">Hệ thống sẽ tự động phân tích và gợi ý việc làm phù hợp</p>
      </div>

      <div className="border-2 border-dashed border-purple-300 rounded-2xl p-12 text-center hover:border-purple-500 transition">
        <input
          type="file"
          accept=".pdf,.docx"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="hidden"
          id="cv-upload"
        />
        <label htmlFor="cv-upload" className="cursor-pointer">
          <Upload className="mx-auto text-purple-600 mb-4" size={60} />
          <p className="text-lg font-medium">{file ? file.name : "Chọn file PDF hoặc DOCX"}</p>
          <p className="text-sm text-gray-500 mt-1">Kéo thả hoặc click để chọn</p>
        </label>
      </div>

      {file && (
        <button
          onClick={handleUpload}
          disabled={loading}
          className="w-full mt-6 bg-purple-600 hover:bg-purple-700 text-white py-4 rounded-xl font-semibold disabled:opacity-70"
        >
          {loading ? "Đang xử lý với AI..." : "Upload & Phân tích CV"}
        </button>
      )}
    </div>
  );
}