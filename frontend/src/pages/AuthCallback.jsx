import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.jsx'

function AuthCallback() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { login } = useAuth()
  const [error, setError] = useState(null)

  useEffect(() => {
    const handleCallback = async () => {
      const token = searchParams.get('token')

      if (token) {
        try {
          // Wait for login to complete before navigating
          await login(token)
          navigate('/dashboard')
        } catch (err) {
          console.error('Login failed:', err)
          setError('Authentication failed. Please try again.')
          setTimeout(() => navigate('/login'), 2000)
        }
      } else {
        // If no token, redirect to login
        navigate('/login')
      }
    }

    handleCallback()
  }, [searchParams, login, navigate])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-lg text-gray-600">
          {error ? error : 'Completing sign in...'}
        </p>
      </div>
    </div>
  )
}

export default AuthCallback
