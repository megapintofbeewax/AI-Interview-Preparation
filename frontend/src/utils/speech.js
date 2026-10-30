/**
 * Dedicated Speech Services Utility
 * Powered by Neural Text-to-Speech (Edge-TTS / ElevenLabs) with HTML5 Audio streaming
 * and Web Speech API Speech-to-Text (STT) for candidate responses.
 */

// Global single instance to prevent overlapping audio
let activeAudio = null;
let activeBlobUrl = null;

export const isNeuralTTSSupported = () => {
  return typeof window !== 'undefined' && typeof window.Audio !== 'undefined';
};

export const stopAudio = () => {
  if (activeAudio) {
    try {
      activeAudio.pause();
      activeAudio.currentTime = 0;
      activeAudio.removeAttribute('src');
      activeAudio.load();
    } catch (e) {
      console.warn('Audio cancel error:', e);
    }
    activeAudio = null;
  }
  if (activeBlobUrl) {
    try {
      URL.revokeObjectURL(activeBlobUrl);
    } catch (e) {}
    activeBlobUrl = null;
  }
  // Also cancel any residual browser speech synthesis if active
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
    try {
      window.speechSynthesis.cancel();
    } catch (e) {}
  }
};

/**
 * Streams neural interviewer voice audio from the backend.
 * Provides granular lifecycle callbacks: onLoading, onStart, onEnd, onError.
 */
export const playQuestionAudio = async ({
  interviewId,
  questionId,
  token,
  voice,
  onLoading,
  onStart,
  onEnd,
  onError
} = {}) => {
  if (!isNeuralTTSSupported()) {
    const err = new Error('Audio playback not supported in this browser.');
    if (onError) onError(err);
    return;
  }

  // Stop any previously playing audio to ensure strictly zero overlap
  stopAudio();

  if (onLoading) onLoading();

  try {
    const voiceParam = voice ? `?voice=${encodeURIComponent(voice)}` : '';
    const url = `/api/interview/${interviewId}/question/${questionId}/audio${voiceParam}`;
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

    const response = await fetch(url, { headers });
    if (!response.ok) {
      throw new Error(`Audio fetch failed with status: ${response.status}`);
    }

    const blob = await response.blob();
    if (!blob || blob.size === 0) {
      throw new Error('Received empty audio stream from speech service.');
    }

    const blobUrl = URL.createObjectURL(blob);
    activeBlobUrl = blobUrl;

    const audio = new Audio(blobUrl);
    activeAudio = audio;

    audio.onplay = () => {
      if (onStart) onStart();
    };

    audio.onended = () => {
      stopAudio();
      if (onEnd) onEnd();
    };

    audio.onerror = (e) => {
      stopAudio();
      if (onError) onError(new Error('Audio stream playback failed.'));
    };

    await audio.play();
    return audio;
  } catch (err) {
    stopAudio();
    if (onError) onError(err);
    throw err;
  }
};

// Aliases for seamless backwards compatibility
export const stopSpeech = stopAudio;
export const isTTSSupported = isNeuralTTSSupported;

// Intentional fallback using browser speech synthesis (used only if explicitly requested)
export const speakWithBrowserFallback = (text, { onStart, onEnd, onError, rate = 0.95, pitch = 1.0 } = {}) => {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
    if (onError) onError(new Error('Browser speech synthesis not supported'));
    return;
  }
  stopAudio();
  const cleanText = text.replace(/[`*_~]/g, '').trim();
  const utterance = new SpeechSynthesisUtterance(cleanText);
  utterance.rate = rate;
  utterance.pitch = pitch;
  utterance.lang = 'en-US';
  if (onStart) utterance.onstart = onStart;
  if (onEnd) utterance.onend = onEnd;
  if (onError) utterance.onerror = onError;
  window.speechSynthesis.speak(utterance);
};

export const speakText = speakWithBrowserFallback;

// --- SPEECH-TO-TEXT (STT) ---

export const isSTTSupported = () => {
  if (typeof window === 'undefined') return false;
  return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
};

export const createSpeechRecognizer = ({ onResult, onError, onEnd, lang = 'en-US' } = {}) => {
  if (!isSTTSupported()) {
    return null;
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = lang;

  recognition.onresult = (event) => {
    let fullTranscript = '';
    for (let i = 0; i < event.results.length; i++) {
      fullTranscript += event.results[i][0].transcript + ' ';
    }
    if (onResult) {
      onResult(fullTranscript.trim());
    }
  };

  if (onError) {
    recognition.onerror = onError;
  }

  if (onEnd) {
    recognition.onend = onEnd;
  }

  return recognition;
};
