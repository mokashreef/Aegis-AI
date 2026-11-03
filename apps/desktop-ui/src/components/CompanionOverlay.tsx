import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Mic,
  MicOff,
  Sparkles,
  Eye,
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
  Settings as SettingsIcon,
  Paperclip,
  FileText,
  Loader2,
  Bell,
  Clock,
  Play,
  SkipForward,
  SkipBack,
  Headphones,
} from "lucide-react";
import { AudioWaveform } from "./AudioWaveform";
import { ActionCard } from "./ActionCard";
import { ModelSetupBanner } from "./ModelSetupBanner";
import { SystemTelemetryModal } from "./SystemTelemetryModal";
import { SettingsModal } from "./SettingsModal";
import { useAegisWebSocket } from "../hooks/useAegisWebSocket";
import { useMicrophoneCapture } from "../hooks/useMicrophoneCapture";
import {
  fetchSettings,
  fetchSystemStatus,
  fetchWakeWordStatus,
  toggleWakeWord,
  triggerVoiceSpeech,
  uploadDocument,
  fetchReminders,
  cancelReminder,
  controlMedia,
} from "../services/api";
import {
  SystemTelemetry,
  AIRuntimeStatus,
  VoiceStatus,
  WakeWordStatus,
  UserSettings,
  QuickActionItem,
  DocumentItem,
  ReminderItem,
} from "../types";

