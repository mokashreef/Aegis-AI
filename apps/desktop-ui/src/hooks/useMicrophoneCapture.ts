import { useState, useRef, useCallback } from "react";

export interface VADOptions {
  silenceThreshold?: number; // Normalized RMS/energy threshold (0.0 to 1.0)
  silenceDurationMs?: number; // Trailing silence after speech to auto-stop
  minSpeechDurationMs?: number; // Minimum speech before silence can trigger auto-stop
  maxDurationMs?: number; // Maximum recording timeout cutoff
  autoStopEnabled?: boolean; // Toggle automatic VAD stop
}

export function useMicrophoneCapture(
  onTranscriptionComplete?: (text: string) => void,
  options?: VADOptions
) {
  const {
    silenceThreshold = 0.04,
    silenceDurationMs = 900,
    minSpeechDurationMs = 500,
    maxDurationMs = 20000,
    autoStopEnabled = true,
  } = options || {};

  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  const speechDetectedRef = useRef(false);
  const speechStartTimeRef = useRef(0);
  const lastSpeechTimeRef = useRef(0);
  const recordingStartTimeRef = useRef(0);
  const isStoppingRef = useRef(false);

  const stopRecording = useCallback(() => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive" &&
      !isStoppingRef.current
    ) {
      isStoppingRef.current = true;
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsSpeaking(false);
    }
  }, []);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      audioChunksRef.current = [];
      speechDetectedRef.current = false;
      speechStartTimeRef.current = 0;
      lastSpeechTimeRef.current = 0;
      recordingStartTimeRef.current = Date.now();
      isStoppingRef.current = false;
      setIsSpeaking(false);

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      // Setup audio analyzer for live waveform visualization and VAD
      const AudioCtxClass =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const audioCtx = new AudioCtxClass();
      audioContextRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      source.connect(analyser);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateVolume = () => {
        if (
          !mediaRecorderRef.current ||
          mediaRecorderRef.current.state === "inactive" ||
          isStoppingRef.current
        ) {
          return;
        }

        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        const normalizedLevel = Math.min(1.0, avg / 128);
        setAudioLevel(normalizedLevel);

        const now = Date.now();

        if (autoStopEnabled) {
          // Voice Activity Detection logic
          if (normalizedLevel >= silenceThreshold) {
            if (!speechDetectedRef.current) {
              speechDetectedRef.current = true;
              speechStartTimeRef.current = now;
              setIsSpeaking(true);
            }
            lastSpeechTimeRef.current = now;
          } else if (speechDetectedRef.current) {
            const speechDuration = (lastSpeechTimeRef.current || now) - speechStartTimeRef.current;
            const silenceDuration = now - (lastSpeechTimeRef.current || now);

            // Auto-stop when natural speech pause is detected
            if (speechDuration >= minSpeechDurationMs && silenceDuration >= silenceDurationMs) {
              stopRecording();
              return;
            }
          }

          // Safety guardrail for maximum recording cutoff
          if (recordingStartTimeRef.current && now - recordingStartTimeRef.current >= maxDurationMs) {
            stopRecording();
            return;
          }
        }

        animationFrameRef.current = requestAnimationFrame(updateVolume);
      };
      updateVolume();

      // Determine supported mime type
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Cleanly stop audio tracks and context
        stream.getTracks().forEach((track) => track.stop());
        if (audioContextRef.current) {
          audioContextRef.current.close().catch(() => {});
        }
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
        }
        setAudioLevel(0);
        setIsSpeaking(false);

        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        if (audioBlob.size === 0) {
          setIsTranscribing(false);
          isStoppingRef.current = false;
          return;
        }

        setIsTranscribing(true);

        // Post to backend for Faster-Whisper transcription
        try {
          const formData = new FormData();
          formData.append("file", audioBlob, "mic_input.webm");

          const response = await fetch("http://127.0.0.1:8420/api/voice/transcribe", {
            method: "POST",
            body: formData,
          });

          if (response.ok) {
            const data = await response.json();
            const text = data.text?.trim();
            if (text && onTranscriptionComplete) {
              onTranscriptionComplete(text);
            }
          }
        } catch (uploadErr) {
          console.error("Transcription upload error:", uploadErr);
          setError("Failed to transcribe audio.");
        } finally {
          setIsTranscribing(false);
          isStoppingRef.current = false;
        }
      };

      mediaRecorder.start(250);
      setIsRecording(true);
    } catch (err: unknown) {
      console.error("Microphone access error:", err);
      setError("Microphone permission denied or unavailable.");
      setIsRecording(false);
      setIsSpeaking(false);
    }
  }, [
    autoStopEnabled,
    maxDurationMs,
    minSpeechDurationMs,
    onTranscriptionComplete,
    silenceDurationMs,
    silenceThreshold,
    stopRecording,
  ]);

  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  return {
    isRecording,
    isTranscribing,
    isSpeaking,
    audioLevel,
    error,
    startRecording,
    stopRecording,
    toggleRecording,
  };
}
