import { useState, useRef, useCallback, useEffect } from "react";

export interface VADOptions {
  silenceThreshold?: number; // Normalized RMS/energy threshold (default 0.012)
  silenceDurationMs?: number; // Trailing silence after speech to auto-stop (default 650ms)
  minSpeechDurationMs?: number; // Minimum speech before silence can trigger auto-stop (default 300ms)
  maxDurationMs?: number; // Maximum recording timeout cutoff (default 8000ms)
  autoStopEnabled?: boolean; // Toggle automatic VAD stop
  initialHandsFree?: boolean; // Whether hands-free mode starts enabled
  onNotice?: (message: string) => void;
}

export function useMicrophoneCapture(
  onTranscriptionComplete?: (text: string) => void,
  options?: VADOptions
) {
  const {
    silenceThreshold = 0.012,
    silenceDurationMs = 650,
    minSpeechDurationMs = 300,
    maxDurationMs = 8000,
    autoStopEnabled = true,
    initialHandsFree = false,
    onNotice,
  } = options || {};

  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isHandsFree, setIsHandsFree] = useState(initialHandsFree);
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
  const isHandsFreeRef = useRef(initialHandsFree);
  const isHandsFreePausedRef = useRef(false);
  const rearmTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const noiseFloorRef = useRef(0.005);

  isHandsFreeRef.current = isHandsFree;

  const stopRecording = useCallback(() => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state !== "inactive" &&
      !isStoppingRef.current
    ) {
      isStoppingRef.current = true;
      try {
        mediaRecorderRef.current.stop();
      } catch (err) {
        console.debug("MediaRecorder stop notice:", err);
      }
      setIsRecording(false);
      setIsSpeaking(false);
    }
  }, []);

  const startRecording = useCallback(async () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      return;
    }

    if (rearmTimerRef.current) {
      clearTimeout(rearmTimerRef.current);
      rearmTimerRef.current = null;
    }

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
          autoGainControl: true,
        },
      });

      // Setup audio analyzer for live waveform visualization and adaptive VAD
      const AudioCtxClass =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const audioCtx = new AudioCtxClass();
      audioContextRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 128;
      analyser.smoothingTimeConstant = 0.3;
      source.connect(analyser);

      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      let sampleFrames = 0;
      let noiseAccum = 0;

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

        // Calibrate noise floor in initial 250ms
        if (sampleFrames < 15) {
          noiseAccum += normalizedLevel;
          sampleFrames++;
          noiseFloorRef.current = Math.max(0.004, noiseAccum / sampleFrames);
        }

        const effectiveThreshold = Math.max(silenceThreshold, noiseFloorRef.current * 1.5);

        if (autoStopEnabled) {
          // Voice Activity Detection logic
          if (normalizedLevel >= effectiveThreshold) {
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
          } else if (isHandsFreeRef.current) {
            // In Hands-Free mode, if no speech detected for 3.5s, recycle buffer to keep audio fresh
            if (now - recordingStartTimeRef.current >= 3500) {
              audioChunksRef.current = [];
              recordingStartTimeRef.current = now;
            }
          }

          // Maximum recording cutoff guardrail (default 8s)
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
        if (audioBlob.size < 100) {
          setIsTranscribing(false);
          isStoppingRef.current = false;
          // In hands-free mode, re-arm listening smoothly
          if (isHandsFreeRef.current && !isHandsFreePausedRef.current) {
            rearmTimerRef.current = setTimeout(() => {
              startRecording();
            }, 400);
          }
          return;
        }

        setIsTranscribing(true);

        // Post to backend for lightning-fast Faster-Whisper transcription
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
            } else if (data.empty) {
              if (onNotice) {
                onNotice("لم يتم التقاط صوت واضح، يمكنك التحدث مجدداً.");
              }
            }
          }
        } catch (uploadErr) {
          console.error("Transcription upload error:", uploadErr);
          setError("تعذر تحويل الصوت إلى نص.");
        } finally {
          setIsTranscribing(false);
          isStoppingRef.current = false;

          // Hands-free continuous loop: Re-arm listening if enabled and not paused
          if (isHandsFreeRef.current && !isHandsFreePausedRef.current) {
            rearmTimerRef.current = setTimeout(() => {
              startRecording();
            }, 600);
          }
        }
      };

      mediaRecorder.start(200);
      setIsRecording(true);
    } catch (err: unknown) {
      console.error("Microphone access error:", err);
      setError("المايكروفون غير متوفر أو تم رفض الإذن.");
      setIsRecording(false);
      setIsSpeaking(false);
    }
  }, [
    autoStopEnabled,
    maxDurationMs,
    minSpeechDurationMs,
    onNotice,
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

  const toggleHandsFree = useCallback(() => {
    setIsHandsFree((prev) => {
      const next = !prev;
      isHandsFreeRef.current = next;
      if (next && !isRecording && !isTranscribing) {
        startRecording();
      } else if (!next && isRecording) {
        stopRecording();
      }
      return next;
    });
  }, [isRecording, isTranscribing, startRecording, stopRecording]);

  const setHandsFreePaused = useCallback((paused: boolean) => {
    isHandsFreePausedRef.current = paused;
    if (!paused && isHandsFreeRef.current && !isRecording && !isTranscribing) {
      if (rearmTimerRef.current) clearTimeout(rearmTimerRef.current);
      rearmTimerRef.current = setTimeout(() => {
        startRecording();
      }, 700);
    }
  }, [isRecording, isTranscribing, startRecording]);

  useEffect(() => {
    return () => {
      if (rearmTimerRef.current) clearTimeout(rearmTimerRef.current);
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  return {
    isRecording,
    isTranscribing,
    isSpeaking,
    audioLevel,
    isHandsFree,
    error,
    startRecording,
    stopRecording,
    toggleRecording,
    toggleHandsFree,
    setHandsFreePaused,
  };
}
