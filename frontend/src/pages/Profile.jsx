import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ErrorAlert from '../components/ErrorAlert';

const DEFAULT_ROLES = [
  'Software Developer',
  'Frontend Developer',
  'Backend Developer',
  'Full Stack Developer',
  'Data Analyst',
  'Data Scientist',
  'Machine Learning Engineer',
  'DevOps Engineer',
  'Cloud Engineer',
  'Mobile App Developer'
];

export default function Profile() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [education, setEducation] = useState('');
  const [selectedRoleOption, setSelectedRoleOption] = useState('Software Developer');
  const [customRole, setCustomRole] = useState('');
  const [skills, setSkills] = useState('');
  const [availableRoles, setAvailableRoles] = useState(DEFAULT_ROLES);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [hasSaved, setHasSaved] = useState(false);

  useEffect(() => {
    const fetchProfileAndRoles = async () => {
      let currentRoles = DEFAULT_ROLES;

      try {
        // Fetch standard roles catalog
        const rolesRes = await fetch('/api/interview/roles');
        if (rolesRes.ok) {
          const rolesData = await rolesRes.json();
          if (rolesData.roles?.length) {
            currentRoles = rolesData.roles;
            setAvailableRoles(rolesData.roles);
          }
        }

        // Fetch candidate profile
        const profileRes = await fetch('/api/profile', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (profileRes.ok) {
          const data = await profileRes.json();
          setName(data.name || '');
          setEmail(data.email || '');
          setEducation(data.education || '');
          setSkills(data.skills || '');

          const userRole = (data.target_role || '').trim();
          if (!userRole) {
            setSelectedRoleOption(currentRoles[0] || 'Software Developer');
            setCustomRole('');
          } else if (currentRoles.includes(userRole)) {
            setSelectedRoleOption(userRole);
            setCustomRole('');
          } else {
            setSelectedRoleOption('Other');
            setCustomRole(userRole);
          }

          if (data.education || data.target_role || data.skills) {
            setHasSaved(true);
          }
        } else {
          setError('Failed to load profile data.');
        }
      } catch (err) {
        setError('Network error while loading profile.');
      } finally {
        setLoading(false);
      }
    };

    fetchProfileAndRoles();
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!name.trim()) {
      setError('Name is required.');
      return;
    }

    const effectiveRole = selectedRoleOption === 'Other' ? customRole.trim() : selectedRoleOption.trim();
    if (selectedRoleOption === 'Other' && !effectiveRole) {
      setError('Please specify your custom target engineering role.');
      return;
    }
    if (!effectiveRole) {
      setError('Please select or enter your target engineering role.');
      return;
    }

    setSaving(true);
    try {
      const response = await fetch('/api/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: name.trim(),
          education: education.trim(),
          target_role: effectiveRole,
          skills: skills.trim()
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to save profile.');
      }

      setSuccess('Profile configuration saved successfully.');
      setHasSaved(true);
    } catch (err) {
      setError(err.message || 'Error saving profile.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-amber-500/20 border-t-amber-500 rounded-full animate-spin" />
          <span className="text-xs text-[#A1A1AA] font-mono tracking-wider">Loading candidate parameters...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col justify-center items-center px-4 py-10 sm:py-14 relative">
      {/* Background Ambient Glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[500px] h-[350px] bg-amber-500/[0.07] blur-[130px] rounded-full pointer-events-none -z-10" />

      <div className="w-full max-w-xl">
        {/* Header */}
        <div className="text-center mb-8 space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[11px] font-mono tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            <span>Profile Matrix // Configuration</span>
          </div>
          <h1 className="font-heading text-3xl font-extrabold tracking-tight text-[#FAFAF5]">
            Candidate Profile
          </h1>
          <p className="text-xs text-[#A1A1AA] max-w-md mx-auto">
            Configure your target domain, education, and technical competencies for adaptive AI questions
          </p>
        </div>

        {/* Maximalist Dark Glass Card */}
        <div className="glass-panel p-7 sm:p-9 shadow-glass-panel border border-white/12 relative overflow-hidden">
          {/* Top illuminated edge */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-amber-500/50 to-transparent" />

          {error && (
            <div className="mb-6">
              <ErrorAlert
                message={error}
                onRetry={() => setError('')}
                retryLabel="Dismiss"
              />
            </div>
          )}

          {success && (
            <div
              role="status"
              aria-live="polite"
              className="mb-6 p-4 rounded-control bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs font-medium flex items-center space-x-2.5 shadow-amber-glow-sm"
            >
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse inline-block" />
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="name"
                  className="block text-xs font-semibold uppercase tracking-wider text-[#A1A1AA] mb-2"
                >
                  Candidate Name
                </label>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    if (error) setError('');
                  }}
                  className="input-base"
                  placeholder="Alex Mercer"
                  disabled={saving}
                />
              </div>

              <div>
                <label
                  htmlFor="email"
                  className="block text-xs font-semibold uppercase tracking-wider text-[#A1A1AA] mb-2"
                >
                  Email (Immutable)
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  disabled
                  className="input-base bg-white/[0.03] text-[#71717A] border-white/5 cursor-not-allowed font-mono text-xs"
                  placeholder="candidate@domain.com"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="education"
                className="block text-xs font-semibold uppercase tracking-wider text-[#A1A1AA] mb-2"
              >
                Education / Degree
              </label>
              <input
                id="education"
                type="text"
                value={education}
                onChange={(e) => {
                  setEducation(e.target.value);
                  if (error) setError('');
                }}
                className="input-base"
                placeholder="B.Tech Computer Science, 2025"
                disabled={saving}
              />
            </div>

            {/* Target Engineering Role Dropdown with "Other" preference */}
            <div>
              <label
                htmlFor="targetRole"
                className="block text-xs font-semibold uppercase tracking-wider text-[#A1A1AA] mb-2"
              >
                Target Engineering Role
              </label>
              <div className="relative">
                <select
                  id="targetRole"
                  value={selectedRoleOption}
                  onChange={(e) => {
                    setSelectedRoleOption(e.target.value);
                    if (error) setError('');
                  }}
                  className="input-base pr-10 appearance-none cursor-pointer bg-[#111113]/90 text-[#FAFAF5] border-white/15"
                  disabled={saving}
                >
                  {availableRoles.map((role) => (
                    <option key={role} value={role} className="bg-[#18181B] text-[#FAFAF5]">
                      {role}
                    </option>
                  ))}
                  <option value="Other" className="bg-[#18181B] text-[#FCD34D] font-semibold">
                    Other (Enter custom preference)
                  </option>
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-amber-400 text-xs">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>

              {/* Custom Role Input field when "Other" is selected */}
              {selectedRoleOption === 'Other' && (
                <div className="mt-3 animate-fade-in-up">
                  <label
                    htmlFor="customRoleInput"
                    className="block text-[11px] font-mono uppercase tracking-wider text-amber-400 mb-1.5"
                  >
                    Specify Your Custom Role:
                  </label>
                  <input
                    id="customRoleInput"
                    type="text"
                    value={customRole}
                    onChange={(e) => {
                      setCustomRole(e.target.value);
                      if (error) setError('');
                    }}
                    className="input-base border-amber-500/40 focus:border-amber-400 text-[#FAFAF5]"
                    placeholder="e.g. Cybersecurity Analyst, Game Developer, Embedded Systems"
                    disabled={saving}
                  />
                </div>
              )}
            </div>

            <div>
              <label
                htmlFor="skills"
                className="block text-xs font-semibold uppercase tracking-wider text-[#A1A1AA] mb-2"
              >
                Core Skills (Comma Separated)
              </label>
              <input
                id="skills"
                type="text"
                value={skills}
                onChange={(e) => {
                  setSkills(e.target.value);
                  if (error) setError('');
                }}
                className="input-base"
                placeholder="Python, React, FastAPI, SQL, Docker, Machine Learning"
                disabled={saving}
              />
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={saving}
                className="btn-primary w-full py-3"
              >
                {saving ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-[#09090B] border-t-transparent rounded-full animate-spin" />
                    <span>Saving Parameters...</span>
                  </div>
                ) : (
                  'Save Profile Parameters'
                )}
              </button>
            </div>
          </form>

          {/* Action Step to Resume Upload */}
          <div className="mt-7 pt-6 border-t border-white/10">
            <button
              type="button"
              onClick={() => navigate('/resume-upload')}
              className="btn-secondary w-full py-3 flex items-center justify-center space-x-2"
            >
              <span>{hasSaved ? 'Proceed to Resume Upload' : 'Skip to Resume Upload'}</span>
              <span aria-hidden="true">→</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
