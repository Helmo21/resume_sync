import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.jsx'
import { profile, jobs, resumes } from '../services/api'

function Dashboard() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [profileData, setProfileData] = useState(null)
  const [scrapedJobs, setScrapedJobs] = useState([])
  const [recentResumes, setRecentResumes] = useState([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [showSyncModal, setShowSyncModal] = useState(false)
  const [syncUrl, setSyncUrl] = useState('')
  const [message, setMessage] = useState({ type: '', text: '' })

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch profile
        const profileResponse = await profile.getMyProfile()
        setProfileData(profileResponse.data)

        // Fetch recent scraped jobs
        try {
          const jobsResponse = await jobs.listJobs()
          setScrapedJobs(jobsResponse.data.jobs.slice(0, 3)) // Show latest 3
        } catch (error) {
          console.error('Failed to fetch jobs:', error)
        }

        // Fetch recent resumes
        try {
          const resumesResponse = await resumes.listResumes()
          setRecentResumes(resumesResponse.data.resumes.slice(0, 3)) // Show latest 3
        } catch (error) {
          console.error('Failed to fetch resumes:', error)
        }
      } catch (error) {
        console.error('Failed to fetch profile:', error)
      } finally {
        setLoading(false)
      }
    }

    if (user) {
      fetchData()
    }
  }, [user])

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

      // Refresh profile data
      const profileResponse = await profile.getMyProfile()
      setProfileData(profileResponse.data)
    } catch (error) {
      console.error('Failed to sync profile:', error)
      showMessage('error', error.response?.data?.detail || 'Failed to sync profile. Please try again.')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">ResumeSync</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.email}</span>
            <button
              onClick={logout}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
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

        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to ResumeSync
          </h2>
          <p className="text-xl text-gray-600">
            Generate tailored resumes for any job posting in seconds
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {/* Generate New Resume Card */}
          <div
            onClick={() => navigate('/generate')}
            className="bg-white rounded-xl shadow-lg p-8 hover:shadow-xl transition duration-200 cursor-pointer border-2 border-transparent hover:border-blue-500"
          >
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-blue-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
            </div>
            <h3 className="text-2xl font-semibold text-gray-900 mb-2">
              Generate Resume
            </h3>
            <p className="text-gray-600">
              Create a new AI-tailored resume for a specific job posting
            </p>
          </div>

          {/* Find Jobs Card - NEW */}
          <div
            onClick={() => navigate('/find-jobs')}
            className="bg-white rounded-xl shadow-lg p-8 hover:shadow-xl transition duration-200 cursor-pointer border-2 border-transparent hover:border-purple-500"
          >
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-purple-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
            <h3 className="text-2xl font-semibold text-gray-900 mb-2">
              Find Jobs
            </h3>
            <p className="text-gray-600">
              Upload your resume and find matching job opportunities
            </p>
          </div>

          {/* Resume History Card */}
          <div
            onClick={() => navigate('/history')}
            className="bg-white rounded-xl shadow-lg p-8 hover:shadow-xl transition duration-200 cursor-pointer border-2 border-transparent hover:border-green-500"
          >
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-8 h-8 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h3 className="text-2xl font-semibold text-gray-900 mb-2">
              Resume History
            </h3>
            <p className="text-gray-600">
              View and download your previously generated resumes
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-12 bg-white rounded-xl shadow-lg p-8 max-w-4xl mx-auto">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">
            Your Stats
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-600">
                {recentResumes.length || user?.resumes_generated_count || 0}
              </p>
              <p className="text-sm text-gray-600">Resumes Generated</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-green-600">
                {scrapedJobs.length || 0}
              </p>
              <p className="text-sm text-gray-600">Jobs Scraped</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-purple-600">
                {profileData?.skills?.length || 0}
              </p>
              <p className="text-sm text-gray-600">Skills</p>
            </div>
          </div>
        </div>

        {/* Recent Scraped Jobs */}
        {scrapedJobs.length > 0 && (
          <div className="mt-12 bg-white rounded-xl shadow-lg p-8 max-w-4xl mx-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-gray-900">
                Recent Scraped Jobs
              </h3>
              <button
                onClick={() => navigate('/generate')}
                className="text-blue-600 hover:text-blue-700 font-medium text-sm"
              >
                Scrape New Job
              </button>
            </div>
            <div className="space-y-4">
              {scrapedJobs.map((job) => (
                <div
                  key={job.id}
                  className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors cursor-pointer"
                  onClick={() => navigate('/generate')}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-1">
                        {job.job_title}
                      </h4>
                      <p className="text-sm text-gray-600 mb-2">
                        {job.company_name} • {job.location}
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {job.employment_type && (
                          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
                            {job.employment_type}
                          </span>
                        )}
                        {job.seniority_level && (
                          <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs">
                            {job.seniority_level}
                          </span>
                        )}
                        {job.is_remote && (
                          <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
                            Remote
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">
                        {new Date(job.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* LinkedIn Profile Summary */}
        {loading ? (
          <div className="mt-12 bg-white rounded-xl shadow-lg p-8 max-w-4xl mx-auto">
            <div className="animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            </div>
          </div>
        ) : profileData ? (
          <div className="mt-12 bg-white rounded-xl shadow-lg p-8 max-w-4xl mx-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-semibold text-gray-900">
                Your LinkedIn Profile
              </h3>
              <div className="flex items-center gap-4">
                <span className="text-xs text-gray-500">
                  Last synced: {new Date(profileData.last_synced_at).toLocaleDateString()}
                </span>
                <button
                  onClick={handleSyncProfile}
                  disabled={syncing}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  {syncing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Syncing...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Sync Profile
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Profile Incomplete Warning */}
            {(!profileData.experiences || profileData.experiences.length === 0) && (
              <div className="mb-6 bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-yellow-700">
                      Your profile is incomplete. Sync your LinkedIn profile to import your work experience and education.
                      <button
                        onClick={handleSyncProfile}
                        className="ml-2 font-medium underline hover:text-yellow-800"
                      >
                        Sync now
                      </button>
                    </p>
                  </div>
                </div>
              </div>
            )}


            {/* Headline & Summary */}
            {profileData.headline && (
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Professional Headline</h4>
                <p className="text-gray-900">{profileData.headline}</p>
              </div>
            )}

            {profileData.summary && (
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-gray-700 mb-2">Summary</h4>
                <p className="text-gray-700 whitespace-pre-line">{profileData.summary}</p>
              </div>
            )}

            {/* Experience */}
            {profileData.experiences && profileData.experiences.length > 0 && (
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  Experience ({profileData.experiences.length})
                </h4>
                <div className="space-y-4">
                  {profileData.experiences.slice(0, 3).map((exp, index) => (
                    <div key={index} className="border-l-2 border-gray-200 pl-4">
                      <p className="font-semibold text-gray-900">{exp.title || exp.position || 'Position'}</p>
                      <p className="text-sm text-gray-600">{exp.company}</p>
                      <p className="text-xs text-gray-500">
                        {exp.start_date || exp.startDate} - {exp.end_date || exp.endDate || 'Present'}
                      </p>
                      {exp.description && (
                        <p className="text-sm text-gray-700 mt-2 line-clamp-2">{exp.description}</p>
                      )}
                    </div>
                  ))}
                  {profileData.experiences.length > 3 && (
                    <p className="text-sm text-gray-500 italic">
                      +{profileData.experiences.length - 3} more experience(s)
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Education */}
            {profileData.education && profileData.education.length > 0 && (
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
                  </svg>
                  Education ({profileData.education.length})
                </h4>
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
                <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
                  </svg>
                  Skills ({profileData.skills.length})
                </h4>
                <div className="flex flex-wrap gap-2">
                  {profileData.skills.slice(0, 15).map((skill, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                    >
                      {typeof skill === 'string' ? skill : skill.name}
                    </span>
                  ))}
                  {profileData.skills.length > 15 && (
                    <span className="px-3 py-1 bg-gray-200 text-gray-600 rounded-full text-sm">
                      +{profileData.skills.length - 15} more
                    </span>
                  )}
                </div>
              </div>
            )}

          </div>
        ) : (
          <div className="mt-12 bg-yellow-50 border-l-4 border-yellow-500 p-6 max-w-4xl mx-auto rounded-lg">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-yellow-800 font-semibold mb-2">
                  ⚠️ No profile data found
                </p>
                <p className="text-yellow-700 text-sm mb-4">
                  Your LinkedIn profile data is empty. Please sync your profile to enable resume generation.
                </p>
                <button
                  onClick={handleSyncProfile}
                  className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg font-medium text-sm transition-colors"
                >
                  Sync Your Profile
                </button>
              </div>
            </div>
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

export default Dashboard
