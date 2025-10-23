import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auth
export const auth = {
  getLinkedInAuthUrl: () => api.get('/auth/linkedin/login'),
  getCurrentUser: () => api.get('/auth/me'),
}

// Profile
export const profile = {
  getMyProfile: () => api.get('/profile/me'),
  updateProfile: (data) => api.put('/profile/update', data),
  resyncProfile: () => api.post('/profile/resync'),
  syncWithCamoufox: () => api.post('/profile/sync-with-camoufox'),
  syncWithApify: (data = {}) => api.post('/profile/sync-with-apify', data),
}

// Jobs
export const jobs = {
  scrapeJob: (jobUrl) => api.post('/jobs/scrape', { job_url: jobUrl }),
  listJobs: () => api.get('/jobs/'),
  getJob: (id) => api.get(`/jobs/${id}`),
}

// Resumes
export const resumes = {
  generateResume: (data) => api.post('/resumes/generate', data),
  generateOptions: (data) => api.post('/resumes/generate-options', data),
  listResumes: () => api.get('/resumes/'),
  getResume: (id) => api.get(`/resumes/${id}`),
  downloadResume: (id, format = 'pdf') =>
    api.get(`/resumes/${id}/download`, { params: { format } }),
  listTemplates: () => api.get('/resumes/templates/list'),
}

export default api
