import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ErrorAlert from '../components/ErrorAlert';

export default function ResumeAnalysis() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [saveSuccess, setSaveSuccess] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  // Extracted entities
  const [skills, setSkills] = useState([]);
  const [projects, setProjects] = useState([]);
  const [education, setEducation] = useState('');
  const [experience, setExperience] = useState('');
  const [certifications, setCertifications] = useState('');

  // Editable text representations
  const [editSkillsText, setEditSkillsText] = useState('');
  const [editProjectsText, setEditProjectsText] = useState('');
  const [editEducation, setEditEducation] = useState('');
  const [editExperience, setEditExperience] = useState('');
  const [editCertifications, setEditCertifications] = useState('');

  const fetchAnalysis = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/resume-analysis', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to load resume analysis.');
      }

      const data = await response.json();
      populateData(data);
    } catch (err) {
      setError(err.message || 'Error fetching resume analysis.');
    } finally {
      setLoading(false);
    }
  };

  const populateData = (data) => {
    setSkills(data.skills || []);
    setProjects(data.projects || []);
    setEducation(data.education || '');
    setExperience(data.experience || '');
    setCertifications(data.certifications || '');

    setEditSkillsText((data.skills || []).join(', '));
    setEditProjectsText((data.projects || []).join('\n'));
    setEditEducation(data.education || '');
    setEditExperience(data.experience || '');
    setEditCertifications(data.certifications || '');
  };

  useEffect(() => {
    fetchAnalysis();
  }, [token]);

  const handleSaveCorrections = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSaveSuccess('');

    const updatedSkills = editSkillsText
      .split(',')
      .map(s => s.trim())
      .filter(Boolean);

    const updatedProjects = editProjectsText
      .split('\n')
      .map(p => p.trim())
      .filter(Boolean);

    try {
      const response = await fetch('/api/resume-analysis', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          skills: updatedSkills,
          projects: updatedProjects,
          education: editEducation.trim(),
          experience: editExperience.trim(),
          certifications: editCertifications.trim()
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to save changes.');
      }

      const updated = await response.json();
      populateData(updated);
      setIsEditing(false);
      setSaveSuccess('Corrections saved successfully.');
    } catch (err) {
      setError(err.message || 'Error updating resume analysis.');
    } finally {
      setSaving(false);
    }
  };

  const handleReanalyze = async () => {
    setAnalyzing(true);
    setError('');
    setSaveSuccess('');
    try {
      const response = await fetch('/api/resume-analysis/analyze', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Analysis failed.');
      }
      const data = await response.json();
      populateData(data);
      setSaveSuccess('Resume re-analyzed successfully.');
    } catch (err) {
      setError(err.message || 'Error running NLP analysis.');
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-amber-500/20 border-t-amber-500 rounded-full animate-spin" />
          <span className="text-xs text-[#A1A1AA] font-mono tracking-wider">Parsing & classifying entities...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col justify-center items-center px-4 py-10 sm:py-16 relative">
      {/* Background Ambient Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-amber-500/[0.08] blur-[140px] rounded-full pointer-events-none -z-10" />

      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8 space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[11px] font-mono tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            <span>Parsed Resume Profile // Entity Extraction</span>
          </div>
          <h1 className="font-heading text-3xl sm:text-4xl font-extrabold tracking-tight text-[#FAFAF5]">
            Resume Analysis
          </h1>
          <p className="text-xs text-[#A1A1AA] max-w-md mx-auto">
            Extracted competencies, project highlights, and academic qualifications mapped for interview generation
          </p>
        </div>

        {/* Main Glass Panel */}
        <div className="glass-panel p-7 sm:p-9 shadow-glass-panel border border-white/12 space-y-6 relative overflow-hidden">
          {/* Top illuminated edge */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-amber-500/50 to-transparent" />

          {error && (
            <ErrorAlert
              message={error}
              onRetry={handleReanalyze}
              retryLabel="Re-analyze"
            />
          )}

          {saveSuccess && (
            <div className="p-3.5 rounded-control bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs font-medium flex items-center space-x-2 shadow-amber-glow-sm">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse inline-block" />
              <span>{saveSuccess}</span>
            </div>
          )}

          {/* Subheader Controls Bar */}
          <div className="flex items-center justify-between border-b border-white/10 pb-4">
            <div className="flex items-center space-x-2">
              <span className="text-[11px] uppercase font-mono tracking-wider text-[#A1A1AA]">Mode:</span>
              <span className="text-xs font-semibold text-[#FAFAF5]">
                {isEditing ? 'Interactive Entity Correction' : 'Extracted Entities Overview'}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              {!isEditing ? (
                <button
                  type="button"
                  onClick={() => setIsEditing(true)}
                  className="btn-secondary text-xs px-3 py-1"
                >
                  Edit / Correct
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="text-xs text-[#A1A1AA] hover:text-[#FAFAF5] px-2 py-1 transition-colors"
                >
                  Cancel
                </button>
              )}
              <button
                type="button"
                onClick={handleReanalyze}
                disabled={analyzing}
                className="text-xs text-amber-400 hover:text-amber-300 disabled:opacity-40 px-2.5 py-1 transition-colors border border-amber-500/20 rounded-lg hover:bg-amber-500/10"
              >
                {analyzing ? 'Re-analyzing...' : '↻ Re-analyze'}
              </button>
            </div>
          </div>

          {!isEditing ? (
            /* View Mode: Differentiated Layered Panels */
            <div className="space-y-6">
              {/* Technical Skills Panel */}
              <div className="glass-panel-subtle p-5 border border-white/10 space-y-3">
                <div className="flex items-center justify-between">
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-[#FAFAF5] flex items-center space-x-2">
                    <span className="w-2 h-2 rounded-full bg-amber-500 shadow-amber-glow-sm" />
                    <span>Technical Competencies</span>
                  </h2>
                  <span className="badge-amber text-[10px] font-mono">
                    {skills.length} Detected
                  </span>
                </div>
                {skills.length > 0 ? (
                  <div className="flex flex-wrap gap-2 pt-1">
                    {skills.map((skill, index) => (
                      <span
                        key={index}
                        className="badge-amber text-xs font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-[#71717A] italic">No skills identified in document</p>
                )}
              </div>

              {/* Projects Panel */}
              <div className="glass-panel-subtle p-5 border border-white/10 space-y-3">
                <h2 className="text-xs font-semibold uppercase tracking-wider text-[#FAFAF5] flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-amber-500 shadow-amber-glow-sm" />
                  <span>Featured Technical Projects</span>
                </h2>
                {projects.length > 0 ? (
                  <div className="space-y-2.5 pt-1">
                    {projects.map((proj, index) => (
                      <div
                        key={index}
                        className="text-xs text-[#FAFAF5] flex items-start space-x-2.5 leading-relaxed bg-white/[0.03] p-3 rounded-control border border-white/5"
                      >
                        <span className="text-amber-400 font-bold mt-0.5">•</span>
                        <span>{proj}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-[#71717A] italic">No projects identified</p>
                )}
              </div>

              {/* Grid: Education & Experience */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Education Panel */}
                <div className="glass-panel-subtle p-4 border border-white/10 space-y-1.5">
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-[#A1A1AA]">
                    Academic Background
                  </h2>
                  <p className="text-xs font-semibold text-[#FAFAF5]">
                    {education || 'Not specified'}
                  </p>
                </div>

                {/* Experience Panel */}
                <div className="glass-panel-subtle p-4 border border-white/10 space-y-1.5">
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-[#A1A1AA]">
                    Industry Experience
                  </h2>
                  <p className="text-xs text-[#FAFAF5] whitespace-pre-line leading-relaxed">
                    {experience || 'Not specified'}
                  </p>
                </div>
              </div>

              {/* Certifications (if present) */}
              {certifications && certifications !== 'None listed' && (
                <div className="glass-panel-subtle p-4 border border-white/10 space-y-1.5">
                  <h2 className="text-xs font-semibold uppercase tracking-wider text-[#A1A1AA]">
                    Verified Certifications
                  </h2>
                  <p className="text-xs text-[#FAFAF5]">
                    {certifications}
                  </p>
                </div>
              )}
            </div>
          ) : (
            /* Edit Mode: Clean Dark Form */
            <form onSubmit={handleSaveCorrections} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#A1A1AA] mb-1.5">
                  Skills (comma-separated)
                </label>
                <input
                  type="text"
                  value={editSkillsText}
                  onChange={(e) => setEditSkillsText(e.target.value)}
                  className="input-base"
                  placeholder="Python, React, FastAPI, SQL"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#A1A1AA] mb-1.5">
                  Projects (one per line)
                </label>
                <textarea
                  rows={3}
                  value={editProjectsText}
                  onChange={(e) => setEditProjectsText(e.target.value)}
                  className="input-base"
                  placeholder={"E-Commerce API\nNeural Chatbot"}
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#A1A1AA] mb-1.5">
                  Education
                </label>
                <input
                  type="text"
                  value={editEducation}
                  onChange={(e) => setEditEducation(e.target.value)}
                  className="input-base"
                  placeholder="B.Tech Computer Science"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#A1A1AA] mb-1.5">
                  Experience
                </label>
                <textarea
                  rows={2}
                  value={editExperience}
                  onChange={(e) => setEditExperience(e.target.value)}
                  className="input-base"
                  placeholder="Software Engineer Intern at Tech Corp"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-[#A1A1AA] mb-1.5">
                  Certifications
                </label>
                <input
                  type="text"
                  value={editCertifications}
                  onChange={(e) => setEditCertifications(e.target.value)}
                  className="input-base"
                  placeholder="AWS Solutions Architect"
                />
              </div>

              <div className="flex space-x-3 pt-3">
                <button
                  type="submit"
                  disabled={saving}
                  className="btn-primary flex-1 py-3"
                >
                  {saving ? 'Saving...' : 'Save Entity Corrections'}
                </button>
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}

          {/* Primary Action Button to Proceed */}
          <div className="pt-5 border-t border-white/10">
            <button
              onClick={() => navigate('/interview-setup')}
              className="btn-primary w-full py-3.5 flex items-center justify-center space-x-2"
            >
              <span>Proceed to Interview Setup</span>
              <span aria-hidden="true">→</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
