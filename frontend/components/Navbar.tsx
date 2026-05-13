'use client';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { LogOut, User, Upload } from 'lucide-react';
import { useEffect, useState } from 'react';

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsLoggedIn(!!token);
  }, [pathname]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setIsLoggedIn(false);
    router.push('/login');
  };

  if (pathname === '/login' || pathname === '/register') {
    return null;
  }

  return (
    <nav className="border-b bg-white sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
        <Link href="/" className="text-2xl font-bold text-purple-600">JobMatch AI</Link>
        
        {isLoggedIn ? (
          <div className="flex items-center gap-6">
            <Link href="/dashboard" className="hover:text-purple-600 font-medium">Dashboard</Link>
            <Link href="/cv-upload" className="hover:text-purple-600 font-medium flex items-center gap-1">
              <Upload size={18} /> Upload CV
            </Link>
            
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 text-red-600 hover:text-red-700 transition"
            >
              <LogOut size={18} /> Đăng xuất
            </button>
          </div>
        ) : (
          <Link 
            href="/login" 
            className="bg-purple-600 text-white px-6 py-2.5 rounded-xl hover:bg-purple-700 font-medium"
          >
            Đăng nhập
          </Link>
        )}
      </div>
    </nav>
  );
}