export const CompanionOverlay: React.FC = () => {
  const [sessionId] = useState(() => "session-" + Math.random().toString(36).substring(7));
  const [userSettings, setUserSettings] = useState<UserSettings | null>(null);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  const handleStreamFinished = useCallback(
    (fullText: string) => {
      if (userSettings?.auto_speak && fullText.trim()) {
        triggerVoiceSpeech(fullText.trim());
      }
    },
    [userSettings]
  );

  const [activeReminders, setActiveReminders] = useState<ReminderItem[]>([]);
  const [firingReminder, setFiringReminder] = useState<ReminderItem | null>(null);

  const handleReminderAlert = useCallback((rem: ReminderItem) => {
    setFiringReminder(rem);
    fetchReminders().then(setActiveReminders).catch(() => {});
  }, []);

  const sendMessageRef = useRef<(text: string, confirmed?: boolean) => void>(() => {});
  const [voiceNotice, setVoiceNotice] = useState<string | null>(null);

  const handleVoiceNotice = useCallback((msg: string) => {
    setVoiceNotice(msg);
    setTimeout(() => setVoiceNotice(null), 3500);
  }, []);

  const handleTranscription = useCallback((text: string) => {
    if (text.trim()) {
      setInput(text.trim());
      sendMessageRef.current(text.trim());
    }
  }, []);

  const {
    isRecording,
    isTranscribing,
    isSpeaking,
    audioLevel,
    isHandsFree,
    startRecording,
    toggleRecording,
    toggleHandsFree,
    setHandsFreePaused,
  } = useMicrophoneCapture(handleTranscription, {
    silenceThreshold: 0.012,
    silenceDurationMs: 650,
    minSpeechDurationMs: 300,
    maxDurationMs: 8000,
    initialHandsFree: localStorage.getItem("aegis_hands_free") === "true",
    onNotice: handleVoiceNotice,
  });

  const handleWakeWordTriggered = useCallback((keyword: string) => {
    console.log("Wake word triggered:", keyword);
    setVoiceNotice(`🎙️ تم التقاط النداء الصوتي (${keyword})! تحدث الآن...`);
    setTimeout(() => setVoiceNotice(null), 3000);
    startRecording();
  }, [startRecording]);

  const { messages, activeTools, isStreaming, isConnected, sendMessage, clearMessages } = useAegisWebSocket(
    sessionId,
    handleStreamFinished,
    handleReminderAlert,
    handleWakeWordTriggered
  );

  sendMessageRef.current = sendMessage;

  useEffect(() => {
    setHandsFreePaused(isStreaming);
  }, [isStreaming, setHandsFreePaused]);

  useEffect(() => {
    localStorage.setItem("aegis_hands_free", isHandsFree ? "true" : "false");
  }, [isHandsFree]);

  const [input, setInput] = useState("");
  const [showTelemetry, setShowTelemetry] = useState(false);
  const [telemetry, setTelemetry] = useState<SystemTelemetry | null>(null);
  const [runtimeStatus, setRuntimeStatus] = useState<AIRuntimeStatus | null>(null);
  const [voiceStatus, setVoiceStatus] = useState<VoiceStatus | null>(null);
  const [wakeWordStatus, setWakeWordStatus] = useState<WakeWordStatus | null>(null);
  const [isPinned, setIsPinned] = useState(false);

  useEffect(() => {
    const updateReminders = () => {
      fetchReminders("active").then(setActiveReminders).catch(() => {});
    };
    updateReminders();
    const interval = setInterval(updateReminders, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (activeReminders.length === 0) return;
    const tick = setInterval(() => {
      setActiveReminders((prev) =>
        prev
          .map((r) => ({
            ...r,
            remaining_seconds: Math.max(0, Math.floor(r.due_timestamp - Date.now() / 1000)),
          }))
          .filter((r) => (r.remaining_seconds ?? 0) > 0)
      );
    }, 1000);
    return () => clearInterval(tick);
  }, [activeReminders.length]);

  const formatCountdown = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const handleMediaAction = async (action: "play_pause" | "next" | "previous") => {
    try {
      await controlMedia(action);
    } catch (err) {
      console.error("Failed to control media:", err);
    }
  };

  const handleCancelReminder = async (id: string) => {
    await cancelReminder(id);
    setActiveReminders((prev) => prev.filter((r) => r.id !== id));
  };
  const [isDragging, setIsDragging] = useState(false);
  const [activeDocument, setActiveDocument] = useState<DocumentItem | null>(null);
  const [isUploadingDoc, setIsUploadingDoc] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (file: File) => {
    try {
      setIsUploadingDoc(true);
      const doc = await uploadDocument(file);
      setActiveDocument(doc);
    } catch (err) {
      console.error("Failed to upload document:", err);
    } finally {
      setIsUploadingDoc(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.currentTarget.contains(e.relatedTarget as Node)) return;
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

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

// (Microphone capture initialized with hands-free support above)

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
    fetchSettings().then(setUserSettings).catch(() => {});
    return () => window.removeEventListener("keydown", handleGlobalKey);
  }, [refreshTelemetry, fetchPinStatus]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, activeTools]);

  const handleSend = () => {
    if (!input.trim() || isStreaming) return;
    let queryToSend = input.trim();
    if (activeDocument) {
      const isDocQuery = /(?:مستند|ملف|document|file)/i.test(queryToSend);
      if (!isDocQuery) {
        queryToSend = `ابحث في المستند عن: ${queryToSend}`;
      }
    }
    sendMessage(queryToSend);
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

  const renderQuickActionIcon = (iconName: string) => {
    switch (iconName) {
      case "globe":
        return <Globe className="w-4 h-4 text-cyan-400 shrink-0 group-hover:scale-110 transition-transform" />;
      case "camera":
        return <Camera className="w-4 h-4 text-amber-400 shrink-0 group-hover:scale-110 transition-transform" />;
      case "layers":
        return <Layers className="w-4 h-4 text-purple-400 shrink-0 group-hover:scale-110 transition-transform" />;
      case "clipboard":
        return <Clipboard className="w-4 h-4 text-emerald-400 shrink-0 group-hover:scale-110 transition-transform" />;
      default:
        return <AppWindow className="w-4 h-4 text-sky-400 shrink-0 group-hover:scale-110 transition-transform" />;
    }
  };

  const defaultQuickActions: QuickActionItem[] = [
    { id: "1", title: "YouTube in Chrome", title_ar: "يوتيوب في كروم", command: "افتح موقع يوتيوب بمتصفح كروم", icon: "globe", enabled: true },
    { id: "2", title: "Google in Comet", title_ar: "جوجل في كومت", command: "افتح جوجل بمتصفح كومت", icon: "globe", enabled: true },
    { id: "3", title: "Launch Notepad", title_ar: "المفكرة", command: "open notepad", icon: "app", enabled: true },
    { id: "4", title: "Take Screenshot", title_ar: "لقطة شاشة", command: "صور الشاشة", icon: "camera", enabled: true },
    { id: "vision", title: "Ask My Screen", title_ar: "تحليل الشاشة الذكي", command: "حلل ما يظهر على الشاشة واشرح محتواها", icon: "camera", enabled: true },
    { id: "timer5", title: "Timer 5 Mins", title_ar: "مؤقت 5 دقائق", command: "اضبط مؤقت 5 دقائق", icon: "app", enabled: true },
    { id: "media_pp", title: "Play/Pause Media", title_ar: "تشغيل/إيقاف الموسيقى", command: "شغل أو وقف الموسيقى", icon: "volume", enabled: true },
    { id: "media_next", title: "Next Track", title_ar: "المقطع التالي", command: "المقطع التالي", icon: "volume", enabled: true },
    { id: "5", title: "Show Desktop", title_ar: "إظهار سطح المكتب", command: "صغر كل النوافذ", icon: "layers", enabled: true },
    { id: "6", title: "Read Clipboard", title_ar: "قراءة الحافظة", command: "get clipboard", icon: "clipboard", enabled: true },
  ];

  const quickActionsToRender = userSettings?.quick_actions
    ? userSettings.quick_actions.filter((a) => a.enabled)
    : defaultQuickActions;

  const activeModelDisplay =
    runtimeStatus?.ollama?.models && runtimeStatus.ollama.models.length > 0
      ? runtimeStatus.ollama.models[0]
      : runtimeStatus?.ollama?.status === "needs_model"
      ? "No Model Downloaded"
      : "Pollinations (Emergency)";

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`w-full h-full flex flex-col bg-[#0b0f19] border border-slate-800 shadow-2xl relative select-none ${
        userSettings?.theme === "light" ? "theme-light" : ""
      }`}
    >
      {/* System Reminder / Timer Alert Popup Banner */}
      {firingReminder && (
        <div className="absolute top-12 left-4 right-4 z-50 p-4 rounded-2xl bg-gradient-to-r from-amber-600/95 to-rose-600/95 text-white shadow-2xl border border-amber-300/50 backdrop-blur-md flex items-center justify-between gap-3 animate-in fade-in slide-in-from-top-4 duration-300">
          <div className="flex items-center gap-3 truncate">
            <div className="w-10 h-10 rounded-xl bg-white/20 flex items-center justify-center shrink-0">
              <Bell className="w-6 h-6 text-white animate-bounce" />
            </div>
            <div className="truncate">
              <div className="text-[11px] uppercase tracking-wider text-amber-100 font-bold">
                {firingReminder.remind_type === "timer"
                  ? "⏳ انتهى المؤقت (Timer Finished)"
                  : "⏰ موعد التنبيه (Reminder Alert)"}
              </div>
              <div className="text-sm font-bold text-white truncate leading-tight mt-0.5">
                {firingReminder.title}
              </div>
              <div className="text-[10px] text-amber-100/80">
                {firingReminder.due_time_str}
              </div>
            </div>
          </div>
          <button
            onClick={() => setFiringReminder(null)}
            className="px-3 py-1.5 rounded-xl bg-white text-slate-900 font-bold text-xs hover:bg-amber-100 transition shadow shrink-0"
          >
            {userSettings?.language === "en" ? "Dismiss" : "حسناً / إغلاق"}
          </button>
        </div>
      )}

      {/* Drag & Drop Visual HUD Overlay */}
      {isDragging && (
        <div className="absolute inset-0 z-50 bg-slate-950/85 backdrop-blur-md flex flex-col items-center justify-center border-2 border-dashed border-sky-400 m-2 rounded-2xl pointer-events-none">
          <div className="w-16 h-16 rounded-2xl bg-sky-500/20 border border-sky-400/40 flex items-center justify-center text-sky-400 mb-3 shadow-lg shadow-sky-500/30">
            <FileText className="w-8 h-8 animate-pulse" />
          </div>
          <div className="text-base font-semibold text-white">
            {userSettings?.language === "en" ? "Drop Document for Offline RAG" : "أفلِت المستند هنا للفهرسة والسؤال الذكي"}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {userSettings?.language === "en"
              ? "Supports PDF, DOCX, TXT, MD, Code • 100% Local SQLite FTS5"
              : "يدعم PDF و Word DOCX والشفرات البرمجية • خصوصية محلية 100% دون سحاب"}
          </div>
        </div>
      )}
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
            <button
              onClick={() => setIsSettingsOpen(true)}
              title="Shortcut to summon Aegis AI (Click to change in Settings)"
              className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 font-semibold border border-sky-500/30 hover:bg-sky-500/30 hover:border-sky-400 transition whitespace-nowrap cursor-pointer"
            >
              {userSettings?.global_hotkey || "Alt+Space"}
            </button>
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
            onClick={toggleHandsFree}
            className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs font-mono transition border ${
              isHandsFree
                ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-300 shadow-sm shadow-emerald-500/20"
                : "bg-slate-800 border-slate-700/60 text-slate-400 hover:text-slate-200"
            }`}
            title={
              isHandsFree
                ? "وضع الاستماع الحر نشط: تحدث مباشرة دون فتح أو إغلاق المايك يدويًا (انقر للإيقاف)"
                : "تفعيل الاستماع الحر (Hands-Free): تحدث في أي وقت دون الحاجة لفتح المايك"
            }
          >
            <Headphones className={`w-3.5 h-3.5 ${isHandsFree ? "text-emerald-400 animate-pulse" : ""}`} />
            <span className="text-[11px]">
              {isHandsFree ? "Hands-Free ON" : "Hands-Free"}
            </span>
          </button>

          {/* Global Media Playback Mini-Controls */}
          <div className="flex items-center gap-0.5 bg-slate-800/80 border border-slate-700/60 rounded-lg p-0.5" title="Media Playback Controls">
            <button
              onClick={() => handleMediaAction("previous")}
              className="p-1 rounded text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 transition"
              title={userSettings?.language === "en" ? "Previous Track" : "المقطع السابق"}
            >
              <SkipBack className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => handleMediaAction("play_pause")}
              className="p-1 rounded text-sky-400 hover:text-sky-300 hover:bg-sky-500/20 transition"
              title={userSettings?.language === "en" ? "Play / Pause" : "تشغيل / إيقاف مؤقت"}
            >
              <Play className="w-3.5 h-3.5 fill-current" />
            </button>
            <button
              onClick={() => handleMediaAction("next")}
              className="p-1 rounded text-slate-400 hover:text-slate-100 hover:bg-slate-700/60 transition"
              title={userSettings?.language === "en" ? "Next Track" : "المقطع التالي"}
            >
              <SkipForward className="w-3.5 h-3.5" />
            </button>
          </div>

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
            onClick={() => setIsSettingsOpen(true)}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700/60 text-slate-300 hover:text-white transition"
            title="Personalization & Settings (الإعدادات والتخصيص)"
          >
            <SettingsIcon className="w-3.5 h-3.5" />
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
              {quickActionsToRender.map((act) => (
                <button
                  key={act.id}
                  onClick={() => handleQuickAction(act.command)}
                  className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-800/50 hover:bg-slate-800 text-xs text-slate-300 border border-slate-700/50 transition text-left group"
                >
                  {renderQuickActionIcon(act.icon)}
                  <span className="truncate">{act.title}</span>
                </button>
              ))}
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
        {/* Active Timers Pill */}
        {activeReminders.length > 0 && (
          <div className="mb-2 px-3 py-1.5 rounded-xl bg-amber-950/50 border border-amber-500/40 flex items-center justify-between gap-2 text-xs text-amber-200 animate-in fade-in duration-200">
            <div className="flex items-center gap-2 truncate">
              <Clock className="w-3.5 h-3.5 text-amber-400 shrink-0 animate-spin" style={{ animationDuration: "8s" }} />
              <span className="font-medium truncate">{activeReminders[0].title}</span>
              <span className="font-mono text-amber-300 font-bold bg-amber-900/60 px-1.5 py-0.5 rounded text-[11px] shrink-0">
                {formatCountdown(activeReminders[0].remaining_seconds || 0)}
              </span>
            </div>
            <button
              type="button"
              onClick={() => handleCancelReminder(activeReminders[0].id)}
              className="p-1 hover:text-rose-400 text-slate-400 transition rounded"
              title="Cancel timer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}
        {/* Active Document Pill */}
        {activeDocument && (
          <div className="mb-2 px-3 py-1.5 rounded-xl bg-sky-950/60 border border-sky-500/40 flex items-center justify-between gap-2 text-xs text-sky-200">
            <div className="flex items-center gap-2 truncate">
              <FileText className="w-3.5 h-3.5 text-sky-400 shrink-0" />
              <span className="font-medium truncate">{activeDocument.filename}</span>
              <span className="text-[10px] text-sky-400/80 bg-sky-900/50 px-1.5 py-0.5 rounded-md font-mono shrink-0">
                {activeDocument.chunk_count} {userSettings?.language === "en" ? "chunks" : "فقرة"}
              </span>
              <span className="text-[10px] text-slate-400 shrink-0">
                {(activeDocument.file_size / 1024).toFixed(1)} KB
              </span>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              <button
                type="button"
                onClick={() => {
                  const q = userSettings?.language === "en" ? "Summarize document" : "لخص المستند المرفق";
                  setInput(q);
                  sendMessage(q);
                }}
                className="px-2 py-0.5 rounded-md bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 hover:text-white transition text-[11px]"
              >
                {userSettings?.language === "en" ? "Summarize" : "لخص المستند"}
              </button>
              <button
                type="button"
                onClick={() => setActiveDocument(null)}
                className="p-1 hover:text-rose-400 text-slate-400 transition rounded"
                title="Detach document"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}

        {voiceNotice && (
          <div className="mb-2 px-3 py-1.5 rounded-lg bg-sky-950/80 border border-sky-500/40 text-xs text-sky-200 flex items-center justify-between">
            <span>{voiceNotice}</span>
            <button onClick={() => setVoiceNotice(null)} className="text-sky-400 hover:text-white">✕</button>
          </div>
        )}

        {isRecording && (
          <div className="mb-2 px-3 py-1 rounded-md bg-slate-800/80 border border-rose-500/40 text-xs text-rose-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
            <span className="font-mono text-[11px]">
              {isSpeaking ? "🎤 جاري التقاط صوتك..." : (isHandsFree ? "🎧 مستمع حر... تحدث في أي وقت" : "جاري الاستماع...")}
            </span>
            <div className="flex-1 h-1.5 bg-slate-950 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-400 via-sky-400 to-rose-400 transition-all duration-75"
                style={{ width: `${Math.min(100, Math.max(6, audioLevel * 300))}%` }}
              />
            </div>
          </div>
        )}

        {isTranscribing && (
          <div className="mb-2 px-3 py-1 rounded-md bg-amber-950/60 border border-amber-500/40 text-xs text-amber-300 flex items-center gap-2 animate-pulse">
            <Activity className="w-3.5 h-3.5 animate-spin" />
            <span>⚡ جاري تحويل الصوت إلى نص...</span>
          </div>
        )}

        <div className="flex items-center gap-2 p-1.5 rounded-2xl bg-slate-800/80 border border-slate-700/80 focus-within:border-sky-500/60 focus-within:ring-2 focus-within:ring-sky-500/20 transition-all">
          {/* Hidden File Input for Paperclip */}
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".pdf,.docx,.txt,.md,.py,.json,.csv,.log,.rs,.ts,.js,.html"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFileUpload(e.target.files[0]);
                e.target.value = "";
              }
            }}
          />
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

          {/* Local Document RAG Attachment Button */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploadingDoc || isStreaming}
            className="p-2 rounded-xl bg-slate-700/60 hover:bg-sky-500/20 text-slate-300 hover:text-sky-300 transition relative"
            title={
              userSettings?.language === "en"
                ? "Attach & Query Document (Drag & Drop Local RAG)"
                : "إرفاق وسؤال مستند محلي (Drag & Drop Local RAG)"
            }
          >
            {isUploadingDoc ? (
              <Loader2 className="w-4 h-4 text-sky-400 animate-spin" />
            ) : (
              <Paperclip className="w-4 h-4" />
            )}
          </button>

          {/* Ask My Screen / Vision AI Button */}
          <button
            type="button"
            onClick={() => {
              const query = userSettings?.language === "en" ? "Analyze what is on my screen" : "حلل ما يظهر على الشاشة واشرح أهم ما تراه";
              setInput(query);
              sendMessage(query);
            }}
            disabled={isStreaming || isTranscribing}
            className="p-2 rounded-xl bg-slate-700/60 hover:bg-sky-500/20 text-slate-300 hover:text-sky-300 transition"
            title={userSettings?.language === "en" ? "Ask My Screen (Vision AI)" : "تحليل ما يظهر على الشاشة الذكي (Ask My Screen)"}
          >
            <Eye className="w-4 h-4" />
          </button>

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

      {/* Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={userSettings}
        onSettingsUpdated={setUserSettings}
        sessionId={sessionId}
        onClearChat={clearMessages}
      />
    </div>
  );
};
