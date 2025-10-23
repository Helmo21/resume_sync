import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { resumes, jobs } from '../services/api'
import JobPreview from '../components/JobPreview'

function GenerateResume() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1) // 1: URL input, 2: Job preview, 3: Options, 4: Generating, 5: Choose template, 6: Done
  const [jobUrl, setJobUrl] = useState('')
  const [scrapedJob, setScrapedJob] = useState(null)
  const [loading, setLoading] = useState(false)
  const [scraping, setScraping] = useState(false)
  const [error, setError] = useState(null)

  // Pre-generation options
  const [useProfilePicture, setUseProfilePicture] = useState(true)
  const [additionalLinks, setAdditionalLinks] = useState([''])
  const [newLink, setNewLink] = useState('')

  // Resume options (2 templates generated)
  const [resumeOptions, setResumeOptions] = useState([])
  const [selectedOption, setSelectedOption] = useState(null)

  // No need to load templates - they're auto-selected based on job

  const handleScrapeJob = async (e) => {
    e.preventDefault()
    if (!jobUrl.trim()) {
      setError('Please enter a job URL')
      return
    }

    setScraping(true)
    setError(null)

    try {
      const response = await jobs.scrapeJob(jobUrl)
      setScrapedJob(response.data)
      setStep(2)
    } catch (err) {
      console.error('Failed to scrape job:', err)
      setError(
        err.response?.data?.detail || 'Failed to scrape job. Please check the URL and try again.'
      )
    } finally {
      setScraping(false)
    }
  }

  const handleContinueToOptions = () => {
    setStep(3)
  }

  const handleAddLink = () => {
    if (newLink.trim()) {
      setAdditionalLinks([...additionalLinks.filter(l => l), newLink])
      setNewLink('')
    }
  }

  const handleRemoveLink = (index) => {
    setAdditionalLinks(additionalLinks.filter((_, i) => i !== index))
  }

  const handleGenerateOptions = async () => {
    setLoading(true)
    setError(null)
    setStep(4) // Generating step

    try {
      const response = await resumes.generateOptions({
        job_url: jobUrl,
        use_profile_picture: useProfilePicture,
        additional_links: additionalLinks.filter(link => link.trim())
      })

      setResumeOptions(response.data.options || [])
      setStep(5) // Choose template step
    } catch (err) {
      console.error('Failed to generate resume options:', err)
      setError(
        err.response?.data?.detail || 'Failed to generate resume options. Please try again.'
      )
      setStep(3)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectOption = (option) => {
    setSelectedOption(option)
    setStep(6) // Done step
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
              Generate Resume
            </h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Progress Steps */}
        <div className="mb-12">
          <div className="flex items-center justify-center">
            {[1, 2, 3, 4, 5, 6].map((stepNum) => (
              <div key={stepNum} className="flex items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                    step >= stepNum
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-300 text-gray-600'
                  }`}
                >
                  {stepNum}
                </div>
                {stepNum < 6 && (
                  <div
                    className={`w-8 h-1 ${
                      step > stepNum ? 'bg-blue-600' : 'bg-gray-300'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-between mt-2 text-xs text-gray-600 max-w-3xl mx-auto">
            <span>Job URL</span>
            <span>Preview</span>
            <span>Customize</span>
            <span>Generating</span>
            <span>Choose</span>
            <span>Download</span>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Step 1: Job URL Input */}
        {step === 1 && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Enter Job Posting URL
            </h2>
            <p className="text-gray-600 mb-6">
              Paste the LinkedIn job URL you want to apply for. We'll scrape the job details and match them with your profile.
            </p>
            <form onSubmit={handleScrapeJob}>
              <input
                type="url"
                value={jobUrl}
                onChange={(e) => setJobUrl(e.target.value)}
                placeholder="https://www.linkedin.com/jobs/view/..."
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
                disabled={scraping}
              />
              <button
                type="submit"
                disabled={scraping}
                className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {scraping ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Scraping Job...</span>
                  </>
                ) : (
                  'Scrape Job Details'
                )}
              </button>
            </form>
          </div>
        )}

        {/* Step 2: Job Preview */}
        {step === 2 && scrapedJob && (
          <div>
            <div className="mb-6">
              <JobPreview job={scrapedJob} />
            </div>
            <div className="flex gap-4">
              <button
                onClick={() => {
                  setStep(1)
                  setScrapedJob(null)
                }}
                className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-3 px-6 rounded-lg transition duration-200"
              >
                Try Different Job
              </button>
              <button
                onClick={handleContinueToOptions}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition duration-200"
              >
                Continue
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Pre-generation Options */}
        {step === 3 && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Customize Your Resume
            </h2>
            <p className="text-gray-600 mb-6">
              Personalize your resume with additional information
            </p>

            {/* Profile Picture Option */}
            <div className="mb-6">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={useProfilePicture}
                  onChange={(e) => setUseProfilePicture(e.target.checked)}
                  className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                />
                <div>
                  <span className="font-medium text-gray-900">
                    Include LinkedIn Profile Picture
                  </span>
                  <p className="text-sm text-gray-600">
                    We'll use your LinkedIn profile photo in the resume header
                  </p>
                </div>
              </label>
            </div>

            {/* Additional Links */}
            <div className="mb-6">
              <label className="block font-medium text-gray-900 mb-2">
                Additional Links (Optional)
              </label>
              <p className="text-sm text-gray-600 mb-3">
                Add links to your GitHub, portfolio, personal website, etc.
              </p>

              {/* Display existing links */}
              {additionalLinks.filter(l => l).length > 0 && (
                <div className="mb-3 space-y-2">
                  {additionalLinks.filter(l => l).map((link, index) => (
                    <div key={index} className="flex items-center gap-2 bg-gray-50 p-2 rounded">
                      <span className="flex-1 text-sm text-gray-700">{link}</span>
                      <button
                        onClick={() => handleRemoveLink(index)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Add new link */}
              <div className="flex gap-2">
                <input
                  type="url"
                  value={newLink}
                  onChange={(e) => setNewLink(e.target.value)}
                  placeholder="https://github.com/username"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  onClick={handleAddLink}
                  className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium rounded-lg transition duration-200"
                >
                  Add
                </button>
              </div>
            </div>

            <div className="flex gap-4">
              <button
                onClick={() => setStep(2)}
                className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-3 px-6 rounded-lg transition duration-200"
              >
                Back
              </button>
              <button
                onClick={handleGenerateOptions}
                disabled={loading}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 disabled:opacity-50"
              >
                {loading ? 'Generating...' : 'Generate Resume Options'}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Generating */}
        {step === 4 && (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-6"></div>
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">
              Generating Your Resume Options...
            </h2>
            <p className="text-gray-600 mb-4">
              Our AI is analyzing the job posting and tailoring your resume. This may take 60-120 seconds.
            </p>
            <p className="text-sm text-gray-500">
              ⏳ Scraping job details...<br/>
              🤖 AI multi-agent processing...<br/>
              📄 Generating 2 resume options...<br/>
              ✨ Applying ATS optimizations...
            </p>
          </div>
        )}

        {/* Step 5: Choose Resume Option */}
        {step === 5 && resumeOptions.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Choose Your Resume
            </h2>
            <p className="text-gray-600 mb-6">
              We've generated {resumeOptions.length} tailored resume options for you. Select one to download.
            </p>

            <div className="space-y-4">
              {resumeOptions.map((option) => (
                <div
                  key={option.option_id}
                  className="border-2 border-gray-300 rounded-lg p-6 hover:border-blue-500 transition cursor-pointer"
                  onClick={() => handleSelectOption(option)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        Option {option.option_id}: {option.template_name}
                      </h3>
                      <span className="inline-block mt-1 text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                        {option.template_type}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-blue-600">{option.score}/100</div>
                      <div className="text-xs text-gray-500">Match Score</div>
                    </div>
                  </div>

                  <div className="text-sm text-gray-700 mb-4">
                    {option.justification}
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSelectOption(option);
                    }}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
                  >
                    Select This Option
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 6: Done - Download Resume */}
        {step === 6 && selectedOption && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
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
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Resume Ready!
              </h2>
              <p className="text-gray-600">
                Your ATS-optimized resume is ready to download
              </p>
            </div>

            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <p className="text-sm text-gray-600 mb-2">Selected Resume:</p>
              <p className="font-semibold text-gray-900 mb-1">
                {selectedOption.template_name}
              </p>
              <div className="flex items-center gap-3 text-sm">
                <span className="px-2 py-1 bg-gray-200 rounded">
                  {selectedOption.template_type}
                </span>
                <span className="text-blue-600 font-semibold">
                  {selectedOption.score}/100 Match
                </span>
              </div>
            </div>

            <div className="flex gap-4 mb-4">
              <button
                onClick={() => {
                  window.open(selectedOption.pdf_preview_url, '_blank')
                }}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition duration-200"
              >
                📄 Download PDF
              </button>
              <button
                onClick={() => {
                  if (selectedOption.docx_url) {
                    window.open(selectedOption.docx_url, '_blank')
                  }
                }}
                disabled={!selectedOption.docx_url}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                📝 Download DOCX
              </button>
            </div>

            <div className="flex gap-4">
              <button
                onClick={() => {
                  setStep(1);
                  setJobUrl('');
                  setScrapedJob(null);
                  setResumeOptions([]);
                  setSelectedOption(null);
                  setError(null);
                }}
                className="flex-1 text-gray-600 hover:text-gray-900 font-semibold py-3"
              >
                ← Generate Another Resume
              </button>
              <button
                onClick={() => navigate('/history')}
                className="flex-1 text-blue-600 hover:text-blue-700 font-semibold py-3"
              >
                View All Resumes →
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default GenerateResume
