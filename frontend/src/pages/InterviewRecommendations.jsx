import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ErrorAlert from '../components/ErrorAlert';

export default function InterviewRecommendations() {
  const [searchParams] = useSearchParams();
  const interviewId = searchParams.get('id');
  const { token } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [recData, setRecData] = useState(null);

  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!interviewId) {
        setError('Missing interview reference.');
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`/api/interview/${interviewId}/recommendations`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to load personalized recommendations.');
        }

        const data = await response.json();
        setRecData(data);
      } catch (err) {
        setError(err.message || 'Error fetching recommendations.');
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [interviewId, token]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-amber-500/20 border-t-amber-500 rounded-full animate-spin" />
          <span className="text-xs text-[#A1A1AA] font-mono tracking-wider">Generating adaptive roadmap...</span>
        </div>
      </div>
    );
  }

  const recommendations = recData?.recommendations || [
    {
      step_number: 1,
      title: 'Practice SQL JOIN questions',
      description: 'Focus on multi-table queries and aggregation performance.'
    },
    {
      step_number: 2,
      title: 'Revise database normalization',
      description: 'Review 1NF to 3NF schema design rules and consistency.'
    },
    {
      step_number: 3,
      title: 'Practice backend architecture questions',
      description: 'Review horizontal scaling and caching with Redis.'
    },
    {
      step_number: 4,
      title: 'Attempt medium-level technical interviews',
      description: 'Strengthen core implementation speed and accuracy.'
    }
  ];

  const suggestedSetup = recData?.suggested_setup;

  const handleStartRecommendedPractice = () => {
    navigate('/interview-setup');
  };

  return (
    <div className="flex-1 flex flex-col justify-center items-center px-4 py-8 sm:py-14 relative">
      {/* Background Amber Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[650px] h-[450px] bg-amber-500/[0.08] blur-[150px] rounded-full pointer-events-none -z-10" />

      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-6 space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[11px] font-mono tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            <span>Adaptive Roadmap // Targeted Practice</span>
          </div>
          <h1 className="font-heading text-3xl sm:text-4xl font-extrabold tracking-tight text-[#FAFAF5]">
            Recommended Practice
          </h1>
          <p className="text-xs text-[#A1A1AA] max-w-md mx-auto">
            Action items and tailored focus tracks based on your recent evaluation metrics
          </p>
        </div>

        {/* Main Glass Panel */}
        <div className="glass-panel p-7 sm:p-10 shadow-glass-panel border border-white/12 space-y-6 relative overflow-hidden">
          {/* Top illuminated edge */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-amber-500/50 to-transparent" />

          {error && (
            <ErrorAlert
              message={error}
              onRetry={() => window.location.reload()}
              retryLabel="Retry"
            />
          )}

          {/* Context Summary Banner */}
          {recData?.summary_message && (
            <div className="glass-panel-subtle p-5 border border-white/10 space-y-2">
              <span className="block text-[11px] font-mono font-semibold uppercase tracking-wider text-amber-400">
                Strategic Goal:
              </span>
              <p className="text-xs sm:text-sm text-[#FAFAF5] leading-relaxed">
                {recData.summary_message}
              </p>
            </div>
          )}

          {/* Actionable Numbered Steps */}
          <div className="space-y-4">
            <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-[#A1A1AA]">
              Prioritized Action Steps
            </h2>

            <div className="space-y-3">
              {recommendations.map((item) => (
                <div
                  key={item.step_number}
                  className="flex items-start space-x-4 p-4 rounded-control bg-white/[0.03] border border-white/10 hover:border-amber-500/30 transition-all shadow-sm"
                >
                  <div className="shrink-0 w-7 h-7 rounded-full bg-gradient-to-r from-amber-500 to-amber-600 text-[#09090B] flex items-center justify-center text-xs font-black mt-0.5 shadow-amber-glow-sm">
                    {item.step_number}
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-sm font-semibold text-[#FAFAF5]">
                      {item.title}
                    </h3>
                    <p className="text-xs text-[#A1A1AA] leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recommended Next Practice Session Setup */}
          {suggestedSetup && (
            <div className="p-5 bg-amber-500/10 border border-amber-500/30 rounded-card space-y-3 shadow-amber-glow-sm">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-amber-400">
                  Recommended Next Session Configuration
                </span>
              </div>
              <p className="text-sm font-semibold text-[#FAFAF5]">
                {suggestedSetup.target_role} • <span className="text-amber-400">{suggestedSetup.interview_type}</span> ({suggestedSetup.difficulty})
              </p>
              {suggestedSetup.focus_topics?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {suggestedSetup.focus_topics.map((topic, idx) => (
                    <span
                      key={idx}
                      className="badge-amber text-xs"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="pt-4 border-t border-white/10 space-y-3">
            <button
              onClick={handleStartRecommendedPractice}
              className="btn-primary w-full py-4 text-sm font-bold"
            >
              Practice Recommended Topics →
            </button>

            <button
              onClick={() => navigate('/history')}
              className="btn-secondary w-full py-3"
            >
              View Session History
            </button>

            <button
              onClick={() => navigate(`/interview/feedback?id=${interviewId}`)}
              className="w-full py-2 text-xs font-medium text-[#71717A] hover:text-[#FAFAF5] transition-colors text-center cursor-pointer"
            >
              Back to Feedback
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
