import { BrowserRouter as Router, Routes, Route , useNavigate} from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import JobsPage from './pages/JobsPage'
import JobDetailPage from './pages/JobDetailPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import ProfilePage from './pages/ProfilePage'
import { use } from 'react'
import { useAuthStore } from './lib/store'

function App() {
  // const navigate = useNavigate()
  // useEffect(() => {
  //   const storedUser = localStorage.getItem('user')
  //   if (storedUser) {
  //     setUser(JSON.parse(storedUser))
  //   }else{
  //     navigate('/login')
  //   }

  // }, [])

  // const { setUser, setToken } = useAuthStore()
  // useEffect(() => {
  //   const storedUser = localStorage.getItem('user')
  //   const storedToken = localStorage.getItem('access_token')
  //   if (storedUser && storedToken) {
  //     setUser(JSON.parse(storedUser))
  //     setToken(storedToken)
  //   }
  // }, [])

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/jobs/:id" element={<JobDetailPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/profile" element={<ProfilePage />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App
