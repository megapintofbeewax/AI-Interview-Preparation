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

export default function InterviewSetup() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [selectedRoleOption, setSelectedRoleOption] = useState('Software Developer');
  const [customRole, setCustomRole] = useState('');
  const [interviewType, setInterviewType] = useState('Technical');
  const [difficulty, setDifficulty] = useState('Medium');
  const [numQuestions, setNumQuestions] = useState(10);
  const [availableRoles, setAvailableRoles] = useState(DEFAULT_ROLES);

  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const initSetup = async () => {
      let currentRoles = DEFAULT_ROLES;

      try {
        const rolesRes = await fetch('/api/interview/roles');
        if (rolesRes.ok) {
          const rolesData = await rolesRes.json();
          if (rolesData.roles?.length) {
            currentRoles = rolesData.roles;
            setAvailableRoles(rolesData.roles);
          }
        }

        const profileRes = await fetch('/api/profile', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (profileRes.ok) {
          const profileData = await profileRes.json();
          const profileRole = (profileData.target_role || '').trim();
          if (profileRole) {
            if (currentRoles.includes(profileRole)) {
              setSelectedRoleOption(profileRole);
              setCustomRole('');
            } else {
              setSelectedRoleOption('Other');
              setCustomRole(profileRole);
            }
          }
        }
      } catch (err) {
        console.error('Error initializing setup:', err);
      } finally {
        setLoading(false);
      }
    };

    initSetup();
  }, [token]);

  const handleStartInterview = async (e) => {
    e.preventDefault();
    setError('');

    const effectiveRole = selectedRoleOption === 'Other' ? customRole.trim() : selectedRoleOption.trim();

    if (!effectiveRole) {
      setError('Please specify a target engineering role.');
      return;
    }

    setStarting(true);
    try {
      const response = await fetch('/api/interview/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          target_role: effectiveRole,
          interview_type: interviewType,
          difficulty: difficulty,
          num_questions: parseInt(numQuestions, 10) || 10
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Unable to start interview session.');
      }

      navigate(`/interview?id=${data.id}`);
    } catch (err) {
      setError(err.message || 'Error configuring interview.');
      setStarting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-amber-500/20 border-t-amber-500 rounded-full animate-spin" />
          <span className="text-xs text-[#A1A1AA] font-mono tracking-wider">Initializing simulation parameters...</span>
        </div>
      </div>
    );
  }

  const interviewTypes = ['Technical', 'HR / Behavioral', 'Mixed'];
  const difficultyLevels = ['Easy', 'Medium', 'Hard'];
  const questionCounts = [5, 10, 15];

  return (
    <div className="flex-1 flex flex-col justify-center items-center px-4 py-10 sm:py-16 relative">
      {/* Background Amber Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-amber-500/[0.08] blur-[140px] rounded-full pointer-events-none -z-10" />

      <div className="w-full max-w-xl">
        {/* Header */}
        <div className="text-center mb-8 space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[11px] font-mono tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            <span>Simulation Parameters // Setup</span>
          </div>
          <h1 className="font-heading text-3xl sm:text-4xl font-extrabold tracking-tight text-[#FAFAF5]">
            Interview Setup
          </h1>
          <p className="text-xs text-[#A1A1AA] max-w-md mx-auto">
            Configure your target domain, technical depth, and session format for the neural interviewer
          </p>
        </div>

        {/* Main Glass Panel */}
        <div className="glass-panel p-7 sm:p-9 shadow-glass-panel border border-white/12 relative overflow-hidden">
          {/* Top illuminated edge */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-amber-500/50 to-transparent" />

          {error && (
            <div className="mb-6">
              <ErrorAlert
                message={error}
                onRetry={handleStartInterview}
                retryLabel="Retry"
              />
            </div>
          )}

          <form onSubmit={handleStartInterview} className="space-y-6">
            {/* Target Role Selector */}
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
                    htmlFor="customRoleSetupInput"
                    className="block text-[11px] font-mono uppercase tracking-wider text-amber-400 mb-1.5"
                  >
                    Specify Your Custom Role:
                  </label>
                  <input
                    id="customRoleSetupInput"
                    type="text"
                    value={customRole}
                    onChange={(e) => {
                      setCustomRole(e.target.value);
                      if (error) setError('');
                    }}
                    className="input-base border-amber-500/40 focus:border-amber-400 text-[#FAFAF5]"
                    placeholder="e.g. Cybersecurity Analyst, Game Developer, Embedded Systems"
                    disabled={starting}
                  />
                </div>
              )}
            </div>

            {/* Interview Type Selector Pills */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-[#A1A1AA] mb-2">
                Interview Format
              </label>
              <div className="grid grid-cols-3 gap-2.5">
                {interviewTypes.map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setInterviewType(type)}
                    className={`py-2.5 px-3 text-xs rounded-control transition-all duration-normal text-center cursor-pointer font-medium ${
                      interviewType === type
                        ? 'bg-amber-500/15 text-[#FCD34D] border border-amber-500/40 shadow-amber-glow-sm font-bold'
                        : 'bg-white/[0.04] text-[#A1A1AA] border border-white/10 hover:bg-white/[0.08] hover:text-[#FAFAF5]'
                    }`}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>

            {/* Difficulty Selector Pills */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-[#A1A1AA] mb-2">
                Difficulty Tier
              </label>
              <div className="grid grid-cols-3 gap-2.5">
                {difficultyLevels.map((diff) => (
                  <button
                    key={diff}
                    type="button"
                    onClick={() => setDifficulty(diff)}
                    className={`py-2.5 px-3 text-xs rounded-control transition-all duration-normal text-center cursor-pointer font-medium ${
                      difficulty === diff
                        ? 'bg-amber-500/15 text-[#FCD34D] border border-amber-500/40 shadow-amber-glow-sm font-bold'
                        : 'bg-white/[0.04] text-[#A1A1AA] border border-white/10 hover:bg-white/[0.08] hover:text-[#FAFAF5]'
                    }`}
                  >
                    {diff}
                  </button>
                ))}
              </div>
            </div>

            {/* Number of Questions Selector Pills */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-[#A1A1AA] mb-2">
                Session Question Depth
              </label>
              <div className="grid grid-cols-3 gap-2.5">
                {questionCounts.map((count) => (
                  <button
                    key={count}
                    type="button"
                    onClick={() => setNumQuestions(count)}
                    className={`py-2.5 px-3 text-xs rounded-control transition-all duration-normal text-center cursor-pointer font-medium ${
                      numQuestions === count
                        ? 'bg-amber-500/15 text-[#FCD34D] border border-amber-500/40 shadow-amber-glow-sm font-bold'
                        : 'bg-white/[0.04] text-[#A1A1AA] border border-white/10 hover:bg-white/[0.08] hover:text-[#FAFAF5]'
                    }`}
                  >
                    {count} Questions
                  </button>
                ))}
              </div>
            </div>

            {/* Start Button */}
            <div className="pt-3">
              <button
                type="submit"
                disabled={starting}
                className="btn-primary w-full py-4 text-sm font-bold tracking-wide"
              >
                {starting ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-[#09090B] border-t-transparent rounded-full animate-spin" />
                    <span>Spinning up AI Interview Agent...</span>
                  </div>
                ) : (
                  'Launch AI Interview Session →'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
