import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Mic,
  MicOff,
  Sparkles,
  Activity,
  AppWindow,
  Clipboard,
  Bot,
  User,
  Volume2,
  X,
  Zap,
  Radio,
  Pin,
  PinOff,
  Globe,
  Camera,
  Layers,
} from "lucide-react";
import { AudioWaveform } from "./AudioWaveform";
import { ActionCard } from "./ActionCard";
import { ModelSetupBanner } from "./ModelSetupBanner";
import { SystemTelemetryModal } from "./SystemTelemetryModal";
import { useAegisWebSocket } from "../hooks/useAegisWebSocket";
import { useMicrophoneCapture } from "../hooks/useMicrophoneCapture";
import { fetchSystemStatus, fetchWakeWordStatus, toggleWakeWord, triggerVoiceSpeech } from "../services/api";
import { SystemTelemetry, AIRuntimeStatus, VoiceStatus, WakeWordStatus } from "../types";

export const CompanionOverlay: React.FC = () => {
  const [sessionId] = useState(() => "session-" + Math.random().toString(36).substring(7));
  const { messages, activeTools, isStreaming, isConnected, sendMessage } = useAegisWebSocket(sessionId);

  const [input, setInput] = useState("");
  const [showTelemetry, setShowTelemetry] = useState(false);
  const [telemetry, setTelemetry] = useState<SystemTelemetry | null>(null);
  const [runtimeStatus, setRuntimeStatus] = useState<AIRuntimeStatus | null>(null);
  const [voiceStatus, setVoiceStatus] = useState<VoiceStatus | null>(null);
  const [wakeWordStatus, setWakeWordStatus] = useState<WakeWordStatus | null>(null);
  const [isPinned, setIsPinned] = useState(false);

  const fetchPinStatus = useCallback(() => {
    // @ts-expect-error pywebview JS bridge
    if (window.pywebview?.api?.get_on_top) {
      // @ts-expect-error pywebview JS bridge
      window.pywebview.api.get_on_top().then((status: boolean) => setIsPinned(status));
    } else {
      fetch("http://127.0.0.1:8420/api/desktop/pin")
        .then((res) => res.json())
        .then((data) => {
          if (typeof data.is_on_top === "boolean") setIsPinned(data.is_on_top);
        })
        .catch(() => {});
    }
  }, []);

  const handleTogglePin = async () => {
    // @ts-expect-error pywebview JS bridge
    if (window.pywebview?.api?.toggle_on_top) {
      // @ts-expect-error pywebview JS bridge
      const newStatus = await window.pywebview.api.toggle_on_top();
      setIsPinned(newStatus);
    } else {
      try {
        const res = await fetch("http://127.0.0.1:8420/api/desktop/pin", { method: "POST" });
        const data = await res.json();
        if (typeof data.is_on_top === "boolean") setIsPinned(data.is_on_top);
      } catch (err) {
        console.error("Failed to toggle pin state:", err);
      }
    }
  };

  const handleToggleWakeWord = async () => {
    try {
      const updated = await toggleWakeWord();
      setWakeWordStatus(updated);
    } catch (err) {
      console.error("Failed to toggle wake word:", err);
    }
  };

  const scrollRef = useRef<HTMLDivElement>(null);

  const handleTranscription = useCallback((text: string) => {
    if (text.trim()) {
      setInput(text.trim());
      sendMessage(text.trim());
    }
  }, [sendMessage]);

  const {
    isRecording,
    isTranscribing,
    isSpeaking,
    audioLevel,
    toggleRecording,
  } = useMicrophoneCapture(handleTranscription);

  const refreshTelemetry = useCallback(() => {
    fetchSystemStatus()
      .then((res) => {
        setTelemetry(res.telemetry);
        setRuntimeStatus(res.ai_runtime);
        setVoiceStatus(res.voice);
        fetchWakeWordStatus().then(setWakeWordStatus).catch(() => {});
      })
      .catch((err) => console.error("Telemetry query error:", err));
  }, []);

  const dismissOverlay = () => {
    // @ts-expect-error pywebview JS bridge
    if (window.pywebview?.api?.hide) {
      // @ts-expect-error pywebview JS bridge
      window.pywebview.api.hide();
    } else {
      fetch("http://127.0.0.1:8420/api/desktop/hide", { method: "POST" }).catch(() => {});
    }
  };

  useEffect(() => {
    const handleGlobalKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        dismissOverlay();
      }
    };
    window.addEventListener("keydown", handleGlobalKey);

    refreshTelemetry();
    fetchPinStatus();
    return () => window.removeEventListener("keydown", handleGlobalKey);
  }, [refreshTelemetry, fetchPinStatus]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, activeTools]);

  const handleSend = () => {
    if (!input.trim() || isStreaming) return;
    sendMessage(input.trim());
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleQuickAction = (command: string) => {
    sendMessage(command);
  };

  const handleSpeak = (text: string) => {
    triggerVoiceSpeech(text);
  };

  const activeModelDisplay =
    runtimeStatus?.ollama?.models && runtimeStatus.ollama.models.length > 0
      ? runtimeStatus.ollama.models[0]
      : runtimeStatus?.ollama?.status === "needs_model"
      ? "No Model Downloaded"
      : "Pollinations (Emergency)";

  return (
    <div className="w-full h-full flex flex-col bg-[#0b0f19] border border-slate-800 shadow-2xl relative select-none">
      {/* Top Header Bar with Native Window Dragging & Quick Actions */}
      <div className="pywebview-drag-region flex items-center justify-between px-4 py-2.5 border-b border-slate-800 bg-[#0f172a] shrink-0 select-none cursor-move">
        <div className="flex items-center gap-3">
          {/* Logo & Online Status */}
          <div className="relative shrink-0">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-sky-600 to-cyan-400 flex items-center justify-center shadow-md shadow-sky-500/20">
              <Sparkles className="w-3.5 h-3.5 text-slate-950 fill-current" />
            </div>
            <span
              className={`absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full border-2 border-slate-900 ${
                isConnected ? "bg-emerald-400" : "bg-rose-400"
              }`}
            />
          </div>

          {/* Title & Badge */}
          <div className="flex items-center gap-2">
            <h1 className="font-bold text-sm tracking-wide text-slate-100 whitespace-nowrap">Aegis AI</h1>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 font-semibold border border-sky-500/30 whitespace-nowrap">
              Alt+Space
            </span>
            <span className="text-xs text-slate-600">•</span>
            <span className="text-[11px] text-slate-400 font-mono truncate max-w-[170px]" title={activeModelDisplay}>
              {activeModelDisplay}
            </span>
            {runtimeStatus?.tokens_per_second ? (
              <span className="flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30 whitespace-nowrap">
                <Zap className="w-3 h-3" />
                {runtimeStatus.tokens_per_second} t/s
              </span>
            ) : null}
          </div>
        </div>

        {/* Right Controls */}
        <div className="flex items-center gap-1.5 shrink-0" onMouseDown={(e) => e.stopPropagation()}>
          <AudioWaveform
            isActive={isRecording || isTranscribing || voiceStatus?.state === "speaking"}
            statusText={
              isTranscribing
                ? "Transcribing..."
                : isRecording
                ? isSpeaking
                  ? "Speaking..."
                  : "Listening..."
                : voiceStatus?.state === "speaking"
                ? "Voice Output"
                : "Ready"
            }
          />

          <button
            onClick={handleToggleWakeWord}
            className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs font-mono transition border ${
              wakeWordStatus?.is_running
                ? "bg-cyan-500/15 border-cyan-500/40 text-cyan-300 shadow-sm shadow-cyan-500/20"
                : "bg-slate-800 border-slate-700/60 text-slate-400 hover:text-slate-200"
            }`}
            title={wakeWordStatus?.is_running ? "Wake Word Listening Active (Click to Pause)" : "Enable Wake Word Summoning"}
          >
            <Radio className={`w-3.5 h-3.5 ${wakeWordStatus?.is_running ? "text-cyan-400 animate-pulse" : ""}`} />
            <span className="text-[11px]">
              {wakeWordStatus?.is_running ? wakeWordStatus.active_model.replace("_", " ") : "Wake Word"}
            </span>
          </button>

          <button
            onClick={handleTogglePin}
            className={`p-1.5 rounded-lg transition border ${
              isPinned
                ? "bg-sky-500/15 border-sky-500/40 text-sky-300 shadow-sm shadow-sky-500/20"
                : "bg-slate-800 border-slate-700/60 text-slate-400 hover:text-slate-200"
            }`}
            title={isPinned ? "Always-on-top active (Click to allow other windows over Aegis)" : "Unpinned (Click to keep on top)"}
          >
            {isPinned ? <Pin className="w-3.5 h-3.5 fill-current" /> : <PinOff className="w-3.5 h-3.5" />}
          </button>

          <button
            onClick={() => setShowTelemetry(true)}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700/60 text-slate-300 hover:text-white transition"
            title="System Telemetry"
          >
            <Activity className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={dismissOverlay}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-rose-500/20 border border-slate-700/60 text-slate-400 hover:text-rose-400 transition"
            title="Dismiss Overlay (ESC)"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Model Bootstrapper Banner (Shows only if models are missing or server needs starting) */}
      <ModelSetupBanner ollama={runtimeStatus?.ollama || null} onRefresh={refreshTelemetry} />

      {/* Messages & Tool Activity Area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-400">
            <div className="w-12 h-12 rounded-2xl bg-slate-800/60 border border-slate-700/60 flex items-center justify-center mb-3 text-sky-400">
              <Bot className="w-6 h-6" />
            </div>
            <h3 className="font-semibold text-slate-200 text-sm mb-1">
              Windows Desktop Companion Active
            </h3>
            <p className="text-xs text-slate-400 max-w-sm mb-5">
              Click the microphone to speak, or type commands below. Press ESC to dismiss.
            </p>

            <div className="grid grid-cols-2 gap-2 w-full max-w-md">
              <button
                onClick={() => handleQuickAction("افتح موقع يوتيوب بمتصفح كروم")}
                className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-800/50 hover:bg-slate-800 text-xs text-slate-300 border border-slate-700/50 transition text-left group"
              >
                <Globe className="w-4 h-4 text-rose-400 shrink-0 group-hover:scale-110 transition-transform" />
                <span className="truncate">YouTube in Chrome</span>
              </button>

              <button
                onClick={() => handleQuickAction("افتح جوجل بمتصفح كومت")}
                className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-800/50 hover:bg-slate-800 text-xs text-slate-300 border border-slate-700/50 transition text-left group"
              >
                <Globe className="w-4 h-4 text-cyan-400 shrink-0 group-hover:scale-110 transition-transform" />
                <span className="truncate">Google in Comet</span>
              </button>

              <button
                onClick={() => handleQuickAction("open notepad")}
                className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-800/50 hover:bg-slate-800 text-xs text-slate-300 border border-slate-700/50 transition text-left"
              >
                <AppWindow className="w-4 h-4 text-sky-400 shrink-0" />
                <span>Launch Notepad</span>
              </button>

              <button
                onClick={() => handleQuickAction("صور الشاشة")}
                className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-800/50 hover:bg-slate-800 text-xs text-slate-300 border border-slate-700/50 transition text-left"
              >
                <Camera className="w-4 h-4 text-amber-400 shrink-0" />
                <span>Take Screenshot</span>
              </button>

              <button
                onClick={() => handleQuickAction("صغر كل النوافذ")}
                className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-800/50 hover:bg-slate-800 text-xs text-slate-300 border border-slate-700/50 transition text-left"
              >
                <Layers className="w-4 h-4 text-purple-400 shrink-0" />
                <span>Show Desktop</span>
              </button>

              <button
                onClick={() => handleQuickAction("get clipboard")}
                className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-800/50 hover:bg-slate-800 text-xs text-slate-300 border border-slate-700/50 transition text-left"
              >
                <Clipboard className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Read Clipboard</span>
              </button>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 text-sm leading-relaxed ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {msg.role === "assistant" && (
              <div className="w-7 h-7 rounded-lg bg-sky-500/20 text-sky-400 flex items-center justify-center shrink-0 mt-0.5">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-[85%] px-4 py-3 rounded-2xl ${
                msg.role === "user"
                  ? "bg-sky-600 text-white rounded-tr-none shadow-md"
                  : "bg-slate-800/70 border border-slate-700/50 text-slate-200 rounded-tl-none shadow-sm"
              }`}
            >
              <div className="whitespace-pre-wrap font-sans">{msg.content}</div>

              {msg.role === "assistant" && msg.content && (
                <div className="mt-2 pt-2 border-t border-slate-700/40 flex items-center justify-between text-[11px] text-slate-400">
                  <span className="font-mono">{msg.provider || "local"}</span>
                  <button
                    onClick={() => handleSpeak(msg.content)}
                    className="p-1 hover:text-sky-300 transition"
                    title="Speak text aloud with neural voice"
                  >
                    <Volume2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
            </div>

            {msg.role === "user" && (
              <div className="w-7 h-7 rounded-lg bg-slate-700 text-slate-300 flex items-center justify-center shrink-0 mt-0.5">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {/* Active Tool Cards */}
        {activeTools.map((act, idx) => (
          <ActionCard key={idx} activity={act} />
        ))}
      </div>

      {/* Input Prompt Bar */}
      <div className="p-4 border-t border-slate-700/50 bg-slate-900/60">
        <div className="flex items-center gap-2 p-1.5 rounded-2xl bg-slate-800/80 border border-slate-700/80 focus-within:border-sky-500/60 focus-within:ring-2 focus-within:ring-sky-500/20 transition-all">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            autoFocus
            disabled={isTranscribing}
            placeholder={
              isTranscribing
                ? "Transcribing speech with Whisper..."
                : isRecording
                ? isSpeaking
                  ? "Listening... (speech detected)"
                  : "Listening... (speak now, pauses auto-submit)"
                : "Ask Aegis or command Windows..."
            }
            className="flex-1 bg-transparent px-3 py-1.5 text-sm text-slate-100 placeholder:text-slate-400 focus:outline-none disabled:opacity-60"
          />

          <button
            onClick={toggleRecording}
            disabled={isTranscribing}
            style={{ transform: isRecording ? `scale(${1 + audioLevel * 0.25})` : undefined }}
            className={`p-2 rounded-xl transition-all ${
              isTranscribing
                ? "bg-amber-500/80 text-slate-950 animate-pulse cursor-wait"
                : isRecording
                ? "bg-rose-500 text-white shadow-lg shadow-rose-500/50"
                : "bg-slate-700/60 hover:bg-slate-700 text-slate-300 hover:text-white"
            }`}
            title={
              isTranscribing
                ? "Transcribing audio..."
                : isRecording
                ? "Recording (auto-stops on silence, or click to stop)"
                : "Click to speak (auto-detects silence)"
            }
          >
            {isTranscribing ? (
              <Activity className="w-4 h-4 animate-spin" />
            ) : isRecording ? (
              <MicOff className="w-4 h-4" />
            ) : (
              <Mic className="w-4 h-4" />
            )}
          </button>

          <button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming || isTranscribing}
            className="p-2 rounded-xl bg-sky-500 hover:bg-sky-400 disabled:opacity-40 disabled:cursor-not-allowed text-slate-950 font-semibold transition shadow-md shadow-sky-500/20"
            title="Send (Enter)"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Telemetry Modal */}
      {showTelemetry && (
        <SystemTelemetryModal
          telemetry={telemetry}
          runtimeStatus={runtimeStatus}
          onClose={() => setShowTelemetry(false)}
        />
      )}
    </div>
  );
};
