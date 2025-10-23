import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { resumes } from '../services/api'

function ResumeHistory() {
  const navigate = useNavigate()
  const [resumeList, setResumeList] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchResumes()
  }, [])

  const fetchResumes = async () => {
    try {
      const response = await resumes.listResumes()
      setResumeList(response.data.resumes)
    } catch (err) {
      console.error('Failed to fetch resumes:', err)
      setError('Failed to load resumes')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-gray-600 hover:text-gray-900"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                />
              </svg>
            </button>
            <h1 className="text-2xl font-bold text-gray-900">
              Resume History
            </h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {loading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {!loading && !error && resumeList.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-gray-400"
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
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              No resumes yet
            </h3>
            <p className="text-gray-600 mb-6">
              Generate your first resume to get started
            </p>
            <button
              onClick={() => navigate('/generate')}
              className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition duration-200"
            >
              Generate Resume
            </button>
          </div>
        )}

        {!loading && !error && resumeList.length > 0 && (
          <div>
            <div className="mb-6 flex justify-between items-center">
              <p className="text-gray-600">
                {resumeList.length} resume{resumeList.length !== 1 ? 's' : ''}{' '}
                generated
              </p>
              <button
                onClick={() => navigate('/generate')}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
              >
                Generate New
              </button>
            </div>

            <div className="grid gap-6">
              {resumeList.map((resume) => (
                <div
                  key={resume.id}
                  className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition duration-200"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <h3 className="text-xl font-semibold text-gray-900 mb-1">
                        {resume.job_title || 'Untitled Resume'}
                      </h3>
                      {resume.company_name && (
                        <p className="text-gray-600 mb-2">
                          {resume.company_name}
                        </p>
                      )}
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span>Template: {resume.template_id}</span>
                        <span>•</span>
                        <span>{formatDate(resume.created_at)}</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {resume.pdf_url && (
                        <button
                          onClick={() => window.open(resume.pdf_url, '_blank')}
                          className="bg-blue-100 hover:bg-blue-200 text-blue-700 font-semibold py-2 px-4 rounded-lg transition duration-200"
                        >
                          PDF
                        </button>
                      )}
                      {resume.docx_url && (
                        <button
                          onClick={() =>
                            window.open(resume.docx_url, '_blank')
                          }
                          className="bg-green-100 hover:bg-green-200 text-green-700 font-semibold py-2 px-4 rounded-lg transition duration-200"
                        >
                          DOCX
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default ResumeHistory
