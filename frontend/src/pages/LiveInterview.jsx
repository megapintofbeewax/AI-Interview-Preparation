import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { playQuestionAudio, stopAudio } from '../utils/speech';
import ErrorAlert from '../components/ErrorAlert';

export default function LiveInterview() {
  const [searchParams] = useSearchParams();
  const interviewId = searchParams.get('id');
  const { token } = useAuth();
  const navigate = useNavigate();

  const [interview, setInterview] = useState(null);
  const [question, setQuestion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorConfig, setErrorConfig] = useState(null);

  // Speech-to-Text & Recording States
  const [isPlayingTTS, setIsPlayingTTS] = useState(false);
  const [isGeneratingTTS, setIsGeneratingTTS] = useState(false);
  const [ttsError, setTtsError] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [micPermissionDenied, setMicPermissionDenied] = useState(false);

  const mediaRecorderRef = useRef(null);
  const recognitionRef = useRef(null);
  const timerIntervalRef = useRef(null);
  const isRecordingRef = useRef(false);
  const liveTranscriptRef = useRef('');

  // 1. Fetch Interview Session and Question
  const fetchSessionAndQuestion = async () => {
    if (!interviewId) {
      setErrorConfig({
        message: 'No interview session provided.',
        retryLabel: 'Go to Setup',
        onRetry: () => navigate('/interview-setup')
      });
      setLoading(false);
      return;
    }

    setLoading(true);
    setErrorConfig(null);

    try {
      const sessRes = await fetch(`/api/interview/${interviewId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!sessRes.ok) {
        throw new Error(sessRes.status === 404 ? 'NotFound' : 'NetworkError');
      }
      const sessData = await sessRes.json();
      setInterview(sessData);

      const qRes = await fetch(`/api/interview/${interviewId}/current-question`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!qRes.ok) {
        if (qRes.status >= 500) {
          throw new Error('AIGenerationError');
        }
        throw new Error('NetworkError');
      }
      const qData = await qRes.json();
      setQuestion(qData);

      if (qData.id) {
        playInterviewerQuestion(qData.id);
      }
    } catch (err) {
      if (err.message === 'AIGenerationError') {
        setErrorConfig({
          message: 'Unable to generate a question. Please try again.',
          retryLabel: 'Try Again',
          onRetry: () => fetchSessionAndQuestion()
        });
      } else {
        setErrorConfig({
          message: 'Unable to connect to the server. Please try again.',
          retryLabel: 'Retry',
          onRetry: () => fetchSessionAndQuestion()
        });
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessionAndQuestion();

    return () => {
      stopAudio();
      isRecordingRef.current = false;
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) {}
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        try {
          mediaRecorderRef.current.stop();
          mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
        } catch (e) {}
      }
    };
  }, [interviewId, token]);

  // 2. Neural Text-to-Speech Interviewer Delivery
  const playInterviewerQuestion = async (qId) => {
    const questionId = qId || question?.id;
    if (!questionId || !interviewId) return;

    setTtsError(null);
    setIsGeneratingTTS(true);
    setIsPlayingTTS(false);

    try {
      await playQuestionAudio({
        interviewId,
        questionId,
        token,
        onLoading: () => {
          setIsGeneratingTTS(true);
          setIsPlayingTTS(false);
        },
        onStart: () => {
          setIsGeneratingTTS(false);
          setIsPlayingTTS(true);
        },
        onEnd: () => {
          setIsGeneratingTTS(false);
          setIsPlayingTTS(false);
        },
        onError: (err) => {
          console.warn('Interviewer speech playback error:', err);
          setIsGeneratingTTS(false);
          setIsPlayingTTS(false);
          setTtsError("We couldn't generate the interviewer's voice. Please try again.");
        }
      });
    } catch (err) {
      console.warn('Interviewer speech generation error:', err);
      setIsGeneratingTTS(false);
      setIsPlayingTTS(false);
      setTtsError("We couldn't generate the interviewer's voice. Please try again.");
    }
  };

  const handleStopTTS = () => {
    stopAudio();
    setIsPlayingTTS(false);
    setIsGeneratingTTS(false);
  };

  // 3. Start Voice Answer
  const handleStartAnswer = async () => {
    setErrorConfig(null);
    setTranscript('');
    liveTranscriptRef.current = '';
    setRecordingSeconds(0);
    setMicPermissionDenied(false);

    stopAudio();
    setIsPlayingTTS(false);
    setIsGeneratingTTS(false);

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setErrorConfig({
        message: 'Speech recognition is not supported in this browser. Please use Google Chrome or Microsoft Edge, or enter your answer manually.',
        retryLabel: 'Enter Answer Manually',
        onRetry: () => handleEnterManually()
      });
      return;
    }

    // Quick mic permission check via getUserMedia without keeping stream open
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        // Immediately release tracks so SpeechRecognition has 100% exclusive access to the mic
        stream.getTracks().forEach((track) => track.stop());
      }
    } catch (err) {
      console.warn('Microphone permission check warning:', err);
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setMicPermissionDenied(true);
        setErrorConfig({
          message: 'Microphone access is required for voice interviews. Please allow microphone permissions in your browser address bar.',
          retryLabel: 'Allow & Try Again',
          onRetry: () => handleStartAnswer(),
          secondaryLabel: 'Enter Answer Manually',
          secondaryAction: () => handleEnterManually()
        });
        return;
      }
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      recognition.maxAlternatives = 1;

      recognition.onresult = (event) => {
        let fullText = '';
        for (let i = 0; i < event.results.length; i++) {
          fullText += event.results[i][0].transcript + ' ';
        }
        const cleaned = fullText.trim();
        if (cleaned) {
          liveTranscriptRef.current = cleaned;
          setTranscript(cleaned);
        }
      };

      recognition.onerror = (event) => {
        console.warn('Speech recognition status:', event.error);
        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
          setMicPermissionDenied(true);
          isRecordingRef.current = false;
          setIsRecording(false);
          if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
          setErrorConfig({
            message: 'Microphone access is required for voice interviews. Please allow microphone permissions in your browser.',
            retryLabel: 'Allow Microphone',
            onRetry: () => handleStartAnswer(),
            secondaryLabel: 'Enter Answer Manually',
            secondaryAction: () => handleEnterManually()
          });
        } else if (event.error === 'audio-capture') {
          setErrorConfig({
            message: 'No microphone was detected. Please check your audio input device.',
            retryLabel: 'Try Again',
            onRetry: () => handleStartAnswer(),
            secondaryLabel: 'Enter Answer Manually',
            secondaryAction: () => handleEnterManually()
          });
        }
        // 'no-speech' is normal during pauses; keep listening while candidate is speaking
      };

      recognition.onend = () => {
        // Automatically restart if user is still in recording mode
        if (isRecordingRef.current) {
          try {
            recognition.start();
          } catch (e) {
            // Already started or restarting
          }
        }
      };

      recognition.start();
      recognitionRef.current = recognition;

      isRecordingRef.current = true;
      setIsRecording(true);

      timerIntervalRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (e) {
      console.warn('Could not start speech recognition:', e);
      setErrorConfig({
        message: 'Could not access microphone for speech recognition. Please check your browser permissions.',
        retryLabel: 'Try Again',
        onRetry: () => handleStartAnswer(),
        secondaryLabel: 'Enter Answer Manually',
        secondaryAction: () => handleEnterManually()
      });
    }
  };

  // 4. Enter Answer Manually Fallback
  const handleEnterManually = async () => {
    isRecordingRef.current = false;
    setIsRecording(false);
    setIsProcessing(true);
    setErrorConfig(null);

    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
    }
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
    }

    const manualFallback = (liveTranscriptRef.current || transcript).trim() || '';

    try {
      const response = await fetch(`/api/interview/${interviewId}/submit-answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          transcript: manualFallback,
          duration_seconds: recordingSeconds || 0
        })
      });

      if (!response.ok) {
        throw new Error('Failed to record answer on server.');
      }

      const answerData = await response.json();
      navigate(`/interview/answer?id=${interviewId}&answerId=${answerData.id}`);
    } catch (err) {
      setIsProcessing(false);
      setErrorConfig({
        message: 'Unable to connect to the server. Please try again.',
        retryLabel: 'Retry',
        onRetry: () => handleEnterManually()
      });
    }
  };

  // 5. Stop Voice Answer
  const handleStopAnswer = async () => {
    isRecordingRef.current = false;
    setIsRecording(false);
    setIsProcessing(true);
    setErrorConfig(null);

    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
    }

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }

    const recordedDuration = recordingSeconds || 1;
    const captured = (liveTranscriptRef.current || transcript).trim();

    if (!captured) {
      setIsProcessing(false);
      setErrorConfig({
        message: "No spoken words were detected from your microphone. Please speak closer to your mic, or type your answer directly.",
        retryLabel: 'Try Speaking Again',
        onRetry: () => handleStartAnswer(),
        secondaryLabel: 'Type Answer Manually',
        secondaryAction: () => handleEnterManually()
      });
      return;
    }

    try {
      const response = await fetch(`/api/interview/${interviewId}/submit-answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          transcript: captured,
          duration_seconds: recordedDuration
        })
      });

      if (!response.ok) {
        throw new Error('Failed to record answer on server.');
      }

      const answerData = await response.json();
      navigate(`/interview/answer?id=${interviewId}&answerId=${answerData.id}`);
    } catch (err) {
      setIsProcessing(false);
      setErrorConfig({
        message: 'Unable to connect to the server. Please try again.',
        retryLabel: 'Retry',
        onRetry: () => handleStopAnswer()
      });
    }
  };

  const formatTimer = (sec) => {
    const mins = Math.floor(sec / 60);
    const secs = sec % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-2 border-amber-500/20 border-t-amber-500 rounded-full animate-spin" />
          <span className="text-xs text-[#A1A1AA] font-mono tracking-wider">Establishing neural interview session...</span>
        </div>
      </div>
    );
  }

  const currentQIndex = question?.question_index || 1;
  const totalQ = question?.total_questions || 10;
  const progressPercent = Math.round((currentQIndex / totalQ) * 100);

  return (
    <div className="flex-1 flex flex-col justify-center items-center px-4 py-8 sm:py-14 relative">
      {/* Central Immersive Amber Light Core */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[650px] h-[450px] bg-amber-500/[0.10] blur-[150px] rounded-full pointer-events-none -z-10" />

      <div className="w-full max-w-2xl">
        {/* Header Progress & Status */}
        <div className="text-center mb-6 space-y-2">
          <div className="flex items-center justify-between text-xs text-[#A1A1AA] px-1 font-mono">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse shadow-amber-glow-sm" />
              <span className="uppercase text-[11px] tracking-widest text-amber-400 font-bold">
                Live Simulation
              </span>
            </div>
            <span>
              Question {currentQIndex} / {totalQ} ({progressPercent}%)
            </span>
          </div>

          {/* Glowing Amber Progress Bar */}
          <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-amber-600 to-amber-400 shadow-amber-glow transition-all duration-slow"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* The AI Interview Chamber: Maximalist Glass Container */}
        <div className="glass-panel p-7 sm:p-10 shadow-glass-panel border border-white/12 text-center relative overflow-hidden">
          {/* Top illuminated edge */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-amber-500/50 to-transparent" />

          {errorConfig && (
            <div className="mb-6">
              <ErrorAlert
                message={errorConfig.message}
                onRetry={errorConfig.onRetry}
                retryLabel={errorConfig.retryLabel}
                secondaryAction={errorConfig.secondaryAction}
                secondaryLabel={errorConfig.secondaryLabel}
              />
            </div>
          )}

          {/* Adaptive Question Indicator */}
          {question?.is_adaptive && (
            <div className="mb-4 inline-flex items-center space-x-2 badge-amber py-1 px-3">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping" />
              <span>Adaptive Question • Tier: {question.difficulty}</span>
            </div>
          )}
          {question?.is_adaptive && question?.adaptive_reason && (
            <p className="text-xs text-[#A1A1AA] mb-4 italic max-w-md mx-auto">
              {question.adaptive_reason}
            </p>
          )}

          {/* Prominent Question Delivery */}
          <div className="py-3 px-2">
            <blockquote
              aria-label="Current interview question"
              className="font-heading text-xl sm:text-2xl font-bold text-[#FAFAF5] leading-relaxed tracking-tight"
            >
              "{question?.question_text}"
            </blockquote>

            {/* Neural Text-to-Speech Controls & Equalizer */}
            <div className="mt-6 flex items-center justify-center space-x-3">
              {isGeneratingTTS ? (
                <div
                  role="status"
                  aria-live="polite"
                  className="inline-flex items-center space-x-2.5 text-xs font-mono text-[#FCD34D] bg-amber-500/10 border border-amber-500/30 px-4 py-2 rounded-full shadow-amber-glow-sm"
                >
                  <span className="w-3 h-3 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" aria-hidden="true" />
                  <span>Synthesizing Interviewer Speech...</span>
                </div>
              ) : isPlayingTTS ? (
                <div className="inline-flex items-center space-x-3">
                  <div
                    role="status"
                    aria-live="polite"
                    className="inline-flex items-center space-x-3 text-xs font-semibold text-[#FAFAF5] bg-amber-500/20 border border-amber-500/40 px-4 py-2 rounded-full shadow-amber-glow"
                  >
                    {/* Expressive Audio Equalizer Waveform */}
                    <div className="flex items-center space-x-1 h-5" aria-hidden="true">
                      <span className="w-1 bg-amber-400 rounded-full animate-soundwave-1 inline-block" />
                      <span className="w-1 bg-amber-400 rounded-full animate-soundwave-2 inline-block" />
                      <span className="w-1 bg-amber-400 rounded-full animate-soundwave-3 inline-block" />
                      <span className="w-1 bg-amber-400 rounded-full animate-soundwave-4 inline-block" />
                      <span className="w-1 bg-amber-400 rounded-full animate-soundwave-5 inline-block" />
                    </div>
                    <span>Interviewer Speaking...</span>
                  </div>
                  <button
                    type="button"
                    onClick={handleStopTTS}
                    aria-label="Stop reading question audio"
                    className="btn-secondary text-xs px-3 py-1.5"
                  >
                    Stop Audio
                  </button>
                </div>
              ) : ttsError ? (
                <div className="flex flex-col items-center space-y-2">
                  <p className="text-xs text-amber-300 bg-amber-500/10 border border-amber-500/25 px-3 py-1.5 rounded-control">
                    {ttsError}
                  </p>
                  <button
                    type="button"
                    onClick={() => playInterviewerQuestion()}
                    className="btn-secondary text-xs px-3.5 py-1.5"
                  >
                    <span>↻ Retry Voice</span>
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => playInterviewerQuestion()}
                  className="btn-secondary text-xs px-4 py-2 rounded-full space-x-2"
                >
                  <span aria-hidden="true">🔊</span>
                  <span>Listen to Question</span>
                </button>
              )}
            </div>
          </div>

          {/* Section Divider */}
          <div className="border-t border-white/10 my-8" role="separator" />

          {/* Candidate Voice Response Chamber */}
          <div className="pt-1">
            <div className="text-[11px] font-mono font-semibold uppercase tracking-widest text-[#A1A1AA] mb-4 text-center">
              Candidate Speech Input
            </div>

            {isProcessing ? (
              /* State: Converting speech to text */
              <div
                role="status"
                aria-live="polite"
                className="py-8 flex flex-col items-center space-y-3"
              >
                <div className="w-8 h-8 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin shadow-amber-glow" aria-hidden="true" />
                <p className="text-xs text-[#FAFAF5] font-mono">Transcribing & evaluating speech payload...</p>
              </div>
            ) : isRecording ? (
              /* State: Live Recording Active with Monospace Timer & Streaming Transcript */
              <div className="space-y-6">
                <div className="flex flex-col items-center justify-center space-y-3 py-2">
                  <div
                    role="status"
                    aria-live="polite"
                    className="flex items-center space-x-2 px-3.5 py-1.5 bg-red-500/20 border border-red-500/40 rounded-full text-xs font-semibold text-red-300 shadow-[0_0_20px_rgba(239,68,68,0.3)]"
                  >
                    <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" aria-hidden="true" />
                    <span className="tracking-widest uppercase text-[11px] font-mono">Mic Live Recording</span>
                  </div>

                  {/* High Contrast Monospace Timer */}
                  <div
                    aria-label="Recording timer"
                    className="text-4xl font-mono font-bold text-[#FAFAF5] tracking-tight drop-shadow-[0_0_15px_rgba(245,158,11,0.3)]"
                  >
                    {formatTimer(recordingSeconds)}
                  </div>

                  {/* Live Streaming STT Transcript Preview Panel */}
                  <div
                    role="region"
                    aria-live="polite"
                    aria-label="Live speech transcript"
                    className="w-full max-w-lg min-h-20 max-h-32 overflow-y-auto p-4 bg-[#111113]/90 border border-white/15 rounded-control text-left mt-3 shadow-2xl"
                  >
                    <span className="text-[10px] font-mono uppercase tracking-wider text-amber-400 block mb-1">
                      Real-time Speech Recognition:
                    </span>
                    <p className="text-xs text-[#FAFAF5] italic leading-relaxed">
                      {transcript || 'Listening to microphone... speak clearly into your mic.'}
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleStopAnswer}
                  className="w-full py-3.5 bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white text-xs font-bold uppercase tracking-wider rounded-control transition-all shadow-[0_0_25px_rgba(239,68,68,0.4)] flex items-center justify-center cursor-pointer"
                >
                  ■ Stop & Submit Answer
                </button>
              </div>
            ) : (
              /* State: Ready / Idle */
              <div className="space-y-4">
                <p className="text-xs text-[#A1A1AA]">
                  {isPlayingTTS
                    ? 'Interviewer is speaking... listen to the prompt before answering.'
                    : isGeneratingTTS
                    ? 'Preparing speech audio...'
                    : 'Click below when you are ready to speak your answer.'}
                </p>

                <button
                  onClick={handleStartAnswer}
                  disabled={isPlayingTTS || isGeneratingTTS}
                  aria-label="Start recording your voice answer"
                  className={`w-full py-4 rounded-control text-sm font-bold transition-all duration-normal flex items-center justify-center space-x-2 ${
                    isPlayingTTS || isGeneratingTTS
                      ? 'bg-white/[0.04] text-[#71717A] border border-white/5 cursor-not-allowed'
                      : 'btn-primary'
                  }`}
                >
                  <span aria-hidden="true" className="text-base">🎙️</span>
                  <span>Start Voice Answer →</span>
                </button>

                <button
                  type="button"
                  onClick={handleEnterManually}
                  className="text-xs text-[#71717A] hover:text-[#FAFAF5] underline underline-offset-2 flex items-center justify-center mx-auto cursor-pointer py-1"
                >
                  Enter Answer Manually
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
