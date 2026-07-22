import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL })

// Attach the saved token to every request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('acme_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// If the token expired, clear it and bounce back to the sign-in screen.
api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401 && !error.config.url.includes('/auth/login')) {
      localStorage.removeItem('acme_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const readError = (error, fallback = 'Something went wrong. Try again.') => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join(', ')
  return fallback
}

export default api
