import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ErrorAlert from '../components/ErrorAlert';

export default function InterviewFeedback() {
  const [searchParams] = useSearchParams();
  const interviewId = searchParams.get('id');
  const { token } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [feedbackData, setFeedbackData] = useState(null);
  const [showDetailedQuestions, setShowDetailedQuestions] = useState(false);

  useEffect(() => {
    const fetchFeedback = async () => {
      if (!interviewId) {
        setError('Missing interview reference.');
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`/api/interview/${interviewId}/feedback`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to load interview feedback.');
        }

        const data = await response.json();
        setFeedbackData(data);
      } catch (err) {
        setError(err.message || 'Error fetching feedback.');
      } finally {
        setLoading(false);
      }
    };

    fetchFeedback();
  }, [interviewId, token]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-amber-500/20 border-t-amber-500 rounded-full animate-spin" />
          <span className="text-xs text-[#A1A1AA] font-mono tracking-wider">Analyzing strengths & improvement areas...</span>
        </div>
      </div>
    );
  }

  const strongAreas = feedbackData?.strong_areas || ['Python', 'Problem Solving'];
  const weakAreas = feedbackData?.weak_areas || ['Database Normalization', 'System Design'];
  const recurringWeaknesses = feedbackData?.recurring_weaknesses || [];
  const questionFeedbacks = feedbackData?.question_feedbacks || [];

  return (
    <div className="flex-1 flex flex-col justify-center items-center px-4 py-8 sm:py-14 relative">
      {/* Background Amber Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[650px] h-[450px] bg-amber-500/[0.08] blur-[150px] rounded-full pointer-events-none -z-10" />

      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-6 space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[11px] font-mono tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            <span>Performance Debrief // In-Depth Feedback</span>
          </div>
          <h1 className="font-heading text-3xl sm:text-4xl font-extrabold tracking-tight text-[#FAFAF5]">
            Interview Feedback
          </h1>
          <p className="text-xs text-[#A1A1AA] max-w-md mx-auto">
            Prioritized competencies, growth opportunities, and question-by-question observations
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

          {/* Overall Observations Box */}
          {feedbackData?.summary_notes && (
            <div className="glass-panel-subtle p-5 border border-white/10 space-y-2">
              <span className="block text-[11px] font-mono font-semibold uppercase tracking-wider text-amber-400">
                Summary Observations:
              </span>
              <p className="text-xs sm:text-sm text-[#FAFAF5] leading-relaxed">
                {feedbackData.summary_notes}
              </p>
            </div>
          )}

          {/* Demonstrated Strengths */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-[#A1A1AA]">
                Demonstrated Technical Strengths
              </h2>
              <span className="text-[10px] text-emerald-400 font-mono bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded-full">
                {strongAreas.length} Verified
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {strongAreas.map((area, idx) => (
                <div
                  key={idx}
                  className="flex items-center space-x-2.5 p-3 rounded-control bg-white/[0.03] border border-emerald-500/25 shadow-sm"
                >
                  <div className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs font-bold shrink-0">
                    ✓
                  </div>
                  <span className="text-xs sm:text-sm font-medium text-[#FAFAF5]">
                    {area}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Recommended Focus Areas */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-[#A1A1AA]">
                Recommended Focus Areas
              </h2>
              <span className="text-[10px] text-amber-400 font-mono bg-amber-500/10 border border-amber-500/30 px-2 py-0.5 rounded-full">
                {weakAreas.length} Focus Points
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {weakAreas.map((area, idx) => (
                <div
                  key={idx}
                  className="flex items-center space-x-2.5 p-3 rounded-control bg-white/[0.03] border border-amber-500/30 shadow-sm"
                >
                  <div className="w-5 h-5 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center text-xs font-bold shrink-0">
                    •
                  </div>
                  <span className="text-xs sm:text-sm text-[#FCD34D]">
                    {area}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Recurring Weaknesses Across Sessions */}
          {recurringWeaknesses.length > 0 && (
            <div className="p-5 bg-amber-500/10 border border-amber-500/30 rounded-card space-y-3 shadow-amber-glow-sm">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-amber-400">
                  Patterns Observed Across Prior Sessions
                </span>
              </div>
              <div className="space-y-2">
                {recurringWeaknesses.map((item, idx) => (
                  <div key={idx} className="text-xs text-amber-200 leading-relaxed bg-white/[0.03] p-3 rounded-control border border-amber-500/20">
                    <span className="font-bold text-amber-300">• {item.topic}:</span> {item.note}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Toggle for Question Breakdown */}
          {questionFeedbacks.length > 0 && (
            <div className="space-y-3 pt-2">
              <button
                type="button"
                onClick={() => setShowDetailedQuestions(!showDetailedQuestions)}
                className="w-full py-2.5 px-4 rounded-control border border-white/10 hover:border-amber-500/30 bg-white/[0.03] hover:bg-white/[0.06] text-xs font-medium text-[#FAFAF5] transition-all flex items-center justify-between cursor-pointer"
              >
                <span>{showDetailedQuestions ? 'Hide Question Breakdown' : 'Show Question Breakdown'}</span>
                <span className="text-amber-400 font-bold">{showDetailedQuestions ? '▲' : '▼'}</span>
              </button>

              {showDetailedQuestions && (
                <div className="space-y-3 pt-2 animate-fade-in-up">
                  {questionFeedbacks.map((item) => (
                    <div
                      key={item.question_index}
                      className="glass-panel-subtle p-4 border border-white/10 rounded-card space-y-2.5 text-left"
                    >
                      <div className="flex justify-between items-center text-xs">
                        <span className="font-semibold text-[#FAFAF5]">
                          Q{item.question_index}: {item.category}
                        </span>
                        <span className="badge-amber font-mono font-bold">
                          {item.overall_score.toFixed(1)} / 10
                        </span>
                      </div>
                      <p className="text-xs text-[#A1A1AA] italic">
                        "{item.question_text}"
                      </p>
                      <p className="text-xs text-[#FAFAF5] border-t border-white/5 pt-2 leading-relaxed">
                        {item.feedback}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="pt-4 border-t border-white/10 space-y-3">
            <button
              onClick={() => navigate(`/interview/recommendations?id=${interviewId}`)}
              className="btn-primary w-full py-4 text-sm font-bold"
            >
              View Practice Recommendations →
            </button>

            <button
              onClick={() => navigate(`/interview/results?id=${interviewId}`)}
              className="btn-secondary w-full py-3"
            >
              Back to Results
            </button>

            <button
              onClick={() => navigate('/interview-setup')}
              className="w-full py-2 text-xs font-medium text-[#71717A] hover:text-[#FAFAF5] transition-colors text-center cursor-pointer"
            >
              Practice Another Session
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
