import { useState, useEffect, createContext, useContext } from 'react'
import { auth } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      setLoading(false)
      return
    }

    try {
      const response = await auth.getCurrentUser()
      setUser(response.data)
    } catch (error) {
      console.error('Auth check failed:', error)
      localStorage.removeItem('token')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (token) => {
    localStorage.setItem('token', token)
    await checkAuth()
  }

  const logout = () => {
    localStorage.removeItem('token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    // Return mock auth for now if provider not available
    const token = localStorage.getItem('token')
    return {
      user: token ? { email: 'user@example.com' } : null,
      loading: false,
      login: async (token) => localStorage.setItem('token', token),
      logout: () => localStorage.removeItem('token'),
      checkAuth: async () => {},
    }
  }
  return context
}
