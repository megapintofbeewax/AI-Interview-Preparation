import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ErrorAlert from '../components/ErrorAlert';

export default function AnswerEvaluation() {
  const [searchParams] = useSearchParams();
  const interviewId = searchParams.get('id');
  const answerId = searchParams.get('answerId');
  const { token } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [advancing, setAdvancing] = useState(false);
  const [error, setError] = useState('');
  const [evaluation, setEvaluation] = useState(null);

  useEffect(() => {
    const fetchEvaluation = async () => {
      if (!interviewId || !answerId) {
        setError('Missing interview or answer reference.');
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`/api/interview/${interviewId}/answer/${answerId}/evaluate`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to evaluate answer.');
        }

        const data = await response.json();
        setEvaluation(data);
      } catch (err) {
        setError(err.message || 'Error processing evaluation.');
      } finally {
        setLoading(false);
      }
    };

    fetchEvaluation();
  }, [interviewId, answerId, token]);

  const handleNextStep = async () => {
    setAdvancing(true);
    try {
      const response = await fetch(`/api/interview/${interviewId}/advance-question`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to advance interview session.');
      }

      const data = await response.json();

      if (data.completed) {
        navigate(`/interview/results?id=${interviewId}`);
      } else {
        navigate(`/interview?id=${interviewId}`);
      }
    } catch (err) {
      console.error('Error advancing to next question:', err);
      navigate(`/interview?id=${interviewId}`);
    } finally {
      setAdvancing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-amber-500/20 border-t-amber-500 rounded-full animate-spin" />
          <span className="text-xs text-[#A1A1AA] font-mono tracking-wider">Evaluating response across rubric dimensions...</span>
        </div>
      </div>
    );
  }

  const isLastQuestion = evaluation && evaluation.question_index >= evaluation.total_questions;

  const metrics = [
    { label: 'Technical Accuracy', score: evaluation?.technical_accuracy_score || 8 },
    { label: 'Domain Relevance', score: evaluation?.relevance_score || 8 },
    { label: 'Completeness', score: evaluation?.completeness_score || 7 },
    { label: 'Communication Clarity', score: evaluation?.clarity_score || 8 },
  ];

  return (
    <div className="flex-1 flex flex-col justify-center items-center px-4 py-8 sm:py-14 relative">
      {/* Amber Light Core */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-amber-500/[0.08] blur-[140px] rounded-full pointer-events-none -z-10" />

      <div className="w-full max-w-xl">
        {/* Header */}
        <div className="text-center mb-6 space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[11px] font-mono tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            <span>AI Feedback // Scoring Rubric</span>
          </div>
          <h1 className="font-heading text-3xl font-extrabold tracking-tight text-[#FAFAF5]">
            Answer Evaluation
          </h1>
          <p className="text-xs text-[#A1A1AA] font-mono">
            Question {evaluation?.question_index || 1} of {evaluation?.total_questions || 10}
          </p>
        </div>

        {/* Main Glass Panel */}
        <div className="glass-panel p-7 sm:p-9 shadow-glass-panel border border-white/12 space-y-6 relative overflow-hidden">
          {/* Top illuminated edge */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-amber-500/50 to-transparent" />

          {error && (
            <ErrorAlert
              message={error}
              onRetry={() => window.location.reload()}
              retryLabel="Try Again"
            />
          )}

          {/* Question Reminder Box */}
          {evaluation?.question_text && (
            <div className="p-4 bg-white/[0.03] border border-white/10 rounded-control">
              <span className="block text-[10px] font-mono uppercase tracking-widest text-amber-400 mb-1">
                Evaluated Question:
              </span>
              <p className="text-xs text-[#FAFAF5] italic leading-relaxed">
                "{evaluation.question_text}"
              </p>
            </div>
          )}

          {/* Overall Score Highlight */}
          <div className="p-5 bg-amber-500/10 border border-amber-500/30 rounded-card flex items-center justify-between shadow-amber-glow-sm">
            <div>
              <span className="text-[11px] uppercase font-mono tracking-wider font-semibold text-amber-400 block">
                Overall Response Score
              </span>
              <span className="text-xs text-[#A1A1AA]">Composite question evaluation</span>
            </div>
            <div className="text-right">
              <span className="text-3xl font-heading font-black text-[#FCD34D] drop-shadow-[0_0_12px_rgba(245,158,11,0.4)]">
                {evaluation?.overall_score?.toFixed(1) || '8.0'}
              </span>
              <span className="text-xs text-[#71717A] font-mono"> / 10</span>
            </div>
          </div>

          {/* Detailed Metric Bars */}
          <div className="space-y-3 pt-1">
            <h2 className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#A1A1AA]">
              Dimension Breakdown
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {metrics.map((m) => (
                <div key={m.label} className="p-3.5 bg-white/[0.03] border border-white/10 rounded-control space-y-2">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-[#A1A1AA] font-medium">{m.label}</span>
                    <span className="font-bold text-[#FAFAF5] font-mono">{m.score} / 10</span>
                  </div>
                  <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-amber-600 to-amber-400 rounded-full shadow-amber-glow transition-all duration-500"
                      style={{ width: `${(m.score / 10) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Feedback Box */}
          <div className="space-y-2 pt-1">
            <h2 className="text-[11px] font-mono font-semibold uppercase tracking-wider text-[#A1A1AA]">
              Actionable Observations
            </h2>
            <div className="p-4 bg-white/[0.03] border border-white/10 rounded-control">
              <p className="text-xs text-[#FAFAF5] leading-relaxed whitespace-pre-line font-normal">
                {evaluation?.feedback}
              </p>
            </div>
          </div>

          {/* Next Button */}
          <div className="pt-4 border-t border-white/10">
            <button
              onClick={handleNextStep}
              disabled={advancing}
              className="btn-primary w-full py-4 text-sm font-bold tracking-wide"
            >
              {advancing ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-[#09090B] border-t-transparent rounded-full animate-spin" />
                  <span>Advancing Simulation Session...</span>
                </div>
              ) : (
                <span>
                  {isLastQuestion ? 'Complete Session & View Report →' : 'Advance to Next Question →'}
                </span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
