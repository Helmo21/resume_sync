import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth.jsx'
import { profile } from '../services/api'

function Profile() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [profileData, setProfileData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })

  // Form state
  const [formData, setFormData] = useState({
    headline: '',
    summary: '',
    email: '',
    phone: '',
    location: '',
    profile_url: '',
    experiences: [],
    education: [],
    skills: []
  })

  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    try {
      const response = await profile.getMyProfile()
      setProfileData(response.data)

      // Initialize form with existing data
      setFormData({
        headline: response.data.headline || '',
        summary: response.data.summary || '',
        email: user?.email || '',
        phone: '',
        location: '',
        profile_url: '',
        experiences: response.data.experiences || [],
        education: response.data.education || [],
        skills: response.data.skills || []
      })
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

  const handleSave = async () => {
    setSaving(true)
    try {
      await profile.updateProfile(formData)
      showMessage('success', 'Profile updated successfully!')
      await fetchProfile()
    } catch (error) {
      console.error('Failed to update profile:', error)
      showMessage('error', 'Failed to update profile')
    } finally {
      setSaving(false)
    }
  }

  const handleSyncProfile = async () => {
    // Ask for LinkedIn profile URL if not already set
    let linkedinUrl = formData.profile_url

    if (!linkedinUrl) {
      linkedinUrl = prompt('Please enter your LinkedIn profile URL:\n(e.g., https://www.linkedin.com/in/yourname)')

      if (!linkedinUrl) {
        showMessage('error', 'LinkedIn profile URL is required')
        return
      }

      // Basic validation
      if (!linkedinUrl.includes('linkedin.com/in/')) {
        showMessage('error', 'Please enter a valid LinkedIn profile URL')
        return
      }
    }

    setSyncing(true)
    showMessage('info', 'Starting profile sync from LinkedIn... This may take up to 3 minutes.')
    try {
      await profile.syncWithApify({ profile_url: linkedinUrl })
      showMessage('success', 'Profile synced successfully from LinkedIn!')
      await fetchProfile()
    } catch (error) {
      console.error('Failed to sync profile:', error)
      showMessage('error', error.response?.data?.detail || 'Failed to sync profile. Please try again.')
    } finally {
      setSyncing(false)
    }
  }

  const addExperience = () => {
    setFormData({
      ...formData,
      experiences: [
        ...formData.experiences,
        { title: '', company: '', start_date: '', end_date: '', description: '' }
      ]
    })
  }

  const updateExperience = (index, field, value) => {
    const updated = [...formData.experiences]
    updated[index][field] = value
    setFormData({ ...formData, experiences: updated })
  }

  const removeExperience = (index) => {
    const updated = formData.experiences.filter((_, i) => i !== index)
    setFormData({ ...formData, experiences: updated })
  }

  const addEducation = () => {
    setFormData({
      ...formData,
      education: [
        ...formData.education,
        { school: '', degree: '', field_of_study: '', graduation_year: '' }
      ]
    })
  }

  const updateEducation = (index, field, value) => {
    const updated = [...formData.education]
    updated[index][field] = value
    setFormData({ ...formData, education: updated })
  }

  const removeEducation = (index) => {
    const updated = formData.education.filter((_, i) => i !== index)
    setFormData({ ...formData, education: updated })
  }

  const addSkill = () => {
    const skillInput = prompt('Enter a skill:')
    if (skillInput && skillInput.trim()) {
      setFormData({
        ...formData,
        skills: [...formData.skills, skillInput.trim()]
      })
    }
  }

  const removeSkill = (index) => {
    const updated = formData.skills.filter((_, i) => i !== index)
    setFormData({ ...formData, skills: updated })
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

        {/* Sync Options */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Sync Your Profile from LinkedIn</h2>
          <p className="text-gray-600 mb-4">
            Automatically import your complete LinkedIn profile data including work experience, education, and skills.
          </p>
          <button
            onClick={handleSyncProfile}
            disabled={syncing}
            className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-4 rounded-lg font-medium transition-colors"
          >
            {syncing ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Syncing from LinkedIn... (This may take up to 3 minutes)
              </>
            ) : (
              <>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Sync from LinkedIn
              </>
            )}
          </button>
          <p className="text-sm text-gray-500 mt-3">
            We use advanced scraping technology with automatic retries to ensure reliable data import.
          </p>
        </div>

        {/* Manual Edit Form */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Or Edit Manually</h2>

          {/* Basic Info */}
          <div className="space-y-4 mb-8">
            <h3 className="text-lg font-medium text-gray-900">Basic Information</h3>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Professional Headline
              </label>
              <input
                type="text"
                value={formData.headline}
                onChange={(e) => setFormData({ ...formData, headline: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Senior Software Engineer"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Summary
              </label>
              <textarea
                value={formData.summary}
                onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Brief professional summary..."
              />
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="+1 (555) 123-4567"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Location
              </label>
              <input
                type="text"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., San Francisco, CA"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                LinkedIn Profile URL
              </label>
              <input
                type="url"
                value={formData.profile_url}
                onChange={(e) => setFormData({ ...formData, profile_url: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="https://www.linkedin.com/in/yourname"
              />
            </div>
          </div>

          {/* Work Experience */}
          <div className="space-y-4 mb-8">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium text-gray-900">Work Experience</h3>
              <button
                onClick={addExperience}
                className="text-blue-600 hover:text-blue-700 font-medium text-sm"
              >
                + Add Experience
              </button>
            </div>

            {formData.experiences.map((exp, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <h4 className="font-medium text-gray-900">Experience {index + 1}</h4>
                  <button
                    onClick={() => removeExperience(index)}
                    className="text-red-600 hover:text-red-700 text-sm"
                  >
                    Remove
                  </button>
                </div>
                <div className="space-y-3">
                  <input
                    type="text"
                    value={exp.title || ''}
                    onChange={(e) => updateExperience(index, 'title', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    placeholder="Job Title"
                  />
                  <input
                    type="text"
                    value={exp.company || ''}
                    onChange={(e) => updateExperience(index, 'company', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    placeholder="Company Name"
                  />
                  <div className="grid grid-cols-2 gap-3">
                    <input
                      type="text"
                      value={exp.start_date || ''}
                      onChange={(e) => updateExperience(index, 'start_date', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      placeholder="Start Date (MM/YYYY)"
                    />
                    <input
                      type="text"
                      value={exp.end_date || ''}
                      onChange={(e) => updateExperience(index, 'end_date', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      placeholder="End Date (MM/YYYY or Present)"
                    />
                  </div>
                  <textarea
                    value={exp.description || ''}
                    onChange={(e) => updateExperience(index, 'description', e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    placeholder="Description of your role and achievements..."
                  />
                </div>
              </div>
            ))}

            {formData.experiences.length === 0 && (
              <p className="text-gray-500 text-sm italic">
                No work experience added yet. Click "Add Experience" to get started.
              </p>
            )}
          </div>

          {/* Education */}
          <div className="space-y-4 mb-8">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium text-gray-900">Education</h3>
              <button
                onClick={addEducation}
                className="text-blue-600 hover:text-blue-700 font-medium text-sm"
              >
                + Add Education
              </button>
            </div>

            {formData.education.map((edu, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <h4 className="font-medium text-gray-900">Education {index + 1}</h4>
                  <button
                    onClick={() => removeEducation(index)}
                    className="text-red-600 hover:text-red-700 text-sm"
                  >
                    Remove
                  </button>
                </div>
                <div className="space-y-3">
                  <input
                    type="text"
                    value={edu.school || ''}
                    onChange={(e) => updateEducation(index, 'school', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    placeholder="School/University Name"
                  />
                  <input
                    type="text"
                    value={edu.degree || ''}
                    onChange={(e) => updateEducation(index, 'degree', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    placeholder="Degree (e.g., Bachelor of Science)"
                  />
                  <input
                    type="text"
                    value={edu.field_of_study || ''}
                    onChange={(e) => updateEducation(index, 'field_of_study', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    placeholder="Field of Study"
                  />
                  <input
                    type="text"
                    value={edu.graduation_year || ''}
                    onChange={(e) => updateEducation(index, 'graduation_year', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                    placeholder="Graduation Year"
                  />
                </div>
              </div>
            ))}

            {formData.education.length === 0 && (
              <p className="text-gray-500 text-sm italic">
                No education added yet. Click "Add Education" to get started.
              </p>
            )}
          </div>

          {/* Skills */}
          <div className="space-y-4 mb-8">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium text-gray-900">Skills</h3>
              <button
                onClick={addSkill}
                className="text-blue-600 hover:text-blue-700 font-medium text-sm"
              >
                + Add Skill
              </button>
            </div>

            <div className="flex flex-wrap gap-2">
              {formData.skills.map((skill, index) => (
                <span
                  key={index}
                  className="inline-flex items-center gap-2 px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm"
                >
                  {typeof skill === 'string' ? skill : skill.name}
                  <button
                    onClick={() => removeSkill(index)}
                    className="text-gray-500 hover:text-red-600"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>

            {formData.skills.length === 0 && (
              <p className="text-gray-500 text-sm italic">
                No skills added yet. Click "Add Skill" to get started.
              </p>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-4 pt-6 border-t border-gray-200">
            <button
              onClick={() => navigate('/dashboard')}
              className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}

export default Profile
