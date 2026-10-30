import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ErrorAlert from '../components/ErrorAlert';

export default function AnswerVerification() {
  const [searchParams] = useSearchParams();
  const interviewId = searchParams.get('id');
  const answerId = searchParams.get('answerId');
  const { token } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const [questionText, setQuestionText] = useState('');
  const [transcript, setTranscript] = useState('');
  const [duration, setDuration] = useState(0);

  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState('');

  useEffect(() => {
    const fetchAnswer = async () => {
      if (!interviewId || !answerId) {
        setError('Missing interview or answer reference.');
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`/api/interview/${interviewId}/answer/${answerId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
          throw new Error('Unable to retrieve transcribed answer.');
        }

        const data = await response.json();
        setQuestionText(data.question_text || '');
        setTranscript(data.transcript || '');
        setEditText(data.transcript || '');
        setDuration(data.duration_seconds || 0);
        if (!data.transcript) {
          setIsEditing(true);
        }
      } catch (err) {
        setError(err.message || 'Error loading answer.');
      } finally {
        setLoading(false);
      }
    };

    fetchAnswer();
  }, [interviewId, answerId, token]);

  const handleSaveEdit = async (e) => {
    if (e) e.preventDefault();
    if (!editText.trim()) {
      setError('Answer cannot be empty.');
      return;
    }

    setSaving(true);
    setError('');
    setSuccessMsg('');

    try {
      const response = await fetch(`/api/interview/${interviewId}/answer/${answerId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ transcript: editText.trim() })
      });

      if (!response.ok) {
        throw new Error('Failed to update answer.');
      }

      const updated = await response.json();
      setTranscript(updated.transcript);
      setIsEditing(false);
      setSuccessMsg('Transcript updated successfully.');
    } catch (err) {
      setError(err.message || 'Error updating transcript.');
    } finally {
      setSaving(false);
    }
  };

  const handleEvaluate = async () => {
    if (isEditing) {
      if (!editText.trim()) {
        setError('Answer cannot be empty.');
        return;
      }
      try {
        setEvaluating(true);
        const response = await fetch(`/api/interview/${interviewId}/answer/${answerId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ transcript: editText.trim() })
        });
        if (!response.ok) throw new Error('Failed to save answer prior to evaluation.');
      } catch (err) {
        setError(err.message || 'Error saving answer.');
        setEvaluating(false);
        return;
      }
    } else {
      setEvaluating(true);
    }

    navigate(`/interview/evaluation?id=${interviewId}&answerId=${answerId}`);
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-amber-500/20 border-t-amber-500 rounded-full animate-spin" />
          <span className="text-xs text-[#A1A1AA] font-mono tracking-wider">Retrieving transcribed payload...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col justify-center items-center px-4 py-8 sm:py-14 relative">
      {/* Ambient Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[550px] h-[380px] bg-amber-500/[0.08] blur-[140px] rounded-full pointer-events-none -z-10" />

      <div className="w-full max-w-xl">
        {/* Header */}
        <div className="text-center mb-6 space-y-2">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[11px] font-mono tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            <span>Speech Recognition // Verification</span>
          </div>
          <h1 className="font-heading text-3xl font-extrabold tracking-tight text-[#FAFAF5]">
            Review Transcript
          </h1>
          <p className="text-xs text-[#A1A1AA] max-w-md mx-auto">
            Verify or refine your transcribed answer before submitting it to the neural evaluation engine
          </p>
        </div>

        {/* Glass Card */}
        <div className="glass-panel p-7 sm:p-9 shadow-glass-panel border border-white/12 space-y-6 relative overflow-hidden">
          {/* Top illuminated edge */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-amber-500/50 to-transparent" />

          {error && (
            <ErrorAlert
              message={error}
              onRetry={() => setError('')}
              retryLabel="Dismiss"
            />
          )}

          {successMsg && (
            <div className="p-3.5 rounded-control bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs font-medium flex items-center space-x-2 shadow-amber-glow-sm">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse inline-block" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Question Reference Box */}
          {questionText && (
            <div className="p-4 bg-white/[0.03] border border-white/10 rounded-control">
              <span className="block text-[10px] font-mono font-semibold uppercase tracking-widest text-amber-400 mb-1.5">
                Interview Question:
              </span>
              <p className="text-xs text-[#FAFAF5] italic leading-relaxed">
                "{questionText}"
              </p>
            </div>
          )}

          {/* Transcript Box */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] uppercase font-mono tracking-wider text-[#A1A1AA]">
                Transcribed Response {duration > 0 && `(${duration}s)`}
              </span>
              {!isEditing ? (
                <button
                  type="button"
                  onClick={() => setIsEditing(true)}
                  className="btn-secondary text-xs px-3 py-1"
                >
                  Edit Text
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => {
                    setEditText(transcript);
                    setIsEditing(false);
                  }}
                  className="text-xs text-[#A1A1AA] hover:text-[#FAFAF5] px-2 py-1 transition-colors"
                >
                  Cancel
                </button>
              )}
            </div>

            {!isEditing ? (
              /* Display Box */
              <div className="p-5 bg-[#111113]/90 border border-white/10 rounded-control min-h-[100px] shadow-lg">
                <blockquote className="text-xs sm:text-sm text-[#FAFAF5] leading-relaxed font-normal">
                  "{transcript}"
                </blockquote>
              </div>
            ) : (
              /* Edit Textarea */
              <div className="space-y-3">
                <textarea
                  rows={4}
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  className="input-base leading-relaxed text-[#FAFAF5]"
                  placeholder="Enter or correct your answer..."
                  disabled={saving}
                />
                <button
                  type="button"
                  onClick={handleSaveEdit}
                  disabled={saving}
                  className="btn-primary text-xs px-4 py-2"
                >
                  {saving ? 'Saving...' : 'Save Correction'}
                </button>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="pt-4 border-t border-white/10 space-y-3">
            <button
              onClick={handleEvaluate}
              disabled={evaluating}
              className="btn-primary w-full py-3.5"
            >
              {evaluating ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-[#09090B] border-t-transparent rounded-full animate-spin" />
                  <span>Evaluating Competencies...</span>
                </div>
              ) : (
                <span>Submit to AI Evaluation →</span>
              )}
            </button>

            <button
              type="button"
              onClick={() => navigate(`/interview?id=${interviewId}`)}
              className="btn-secondary w-full py-3"
            >
              Re-record Voice Answer
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
