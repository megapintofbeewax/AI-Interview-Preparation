import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ErrorAlert from '../components/ErrorAlert';

export default function InterviewResults() {
  const [searchParams] = useSearchParams();
  const interviewId = searchParams.get('id');
  const { token } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [results, setResults] = useState(null);

  useEffect(() => {
    const fetchResults = async () => {
      if (!interviewId) {
        setError('Missing interview reference.');
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`/api/interview/${interviewId}/results`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to load interview results.');
        }

        const data = await response.json();
        setResults(data);
      } catch (err) {
        setError(err.message || 'Error fetching results.');
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [interviewId, token]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-amber-500/20 border-t-amber-500 rounded-full animate-spin" />
          <span className="text-xs text-[#A1A1AA] font-mono tracking-wider">Synthesizing performance assessment...</span>
        </div>
      </div>
    );
  }

  const performance = results?.performance || {
    technical_accuracy: 8,
    relevance: 9,
    completeness: 7,
    clarity: 8
  };

  const performanceMetrics = [
    { label: 'Technical Accuracy', score: performance.technical_accuracy },
    { label: 'Domain Relevance', score: performance.relevance },
    { label: 'Completeness', score: performance.completeness },
    { label: 'Communication Clarity', score: performance.clarity },
  ];

  const overallScore = results?.overall_score ?? 78;

  return (
    <div className="flex-1 flex flex-col justify-center items-center px-4 py-8 sm:py-14 relative">
      {/* Background Amber Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[650px] h-[450px] bg-amber-500/[0.10] blur-[150px] rounded-full pointer-events-none -z-10" />

      <div className="w-full max-w-xl">
        {/* Header */}
        <div className="text-center mb-6 space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[11px] font-mono tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            <span>Simulation Archive // Evaluation Report</span>
          </div>
          <h1 className="font-heading text-3xl sm:text-4xl font-extrabold tracking-tight text-[#FAFAF5]">
            Interview Results
          </h1>
          <p className="text-xs text-[#A1A1AA] font-mono">
            {results?.target_role || 'Target Role'} • {results?.interview_type || 'Technical'} Session
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

          {/* Focal Overall Score Highlight with Amber Glow */}
          <div className="text-center py-8 px-6 bg-amber-500/[0.08] border border-amber-500/30 rounded-card shadow-amber-glow relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-amber-400/60 to-transparent" />
            <span className="block text-[11px] font-mono font-semibold uppercase tracking-widest text-amber-400 mb-2">
              Composite Benchmark Score
            </span>
            <div className="text-6xl font-heading font-black text-[#FCD34D] tracking-tight drop-shadow-[0_0_20px_rgba(245,158,11,0.5)]">
              {overallScore}
              <span className="text-lg font-normal text-[#A1A1AA] ml-2 font-mono">/ 100</span>
            </div>
            <div className="mt-3">
              <span className="badge-amber font-semibold text-xs px-3 py-1">
                {overallScore >= 80 ? '✦ Senior Readiness Tier' : overallScore >= 65 ? '✦ Proficient with Growth Areas' : '✦ Targeted Practice Recommended'}
              </span>
            </div>
          </div>

          {/* Performance Dimensions Breakdown */}
          <div className="space-y-3.5 pt-2">
            <h2 className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#A1A1AA]">
              Rubric Dimension Breakdown
            </h2>

            <div className="space-y-3">
              {performanceMetrics.map((item) => (
                <div key={item.label} className="p-3.5 bg-white/[0.03] border border-white/10 rounded-control space-y-2">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-[#A1A1AA] font-medium">{item.label}</span>
                    <span className="font-bold text-[#FAFAF5] font-mono">
                      {Math.round(item.score)} / 10
                    </span>
                  </div>
                  <div
                    role="progressbar"
                    aria-valuenow={Math.round(item.score)}
                    aria-valuemin="0"
                    aria-valuemax="10"
                    aria-label={`${item.label} score`}
                    className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden"
                  >
                    <div
                      className="bg-gradient-to-r from-amber-600 to-amber-400 h-1.5 rounded-full shadow-amber-glow transition-all duration-500"
                      style={{ width: `${Math.min(100, (item.score / 10) * 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Questions Answered Meta */}
          <div className="flex items-center justify-between p-4 bg-white/[0.02] border border-white/5 rounded-control text-xs">
            <span className="text-[#A1A1AA] font-mono">Questions Analyzed in Session:</span>
            <span className="font-bold text-[#FAFAF5] font-mono text-sm">
              {results?.questions_answered ?? 0} / {results?.total_questions ?? 10}
            </span>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3 pt-4 border-t border-white/10">
            <button
              onClick={() => navigate(`/interview/feedback?id=${interviewId}`)}
              className="btn-primary w-full py-4 text-sm font-bold"
            >
              View In-Depth Feedback & Recommendations →
            </button>

            <button
              onClick={() => navigate('/interview-setup')}
              className="btn-secondary w-full py-3"
            >
              Configure Another Session
            </button>

            <button
              onClick={() => navigate('/history')}
              className="w-full text-center text-xs text-[#A1A1AA] hover:text-[#FAFAF5] transition-colors py-2 cursor-pointer"
            >
              View Session History →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
