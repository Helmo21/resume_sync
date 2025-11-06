import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.jsx'
import { uploadedResumes, jobSearch } from '../services/api'

function FindJobs() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [uploadedResumesList, setUploadedResumesList] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [loading, setLoading] = useState(true)
  const [selectedResume, setSelectedResume] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)

  // Job search state
  const [scrapedJobs, setScrapedJobs] = useState([])
  const [searchingJobs, setSearchingJobs] = useState(false)
  const [searchLocation, setSearchLocation] = useState('')
  const [searchRemoteOnly, setSearchRemoteOnly] = useState(false)
  const [searchTaskId, setSearchTaskId] = useState(null)
  const [searchStatus, setSearchStatus] = useState(null)
  const [minMatchScore, setMinMatchScore] = useState(0)

  useEffect(() => {
    loadUploadedResumes()
  }, [])

  const loadUploadedResumes = async () => {
    try {
      setLoading(true)
      const response = await uploadedResumes.listUploadedResumes()
      setUploadedResumesList(response.data)
    } catch (error) {
      console.error('Failed to load uploaded resumes:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = (event) => {
    const file = event.target.files[0]
    if (file) {
      // Validate file type
      const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
      if (!validTypes.includes(file.type)) {
        setUploadError('Please upload a PDF or DOCX file')
        setSelectedFile(null)
        return
      }

      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setUploadError('File size must be less than 10MB')
        setSelectedFile(null)
        return
      }

      setSelectedFile(file)
      setUploadError(null)
      setUploadSuccess(false)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    try {
      setUploading(true)
      setUploadError(null)
      setUploadSuccess(false)

      const response = await uploadedResumes.uploadResume(selectedFile)

      setUploadSuccess(true)
      setSelectedFile(null)

      // Reset file input
      const fileInput = document.getElementById('resume-file-input')
      if (fileInput) fileInput.value = ''

      // Reload list
      await loadUploadedResumes()

      // Show success message for 3 seconds
      setTimeout(() => setUploadSuccess(false), 3000)
    } catch (error) {
      console.error('Upload failed:', error)
      setUploadError(
        error.response?.data?.detail || 'Failed to upload resume. Please try again.'
      )
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (resumeId) => {
    if (!confirm('Are you sure you want to delete this resume?')) return

    try {
      await uploadedResumes.deleteUploadedResume(resumeId)
      await loadUploadedResumes()
      if (selectedResume?.id === resumeId) {
        setSelectedResume(null)
      }
    } catch (error) {
      console.error('Failed to delete resume:', error)
      alert('Failed to delete resume. Please try again.')
    }
  }

  const handleViewAnalysis = async (resumeId) => {
    try {
      const response = await uploadedResumes.getUploadedResume(resumeId)
      setSelectedResume(response.data)

      // Load scraped jobs for this resume
      await loadScrapedJobs(resumeId)
    } catch (error) {
      console.error('Failed to load resume:', error)
      alert('Failed to load resume details.')
    }
  }

  const handleAnalyze = async (resumeId) => {
    try {
      setAnalyzing(true)
      const response = await uploadedResumes.analyzeResume(resumeId)
      setSelectedResume(response.data)
      await loadUploadedResumes()
      alert('Resume analyzed successfully!')
    } catch (error) {
      console.error('Failed to analyze resume:', error)
      alert(error.response?.data?.detail || 'Failed to analyze resume. Please try again.')
    } finally {
      setAnalyzing(false)
    }
  }


  const loadScrapedJobs = async (resumeId) => {
    try {
      const response = await jobSearch.getMatchedJobs(resumeId, { min_score: minMatchScore, limit: 50 })
      setScrapedJobs(response.data)
    } catch (error) {
      console.error('Failed to load scraped jobs:', error)
      setScrapedJobs([])
    }
  }

  const pollSearchStatus = async (taskId, resumeId) => {
    const maxAttempts = 60 // 5 minutes max (60 * 5s = 300s)
    let attempts = 0

    const poll = async () => {
      try {
        const response = await jobSearch.getSearchStatus(taskId)
        const status = response.data.status
        const result = response.data.result

        setSearchStatus(status)

        if (status === 'SUCCESS') {
          clearInterval(pollInterval)
          setSearchingJobs(false)
          setSearchTaskId(null)
          setSearchStatus(null)

          alert(`Successfully found ${result.jobs_found} jobs! (${result.jobs_saved} new) | Scraper: ${result.scraper_mode} | Top Match: ${result.top_match_score || 'N/A'}%`)

          // Reload scraped jobs
          await loadScrapedJobs(resumeId)
        } else if (status === 'FAILURE') {
          clearInterval(pollInterval)
          setSearchingJobs(false)
          setSearchTaskId(null)
          setSearchStatus(null)

          const errorMsg = result?.error || result || 'Unknown error'
          alert(`Job search failed: ${errorMsg}`)
        } else if (attempts >= maxAttempts) {
          clearInterval(pollInterval)
          setSearchingJobs(false)
          setSearchTaskId(null)
          setSearchStatus(null)

          alert('Job search timed out. Please try again.')
        }

        attempts++
      } catch (error) {
        console.error('Failed to poll status:', error)
        clearInterval(pollInterval)
        setSearchingJobs(false)
        setSearchTaskId(null)
        setSearchStatus(null)
      }
    }

    const pollInterval = setInterval(poll, 5000) // Poll every 5 seconds
    poll() // Initial poll
  }

  const handleSearchJobs = async (resumeId) => {
    try {
      setSearchingJobs(true)
      setSearchStatus('PENDING')

      const response = await jobSearch.startJobSearch({
        resume_id: resumeId,
        location: searchLocation || null,
        remote_only: searchRemoteOnly,
        max_results: 50  // Reduced to 50 to avoid timeout (balance of speed vs quantity)
      })

      const taskId = response.data.task_id
      setSearchTaskId(taskId)

      // Start polling
      pollSearchStatus(taskId, resumeId)
    } catch (error) {
      console.error('Job search failed:', error)
      alert(error.response?.data?.detail || 'Failed to start job search. Please try again.')
      setSearchingJobs(false)
      setSearchStatus(null)
    }
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
            <h1 className="text-2xl font-bold text-gray-900">Find Jobs</h1>
          </div>
          <span className="text-sm text-gray-600">{user?.email}</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Upload Section */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Upload Your Resume</h2>
          <p className="text-gray-600 mb-6">
            Upload your resume (PDF or DOCX) to find matching job opportunities on LinkedIn.
          </p>

          {/* Upload Area */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-purple-500 transition-colors">
            <input
              id="resume-file-input"
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileSelect}
              className="hidden"
            />

            {!selectedFile ? (
              <div>
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
                <p className="mt-2 text-sm text-gray-600">
                  <label
                    htmlFor="resume-file-input"
                    className="cursor-pointer text-purple-600 hover:text-purple-700 font-medium"
                  >
                    Click to upload
                  </label>{' '}
                  or drag and drop
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  PDF or DOCX (max 10MB)
                </p>
              </div>
            ) : (
              <div>
                <svg
                  className="mx-auto h-12 w-12 text-green-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p className="mt-2 text-sm font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
                <div className="mt-4 flex gap-3 justify-center">
                  <button
                    onClick={() => document.getElementById('resume-file-input').click()}
                    className="px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Choose Different File
                  </button>
                  <button
                    onClick={handleUpload}
                    disabled={uploading}
                    className="px-6 py-2 text-sm text-white bg-purple-600 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {uploading ? 'Uploading...' : 'Upload & Analyze'}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Error Message */}
          {uploadError && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm text-red-700">{uploadError}</p>
            </div>
          )}

          {/* Success Message */}
          {uploadSuccess && (
            <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-sm text-green-700">Resume uploaded and parsed successfully!</p>
            </div>
          )}
        </div>

        {/* Uploaded Resumes List */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Your Uploaded Resumes</h2>

          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="animate-pulse border border-gray-200 rounded-lg p-4">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
              ))}
            </div>
          ) : uploadedResumesList.length === 0 ? (
            <div className="text-center py-12">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
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
              <p className="mt-4 text-gray-600">No resumes uploaded yet</p>
              <p className="text-sm text-gray-500 mt-1">Upload your first resume to get started</p>
            </div>
          ) : (
            <div className="space-y-4">
              {uploadedResumesList.map((resume) => (
                <div
                  key={resume.id}
                  className="border border-gray-200 rounded-lg p-4 hover:border-purple-300 transition-colors"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <svg
                          className="w-5 h-5 text-gray-500"
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
                        <h3 className="font-semibold text-gray-900">{resume.filename}</h3>
                        {resume.has_analysis && (
                          <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
                            Analyzed
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        Uploaded {new Date(resume.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      {resume.has_analysis ? (
                        <button
                          onClick={() => handleViewAnalysis(resume.id)}
                          className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        >
                          View Analysis
                        </button>
                      ) : (
                        <button
                          onClick={() => handleAnalyze(resume.id)}
                          disabled={analyzing}
                          className="px-3 py-1 text-sm text-purple-600 hover:bg-purple-50 rounded-lg transition-colors disabled:opacity-50"
                        >
                          {analyzing ? 'Analyzing...' : 'Analyze'}
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(resume.id)}
                        className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Analysis Results Modal */}
        {selectedResume && selectedResume.analyzed_data && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-900">Resume Analysis</h2>
                <button
                  onClick={() => setSelectedResume(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="p-6 space-y-6">
                {/* Technical Skills */}
                {selectedResume.analyzed_data.technical_skills?.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900 mb-3">Technical Skills</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedResume.analyzed_data.technical_skills.map((skill, idx) => (
                        <span key={idx} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Soft Skills */}
                {selectedResume.analyzed_data.soft_skills?.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900 mb-3">Soft Skills</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedResume.analyzed_data.soft_skills.map((skill, idx) => (
                        <span key={idx} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Experience Level */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-purple-50 rounded-lg p-4">
                    <p className="text-sm text-purple-600 font-medium">Experience</p>
                    <p className="text-2xl font-bold text-purple-900">{selectedResume.analyzed_data.years_of_experience} years</p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4">
                    <p className="text-sm text-purple-600 font-medium">Seniority Level</p>
                    <p className="text-2xl font-bold text-purple-900 capitalize">{selectedResume.analyzed_data.seniority_level}</p>
                  </div>
                </div>

                {/* Job Titles */}
                {selectedResume.analyzed_data.job_titles?.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900 mb-3">Job Titles / Roles</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedResume.analyzed_data.job_titles.map((title, idx) => (
                        <span key={idx} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium">
                          {title}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Industries */}
                {selectedResume.analyzed_data.industries?.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900 mb-3">Industries / Domains</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedResume.analyzed_data.industries.map((industry, idx) => (
                        <span key={idx} className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm">
                          {industry}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Preferences */}
                <div className="grid grid-cols-2 gap-4">
                  {selectedResume.analyzed_data.preferred_languages?.length > 0 && (
                    <div className="bg-yellow-50 rounded-lg p-4">
                      <p className="text-sm text-yellow-600 font-medium mb-2">Preferred Languages</p>
                      <p className="text-sm text-yellow-900">{selectedResume.analyzed_data.preferred_languages.join(', ')}</p>
                    </div>
                  )}
                  {selectedResume.analyzed_data.remote_preference && (
                    <div className="bg-yellow-50 rounded-lg p-4">
                      <p className="text-sm text-yellow-600 font-medium mb-2">Remote Preference</p>
                      <p className="text-sm text-yellow-900 capitalize">{selectedResume.analyzed_data.remote_preference}</p>
                    </div>
                  )}
                </div>

                {/* Search Keywords */}
                {selectedResume.analyzed_data.search_keywords?.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-lg text-gray-900 mb-3">LinkedIn Search Keywords</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedResume.analyzed_data.search_keywords.map((keyword, idx) => (
                        <span key={idx} className="px-2 py-1 bg-gray-200 text-gray-700 rounded text-xs">
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Job Search Section */}
                <div className="border-t pt-6">
                  <h3 className="font-semibold text-lg text-gray-900 mb-4">LinkedIn Job Search</h3>

                  {/* Search Options */}
                  <div className="space-y-3 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Location (optional)
                      </label>
                      <input
                        type="text"
                        value={searchLocation}
                        onChange={(e) => setSearchLocation(e.target.value)}
                        placeholder="e.g., Paris, France"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                      />
                    </div>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        id="remoteOnly"
                        checked={searchRemoteOnly}
                        onChange={(e) => setSearchRemoteOnly(e.target.checked)}
                        className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                      />
                      <label htmlFor="remoteOnly" className="ml-2 text-sm text-gray-700">
                        Remote jobs only
                      </label>
                    </div>
                  </div>

                  {/* Search Button */}
                  <button
                    onClick={() => handleSearchJobs(selectedResume.id)}
                    disabled={searchingJobs}
                    className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  >
                    {searchingJobs ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Searching LinkedIn... (1-3 min)
                      </span>
                    ) : (
                      'Search Jobs on LinkedIn'
                    )}
                  </button>

                  {/* Warning about search time + Status */}
                  {searchingJobs && (
                    <div className="mt-3 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <svg className="animate-spin h-4 w-4 text-yellow-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        <p className="text-xs font-medium text-yellow-800">
                          Status: {searchStatus || 'Starting...'}
                        </p>
                      </div>
                      <p className="text-xs text-yellow-800">
                        Searching LinkedIn with AI matching (1-3 minutes). Please don't close this window.
                      </p>
                    </div>
                  )}

                  {/* Scraped Jobs Display */}
                  {scrapedJobs.length > 0 && (
                    <div className="mt-6">
                      <div className="flex justify-between items-center mb-3">
                        <h4 className="font-medium text-gray-900">
                          Found Jobs ({scrapedJobs.length})
                        </h4>
                        <div className="flex items-center gap-2">
                          <label className="text-xs text-gray-600">Min Match:</label>
                          <select
                            value={minMatchScore}
                            onChange={(e) => {
                              setMinMatchScore(Number(e.target.value))
                              loadScrapedJobs(selectedResume.id)
                            }}
                            className="text-xs px-2 py-1 border border-gray-300 rounded"
                          >
                            <option value={0}>All Matches (0%+)</option>
                            <option value={40}>Decent+ (40%+)</option>
                            <option value={60}>Good+ (60%+)</option>
                            <option value={80}>Strong+ (80%+)</option>
                          </select>
                        </div>
                      </div>
                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {scrapedJobs.map((job) => (
                          <div
                            key={job.id}
                            className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
                          >
                            <div className="flex justify-between items-start mb-2">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <h5 className="font-semibold text-gray-900">{job.job_title || 'Untitled'}</h5>
                                  {job.match_score !== null && job.match_score !== undefined && (
                                    <span
                                      className={`px-2 py-1 rounded text-xs font-bold ${
                                        job.match_score >= 80
                                          ? 'bg-green-100 text-green-800'
                                          : job.match_score >= 60
                                          ? 'bg-blue-100 text-blue-800'
                                          : job.match_score >= 40
                                          ? 'bg-yellow-100 text-yellow-800'
                                          : 'bg-orange-100 text-orange-800'
                                      }`}
                                      title={
                                        job.match_score >= 80 ? 'Strong Match - Apply with confidence!' :
                                        job.match_score >= 60 ? 'Good Match - Worth applying' :
                                        job.match_score >= 40 ? 'Decent Match - Could grow into role' :
                                        'Partial Match - Consider if interested in learning'
                                      }
                                    >
                                      {job.match_score}% Match
                                    </span>
                                  )}
                                </div>
                                <p className="text-sm text-gray-600">{job.company_name || 'Unknown Company'}</p>
                              </div>
                              {job.is_remote && (
                                <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
                                  Remote
                                </span>
                              )}
                            </div>

                            {job.location && (
                              <p className="text-sm text-gray-500 mb-2">
                                📍 {job.location}
                              </p>
                            )}

                            {job.posted_date && (
                              <p className="text-xs text-gray-400 mb-2">
                                Posted: {job.posted_date}
                              </p>
                            )}

                            {/* Match Details */}
                            {job.match_details && (
                              <div className="mb-3 p-3 bg-gray-50 rounded border border-gray-200">
                                <p className="text-xs font-medium text-gray-700 mb-2">
                                  🎯 AI Match Analysis
                                  <span className="ml-2 text-gray-500 font-normal">(Priority: Tech Skills → Soft Skills → Experience → Industry)</span>
                                </p>

                                {job.match_details.matching_skills?.length > 0 && (
                                  <div className="mb-2">
                                    <p className="text-xs text-green-700 font-medium mb-1">
                                      ✓ Matching Skills ({job.match_details.matching_skills.length}):
                                    </p>
                                    <div className="flex flex-wrap gap-1">
                                      {job.match_details.matching_skills.slice(0, 8).map((skill, idx) => (
                                        <span key={idx} className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">
                                          {skill}
                                        </span>
                                      ))}
                                      {job.match_details.matching_skills.length > 8 && (
                                        <span className="text-xs text-gray-500">+{job.match_details.matching_skills.length - 8} more</span>
                                      )}
                                    </div>
                                  </div>
                                )}

                                {job.match_details.missing_skills?.length > 0 && (
                                  <div className="mb-2">
                                    <p className="text-xs text-orange-700 font-medium mb-1">⚠ Skills to Develop:</p>
                                    <div className="flex flex-wrap gap-1">
                                      {job.match_details.missing_skills.slice(0, 5).map((skill, idx) => (
                                        <span key={idx} className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded text-xs">
                                          {skill}
                                        </span>
                                      ))}
                                      {job.match_details.missing_skills.length > 5 && (
                                        <span className="text-xs text-gray-500">+{job.match_details.missing_skills.length - 5} more</span>
                                      )}
                                    </div>
                                  </div>
                                )}

                                {job.match_details.experience_fit && (
                                  <p className="text-xs text-gray-600 mb-1">
                                    <span className="font-medium">Experience Fit:</span> {job.match_details.experience_fit}
                                  </p>
                                )}

                                {job.match_details.reasoning && (
                                  <p className="text-xs text-gray-600 italic">
                                    "{job.match_details.reasoning}"
                                  </p>
                                )}
                              </div>
                            )}

                            {job.description && (
                              <p className="text-sm text-gray-700 mb-3 line-clamp-2">
                                {job.description}
                              </p>
                            )}

                            <a
                              href={job.linkedin_post_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                            >
                              Apply on LinkedIn
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                              </svg>
                            </a>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 pt-4 border-t">
                  <button
                    onClick={() => handleAnalyze(selectedResume.id)}
                    disabled={analyzing}
                    className="px-4 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                  >
                    {analyzing ? 'Re-analyzing...' : 'Re-analyze'}
                  </button>
                  <button
                    onClick={() => setSelectedResume(null)}
                    className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}


        {/* Instructions Section */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-2">How It Works</h3>
          <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
            <li>Upload your resume (PDF or DOCX)</li>
            <li>AI analyzes it and extracts search keywords</li>
            <li>Click "View Analysis" on an analyzed resume</li>
            <li>Use "Search Jobs on LinkedIn" to find matching jobs with AI matching</li>
            <li>The system automatically searches LinkedIn, analyzes each job, and ranks them by match score</li>
            <li>View detailed match analysis including matching skills, missing skills, and experience fit</li>
            <li>Filter results by minimum match score (50%, 70%, 85%+)</li>
          </ol>
        </div>
      </main>
    </div>
  )
}

export default FindJobs
