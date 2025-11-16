import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.jsx'
import { profile } from '../services/api'

function Profile() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [profileData, setProfileData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })
  const [showSyncModal, setShowSyncModal] = useState(false)
  const [syncUrl, setSyncUrl] = useState('')

  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    try {
      const response = await profile.getMyProfile()
      setProfileData(response.data)
    } catch (error) {
      console.error('Failed to fetch profile:', error)
      showMessage('error', 'Failed to load profile data')
    } finally {
      setLoading(false)
    }
  }

  const showMessage = (type, text) => {
    setMessage({ type, text })
    setTimeout(() => setMessage({ type: '', text: '' }), 5000)
  }

  const handleSyncProfile = () => {
    setSyncUrl(profileData?.profile_url || '')
    setShowSyncModal(true)
  }

  const handleSyncSubmit = async () => {
    if (!syncUrl) {
      showMessage('error', 'LinkedIn profile URL is required')
      return
    }

    if (!syncUrl.includes('linkedin.com/in/')) {
      showMessage('error', 'Please enter a valid LinkedIn profile URL')
      return
    }

    setShowSyncModal(false)
    setSyncing(true)
    showMessage('info', 'Starting profile sync from LinkedIn... This may take up to 3 minutes.')

    try {
      await profile.syncWithApify({ profile_url: syncUrl })
      showMessage('success', 'Profile synced successfully from LinkedIn!')
      await fetchProfile()
    } catch (error) {
      console.error('Failed to sync profile:', error)
      showMessage('error', error.response?.data?.detail || 'Failed to sync profile. Please try again.')
    } finally {
      setSyncing(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-lg text-gray-600">Loading profile...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-gray-600 hover:text-gray-900"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <h1 className="text-2xl font-bold text-gray-900">Your Profile</h1>
          </div>
          <span className="text-sm text-gray-600">{user?.email}</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Message Banner */}
        {message.text && (
          <div
            className={`mb-6 p-4 rounded-lg ${
              message.type === 'success'
                ? 'bg-green-50 border-l-4 border-green-400 text-green-700'
                : message.type === 'error'
                ? 'bg-red-50 border-l-4 border-red-400 text-red-700'
                : 'bg-blue-50 border-l-4 border-blue-400 text-blue-700'
            }`}
          >
            {message.text}
          </div>
        )}

        {/* Sync Profile Card */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">LinkedIn Profile</h2>
              {profileData && (
                <p className="text-sm text-gray-500 mt-1">
                  Last synced: {new Date(profileData.last_synced_at).toLocaleDateString()}
                </p>
              )}
            </div>
            <button
              onClick={handleSyncProfile}
              disabled={syncing}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors"
            >
              {syncing ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Syncing...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Sync from LinkedIn
                </>
              )}
            </button>
          </div>
          <p className="text-gray-600 text-sm">
            Click the button above to automatically import or update your LinkedIn profile data.
          </p>
        </div>

        {/* Profile Data Display */}
        {profileData ? (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Profile Data</h2>

            {/* Headline & Summary */}
            {profileData.headline && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Professional Headline</h3>
                <p className="text-gray-900">{profileData.headline}</p>
              </div>
            )}

            {profileData.summary && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Summary</h3>
                <p className="text-gray-700 whitespace-pre-line">{profileData.summary}</p>
              </div>
            )}

            {/* Experience */}
            {profileData.experiences && profileData.experiences.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  Experience ({profileData.experiences.length})
                </h3>
                <div className="space-y-4">
                  {profileData.experiences.map((exp, index) => (
                    <div key={index} className="border-l-2 border-gray-200 pl-4">
                      <p className="font-semibold text-gray-900">{exp.title || exp.position || 'Position'}</p>
                      <p className="text-sm text-gray-600">{exp.company}</p>
                      <p className="text-xs text-gray-500">
                        {exp.start_date || exp.startDate} - {exp.end_date || exp.endDate || 'Present'}
                      </p>
                      {exp.description && (
                        <p className="text-sm text-gray-700 mt-2">{exp.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Education */}
            {profileData.education && profileData.education.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                  </svg>
                  Education ({profileData.education.length})
                </h3>
                <div className="space-y-3">
                  {profileData.education.map((edu, index) => (
                    <div key={index} className="border-l-2 border-gray-200 pl-4">
                      <p className="font-semibold text-gray-900">{edu.degree || edu.fieldOfStudy}</p>
                      <p className="text-sm text-gray-600">{edu.school || edu.schoolName}</p>
                      {edu.graduation_year && (
                        <p className="text-xs text-gray-500">Graduated: {edu.graduation_year}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Skills */}
            {profileData.skills && profileData.skills.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                  </svg>
                  Skills ({profileData.skills.length})
                </h3>
                <div className="flex flex-wrap gap-2">
                  {profileData.skills.map((skill, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                    >
                      {typeof skill === 'string' ? skill : skill.name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {(!profileData.experiences || profileData.experiences.length === 0) &&
             (!profileData.education || profileData.education.length === 0) &&
             (!profileData.skills || profileData.skills.length === 0) && (
              <div className="text-center py-8">
                <p className="text-gray-500">No profile data found. Click "Sync from LinkedIn" to import your profile.</p>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-yellow-50 border-l-4 border-yellow-500 p-6 rounded-lg">
            <p className="text-yellow-800 font-semibold mb-2">No profile data found</p>
            <p className="text-yellow-700 text-sm">
              Click "Sync from LinkedIn" above to import your profile data.
            </p>
          </div>
        )}
      </main>

      {/* Sync Profile Modal */}
      {showSyncModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-2xl p-8 max-w-lg w-full mx-4">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Sync from LinkedIn</h2>
              <p className="text-gray-600">
                Enter your LinkedIn profile URL to automatically import your complete profile data.
              </p>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                LinkedIn Profile URL
              </label>
              <input
                type="url"
                value={syncUrl}
                onChange={(e) => setSyncUrl(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSyncSubmit()}
                placeholder="https://www.linkedin.com/in/yourname"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                autoFocus
              />
              <p className="mt-2 text-sm text-gray-500">
                Example: https://www.linkedin.com/in/antoine-pedretti-997ab2205/
              </p>
            </div>

            <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-blue-700">
                    This process may take up to 3 minutes. We'll scrape your public LinkedIn data using our service accounts.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowSyncModal(false)}
                className="flex-1 px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSyncSubmit}
                disabled={!syncUrl}
                className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors"
              >
                Start Sync
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Profile
