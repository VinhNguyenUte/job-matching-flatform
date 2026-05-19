import { create } from 'zustand'

export const useAuthStore = create((set) => ({
  user: (() => {
    try {
      const savedUser = localStorage.getItem('user')
      return savedUser ? JSON.parse(savedUser) : null
    } catch {
      return null
    }
  })(),
  
  token: localStorage.getItem('access_token') || null,
  isLoading: false,

  setUser: (user) => {
    if (user) {
      localStorage.setItem('user', JSON.stringify(user))
    } else {
      localStorage.removeItem('user')
    }
    set({ user })
  },
  
  setToken: (token) => {
    if (token) {
      localStorage.setItem('access_token', token)
    } else {
      localStorage.removeItem('access_token')
    }
    set({ token })
  },
  setLoading: (isLoading) => set({ isLoading }),

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user') 
    set({ user: null, token: null })
  },
}))

export const useJobStore = create((set) => ({
  jobs: [],
  selectedJob: null,
  isLoading: false,
  filters: {
    search: '',
    city: '',
    jobType: '',
  },

  setJobs: (jobs) => set({ jobs }),
  setSelectedJob: (job) => set({ selectedJob: job }),
  setLoading: (isLoading) => set({ isLoading }),
  setFilters: (filters) => set((state) => ({ filters: { ...state.filters, ...filters } })),
}))

export const useCVStore = create((set) => ({
  cvs: [],
  selectedCV: null,
  isLoading: false,
  
  cvId: null,
  cvInfo: null, 

  setCVs: (cvs) => set({ cvs }),
  setSelectedCV: (cv) => set({ selectedCV: cv }),
  setLoading: (isLoading) => set({ isLoading }),
  
  setCvId: (cvId) => set({ cvId }),
  setCvInfo: (cvInfo) => set({ cvInfo }),
}))