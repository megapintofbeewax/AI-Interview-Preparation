import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ErrorAlert from '../components/ErrorAlert';

export default function InterviewHistory() {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [historyData, setHistoryData] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch('/api/interview/history', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to load interview history.');
        }

        const data = await response.json();
        setHistoryData(data);
      } catch (err) {
        setError(err.message || 'Error fetching history.');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [token]);

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Recent';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-amber-500/20 border-t-amber-500 rounded-full animate-spin" />
          <span className="text-xs text-[#A1A1AA] font-mono tracking-wider">Accessing interview archives...</span>
        </div>
      </div>
    );
  }

  const interviews = historyData?.interviews || [];

  return (
    <div className="flex-1 flex flex-col justify-center items-center px-4 py-8 sm:py-14 relative">
      {/* Background Amber Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[650px] h-[450px] bg-amber-500/[0.08] blur-[150px] rounded-full pointer-events-none -z-10" />

      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-6 space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[11px] font-mono tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            <span>Simulation Archive // Candidate Ledger</span>
          </div>
          <h1 className="font-heading text-3xl sm:text-4xl font-extrabold tracking-tight text-[#FAFAF5]">
            Interview History
          </h1>
          <p className="text-xs text-[#A1A1AA] max-w-md mx-auto">
            Review past simulation sessions, evaluation trajectories, and detailed feedback reports
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

          {/* Empty State */}
          {interviews.length === 0 ? (
            <div className="glass-panel-subtle p-8 text-center space-y-4 rounded-card border border-white/10">
              <div className="w-12 h-12 mx-auto rounded-full bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-400 text-xl shadow-amber-glow-sm">
                ⏱
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-[#FAFAF5]">
                  No Simulation Sessions Recorded
                </h3>
                <p className="text-xs text-[#A1A1AA] max-w-xs mx-auto leading-relaxed">
                  Completed interviews will be archived here with overall scores, rubric dimension breakdowns, and actionable debriefs.
                </p>
              </div>
              <div className="pt-2">
                <button
                  onClick={() => navigate('/interview-setup')}
                  className="btn-primary text-xs"
                >
                  Start Your First Interview →
                </button>
              </div>
            </div>
          ) : (
            /* Interview List: Glass Cards with Hover Lift */
            <div className="space-y-3.5">
              {interviews.map((item) => (
                <div
                  key={item.id}
                  className="glass-card p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 border border-white/10 hover:border-amber-500/35 transition-all shadow-md group"
                >
                  {/* Session Details */}
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2.5">
                      <h2 className="text-sm sm:text-base font-semibold text-[#FAFAF5] group-hover:text-[#FCD34D] transition-colors">
                        {item.target_role}
                      </h2>
                      <span className="badge-dark text-[10px] font-mono">
                        {item.difficulty}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 text-xs text-[#A1A1AA] font-mono">
                      <span>{item.interview_type}</span>
                      <span>•</span>
                      <span>{formatDate(item.created_at)}</span>
                    </div>
                  </div>

                  {/* Score & Review Action */}
                  <div className="flex items-center justify-between sm:justify-end space-x-4 pt-2 sm:pt-0 border-t sm:border-t-0 border-white/10">
                    <div className="text-right">
                      {item.overall_score !== null ? (
                        <span className="badge-amber font-mono font-bold text-xs shadow-amber-glow-sm">
                          {item.overall_score} / 100
                        </span>
                      ) : (
                        <span className="text-xs font-mono text-[#71717A] bg-white/[0.04] px-2.5 py-1 rounded-full">
                          In Progress
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => navigate(`/interview/results?id=${item.id}`)}
                      className="btn-secondary text-xs py-2 px-3.5 whitespace-nowrap"
                    >
                      View Report →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Action Footer */}
          {interviews.length > 0 && (
            <div className="pt-4 border-t border-white/10 space-y-3">
              <button
                onClick={() => navigate('/interview-setup')}
                className="btn-primary w-full py-4 text-sm font-bold"
              >
                Start New Interview Session →
              </button>

              <button
                onClick={() => navigate('/profile')}
                className="w-full py-2 text-xs font-medium text-[#71717A] hover:text-[#FAFAF5] transition-colors text-center cursor-pointer"
              >
                Back to Profile
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
