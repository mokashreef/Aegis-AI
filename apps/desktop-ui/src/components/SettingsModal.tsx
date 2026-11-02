import React, { useState, useEffect } from "react";
import {
  X,
  Settings as SettingsIcon,
  Palette,
  Volume2,
  Sliders,
  Database,
  Play,
  Square,
  Check,
  Globe,
  Plus,
  Trash2,
  RotateCcw,
  Keyboard,
} from "lucide-react";
import { UserSettings, VoiceCatalogItem, QuickActionItem } from "../types";
import {
  fetchVoiceCatalog,
  playVoicePreview,
  updateSettings,
  clearSessionHistory,
} from "../services/api";

const DEFAULT_FALLBACK_SETTINGS: UserSettings = {
  theme: "dark",
  language: "auto",
  auto_speak: false,
  tts_voice: "ar-SA-HamedNeural",
  tts_rate: "0%",
  default_browser: "chrome",
  global_hotkey: "Alt+Space",
  start_with_windows: true,
  quick_actions: [],
};

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: UserSettings | null;
  onSettingsUpdated: (newSettings: UserSettings) => void;
  sessionId: string;
  onClearChat: () => void;
}

type TabType = "general" | "voice" | "actions" | "system";

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onSettingsUpdated,
  sessionId,
  onClearChat,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>("general");
  const [voices, setVoices] = useState<VoiceCatalogItem[]>([]);
  const [localSettings, setLocalSettings] = useState<UserSettings>(settings || DEFAULT_FALLBACK_SETTINGS);
  const [isPlayingPreview, setIsPlayingPreview] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [newActionTitle, setNewActionTitle] = useState("");
  const [newActionCommand, setNewActionCommand] = useState("");
  const [showAddAction, setShowAddAction] = useState(false);
  const [clearSuccess, setClearSuccess] = useState(false);
  const [isRecordingHotkey, setIsRecordingHotkey] = useState(false);
  const [hotkeySavedNotice, setHotkeySavedNotice] = useState(false);

  const handleRecordKeyDown = (e: React.KeyboardEvent) => {
    e.preventDefault();
    e.stopPropagation();

    // Ignore standalone modifier presses
    if (["Control", "Alt", "Shift", "Meta"].includes(e.key)) {
      return;
    }

    const modifiers: string[] = [];
    if (e.ctrlKey) modifiers.push("Ctrl");
    if (e.altKey) modifiers.push("Alt");
    if (e.shiftKey) modifiers.push("Shift");
    if (e.metaKey) modifiers.push("Win");

    let keyName = e.key;
    if (keyName === " ") keyName = "Space";
    else if (keyName.length === 1) keyName = keyName.toUpperCase();

    const formatted = modifiers.length > 0 ? `${modifiers.join("+")}+${keyName}` : keyName;
    handleSaveField("global_hotkey", formatted);
    setIsRecordingHotkey(false);
    setHotkeySavedNotice(true);
    setTimeout(() => setHotkeySavedNotice(false), 3000);
  };

  useEffect(() => {
    if (settings) setLocalSettings(settings);
  }, [settings]);

  useEffect(() => {
    if (isOpen) {
      fetchVoiceCatalog()
        .then(setVoices)
        .catch((err) => console.error("Failed fetching voice catalog:", err));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSaveField = async <K extends keyof UserSettings>(
    key: K,
    val: UserSettings[K]
  ) => {
    const updated = { ...localSettings, [key]: val };
    setLocalSettings(updated);
    setIsSaving(true);
    try {
      const saved = await updateSettings({ [key]: val });
      onSettingsUpdated(saved);
    } catch (err) {
      console.error(`Failed saving setting ${String(key)}:`, err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestVoice = async (voiceId: string) => {
    try {
      setIsPlayingPreview(voiceId);
      await playVoicePreview(voiceId, localSettings.tts_rate);
    } catch (err) {
      console.error("Failed playing preview:", err);
    } finally {
      setIsPlayingPreview(null);
    }
  };

  const handleToggleAction = async (actionId: string) => {
    const updatedActions = localSettings.quick_actions.map((act) =>
      act.id === actionId ? { ...act, enabled: !act.enabled } : act
    );
    await handleSaveField("quick_actions", updatedActions);
  };

  const handleAddAction = async () => {
    if (!newActionTitle.trim() || !newActionCommand.trim()) return;
    const newAct: QuickActionItem = {
      id: "act_" + Date.now(),
      title: newActionTitle.trim(),
      title_ar: newActionTitle.trim(),
      command: newActionCommand.trim(),
      icon: "app",
      enabled: true,
    };
    const updated = [...localSettings.quick_actions, newAct];
    await handleSaveField("quick_actions", updated);
    setNewActionTitle("");
    setNewActionCommand("");
    setShowAddAction(false);
  };

  const handleDeleteAction = async (actionId: string) => {
    const updated = localSettings.quick_actions.filter((a) => a.id !== actionId);
    await handleSaveField("quick_actions", updated);
  };

  const handleClearHistory = async () => {
    if (!window.confirm("هل أنت متأكد من مسح جميع رسائل الجلسة الحالية؟")) return;
    try {
      await clearSessionHistory(sessionId);
      onClearChat();
      setClearSuccess(true);
      setTimeout(() => setClearSuccess(false), 2500);
    } catch (err) {
      console.error("Failed clearing history:", err);
    }
  };

  const isLight = localSettings.theme === "light";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm select-none">
      <div
        className={`w-full max-w-2xl rounded-2xl border shadow-2xl flex flex-col h-[540px] overflow-hidden transition-colors ${
          isLight
            ? "bg-white border-slate-200 text-slate-800"
            : "bg-[#0f172a] border-slate-800 text-slate-100"
        }`}
      >
        {/* Header */}
        <div
          className={`flex items-center justify-between px-5 py-3.5 border-b shrink-0 ${
            isLight ? "bg-slate-50 border-slate-200" : "bg-slate-900 border-slate-800"
          }`}
        >
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-sky-500/15 text-sky-400 border border-sky-500/30">
              <SettingsIcon className="w-4 h-4" />
            </div>
            <div>
              <h2 className="font-bold text-sm tracking-wide">
                {localSettings.language === "ar" ? "إعدادات وتخصيص Aegis AI" : "Settings & Customization"}
              </h2>
              <p className="text-[11px] text-slate-400 font-mono">
                {isSaving ? "Saving changes..." : "Personalize voice, theme & actions"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className={`p-1.5 rounded-lg transition ${
              isLight ? "hover:bg-slate-200 text-slate-500" : "hover:bg-slate-800 text-slate-400"
            }`}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div
          className={`flex items-center gap-1 px-4 py-2 border-b shrink-0 ${
            isLight ? "bg-slate-100/70 border-slate-200" : "bg-slate-950/60 border-slate-800/80"
          }`}
        >
          <button
            onClick={() => setActiveTab("general")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              activeTab === "general"
                ? "bg-sky-500 text-white shadow-sm"
                : isLight
                ? "text-slate-600 hover:bg-slate-200"
                : "text-slate-400 hover:bg-slate-800"
            }`}
          >
            <Palette className="w-3.5 h-3.5" />
            <span>{localSettings.language === "ar" ? "عام والمظهر" : "General & Theme"}</span>
          </button>

          <button
            onClick={() => setActiveTab("voice")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              activeTab === "voice"
                ? "bg-sky-500 text-white shadow-sm"
                : isLight
                ? "text-slate-600 hover:bg-slate-200"
                : "text-slate-400 hover:bg-slate-800"
            }`}
          >
            <Volume2 className="w-3.5 h-3.5" />
            <span>{localSettings.language === "ar" ? "الصوت والتحدث" : "Voice & Speech"}</span>
          </button>

          <button
            onClick={() => setActiveTab("actions")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              activeTab === "actions"
                ? "bg-sky-500 text-white shadow-sm"
                : isLight
                ? "text-slate-600 hover:bg-slate-200"
                : "text-slate-400 hover:bg-slate-800"
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>{localSettings.language === "ar" ? "الشاشة الرئيسية" : "Quick Actions"}</span>
          </button>

          <button
            onClick={() => setActiveTab("system")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
              activeTab === "system"
                ? "bg-sky-500 text-white shadow-sm"
                : isLight
                ? "text-slate-600 hover:bg-slate-200"
                : "text-slate-400 hover:bg-slate-800"
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>{localSettings.language === "ar" ? "النظام والبيانات" : "System & Data"}</span>
          </button>
        </div>

        {/* Tab Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* TAB 1: GENERAL */}
          {activeTab === "general" && (
            <div className="space-y-4">
              {/* Language Lock */}
              <div
                className={`p-4 rounded-xl border ${
                  isLight ? "bg-slate-50 border-slate-200" : "bg-slate-900/60 border-slate-800"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-sky-400">
                      {localSettings.language === "ar" ? "لغة الرد الإلزامية (Language Lock)" : "Response Language Lock"}
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {localSettings.language === "ar"
                        ? "تحديد لغة الإجابة دائماً بغض النظر عن اللغة التي تكتب بها"
                        : "Force Aegis to always formulate replies in this language"}
                    </p>
                  </div>
                  <Globe className="w-4 h-4 text-sky-400" />
                </div>
                <div className="grid grid-cols-3 gap-2 mt-3">
                  {[
                    { id: "auto", label: "تلقائي (Auto)", desc: "حسب لغة المستخدم" },
                    { id: "ar", label: "العربية (دائماً)", desc: "يرد دائماً بالعربية" },
                    { id: "en", label: "English (Always)", desc: "Always in English" },
                  ].map((opt) => (
                    <button
                      key={opt.id}
                      onClick={() => handleSaveField("language", opt.id as "auto" | "ar" | "en")}
                      className={`p-2.5 rounded-xl border text-left transition ${
                        localSettings.language === opt.id
                          ? "bg-sky-500/20 border-sky-500 text-sky-300 font-bold"
                          : isLight
                          ? "bg-white border-slate-200 text-slate-700 hover:bg-slate-100"
                          : "bg-slate-800/80 border-slate-700/60 text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <div className="text-xs">{opt.label}</div>
                      <div className="text-[10px] text-slate-400 font-mono mt-0.5">{opt.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Theme Mode */}
              <div
                className={`p-4 rounded-xl border ${
                  isLight ? "bg-slate-50 border-slate-200" : "bg-slate-900/60 border-slate-800"
                }`}
              >
                <h3 className="text-xs font-bold uppercase tracking-wider text-sky-400 mb-1">
                  {localSettings.language === "ar" ? "مظهر الواجهة (Theme Mode)" : "Appearance Theme"}
                </h3>
                <p className="text-xs text-slate-400 mb-3">
                  {localSettings.language === "ar"
                    ? "التبديل بين الوضع الليلي المريح أو النهاري الواضح"
                    : "Switch between Dark, Light, or OS System appearance"}
                </p>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: "dark", label: "مظلم (Dark)", icon: "🌙" },
                    { id: "light", label: "فاتح (Light)", icon: "☀️" },
                    { id: "system", label: "تلقائي (System)", icon: "💻" },
                  ].map((t) => (
                    <button
                      key={t.id}
                      onClick={() => handleSaveField("theme", t.id as "dark" | "light" | "system")}
                      className={`p-2.5 rounded-xl border flex items-center justify-center gap-2 text-xs transition ${
                        localSettings.theme === t.id
                          ? "bg-sky-500/20 border-sky-500 text-sky-300 font-bold"
                          : isLight
                          ? "bg-white border-slate-200 text-slate-700 hover:bg-slate-100"
                          : "bg-slate-800/80 border-slate-700/60 text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <span>{t.icon}</span>
                      <span>{t.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Default Browser */}
              <div
                className={`p-4 rounded-xl border ${
                  isLight ? "bg-slate-50 border-slate-200" : "bg-slate-900/60 border-slate-800"
                }`}
              >
                <h3 className="text-xs font-bold uppercase tracking-wider text-sky-400 mb-1">
                  {localSettings.language === "ar" ? "المتصفح الافتراضي للمواقع" : "Preferred Web Browser"}
                </h3>
                <p className="text-xs text-slate-400 mb-3">
                  {localSettings.language === "ar"
                    ? "المتصفح الذي سيُفتح تلقائياً عند طلب فتح المواقع بدون تحديد اسم المتصفح"
                    : "Browser to launch when opening links or websites without specifying a browser"}
                </p>
                <select
                  value={localSettings.default_browser}
                  onChange={(e) =>
                    handleSaveField(
                      "default_browser",
                      e.target.value as "chrome" | "comet" | "msedge" | "brave" | "firefox" | "default"
                    )
                  }
                  className={`w-full p-2.5 rounded-xl text-xs border outline-none font-medium ${
                    isLight
                      ? "bg-white border-slate-300 text-slate-800"
                      : "bg-slate-800 border-slate-700 text-slate-200"
                  }`}
                >
                  <option value="chrome">Google Chrome (جوجل كروم)</option>
                  <option value="comet">Comet (متصفح كومت)</option>
                  <option value="msedge">Microsoft Edge (مايكروسوفت إيدج)</option>
                  <option value="brave">Brave Browser (بريف)</option>
                  <option value="firefox">Mozilla Firefox (فايرفوكس)</option>
                  <option value="default">Default System Browser (متصفح النظام الافتراضي)</option>
                </select>
              </div>

              {/* Start with Windows */}
              <div
                className={`p-4 rounded-xl border flex items-center justify-between ${
                  isLight ? "bg-slate-50 border-slate-200" : "bg-slate-900/60 border-slate-800"
                }`}
              >
                <div>
                  <h3 className="text-xs font-bold text-slate-200">
                    {localSettings.language === "ar" ? "البدء التلقائي مع ويندوز" : "Launch on Windows Startup"}
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {localSettings.language === "ar"
                      ? "تشغيل التطبيق في الخلفية صامتاً في شريط المهام عند إقلاع الجهاز"
                      : "Start Aegis AI minimized to system tray when logging into Windows"}
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={localSettings.start_with_windows}
                  onChange={(e) => handleSaveField("start_with_windows", e.target.checked)}
                  className="w-4 h-4 rounded text-sky-500 cursor-pointer"
                />
              </div>
            </div>
          )}

          {/* TAB 2: VOICE & SPEECH */}
          {activeTab === "voice" && (
            <div className="space-y-4">
              {/* Auto Speak Toggle */}
              <div
                className={`p-4 rounded-xl border flex items-center justify-between ${
                  isLight ? "bg-slate-50 border-slate-200" : "bg-slate-900/60 border-slate-800"
                }`}
              >
                <div>
                  <h3 className="text-xs font-bold text-slate-200 flex items-center gap-2">
                    <Volume2 className="w-4 h-4 text-sky-400" />
                    <span>{localSettings.language === "ar" ? "الرد الصوتي التلقائي" : "Auto Voice Response"}</span>
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {localSettings.language === "ar"
                      ? "قراءة ردود وإجابات المساعد صوتياً بالكامل تلقائياً عند انتهاء الكتابة"
                      : "Automatically speak out AI responses using natural neural voice synthesis"}
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={localSettings.auto_speak}
                  onChange={(e) => handleSaveField("auto_speak", e.target.checked)}
                  className="w-4 h-4 rounded text-sky-500 cursor-pointer"
                />
              </div>

              {/* Speech Speed Slider */}
              <div
                className={`p-4 rounded-xl border ${
                  isLight ? "bg-slate-50 border-slate-200" : "bg-slate-900/60 border-slate-800"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs font-bold text-slate-200">
                    {localSettings.language === "ar" ? "سرعة التحدث (Speech Rate)" : "Speech Rate Speed"}
                  </h3>
                  <span className="text-xs font-mono text-sky-400 font-bold">{localSettings.tts_rate}</span>
                </div>
                <div className="grid grid-cols-4 gap-2 mt-2">
                  {[
                    { val: "-15%", label: "هادئ (-15%)" },
                    { val: "+0%", label: "طبيعي (0%)" },
                    { val: "+15%", label: "سريع (+15%)" },
                    { val: "+30%", label: "أسرع (+30%)" },
                  ].map((r) => (
                    <button
                      key={r.val}
                      onClick={() => handleSaveField("tts_rate", r.val)}
                      className={`p-2 rounded-lg text-xs border transition ${
                        localSettings.tts_rate === r.val
                          ? "bg-sky-500/20 border-sky-500 text-sky-300 font-bold"
                          : isLight
                          ? "bg-white border-slate-200 text-slate-700"
                          : "bg-slate-800 border-slate-700 text-slate-400"
                      }`}
                    >
                      {r.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Voice Catalog Selector */}
              <div
                className={`p-4 rounded-xl border ${
                  isLight ? "bg-slate-50 border-slate-200" : "bg-slate-900/60 border-slate-800"
                }`}
              >
                <h3 className="text-xs font-bold uppercase tracking-wider text-sky-400 mb-1">
                  {localSettings.language === "ar" ? "اختيار الصوت العصبي المفضل" : "Select Active Neural Voice"}
                </h3>
                <p className="text-xs text-slate-400 mb-3">
                  {localSettings.language === "ar"
                    ? "اختر الصوت المفضل واضغط على زر الاستماع لتجربة العينة الصوتية مباشرة"
                    : "Select your preferred neural voice. Click the play button to preview live audio"}
                </p>

                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {voices.map((voice) => {
                    const isSelected = localSettings.tts_voice === voice.id;
                    const isPlaying = isPlayingPreview === voice.id;
                    const isArabic = voice.lang.startsWith("ar");

                    return (
                      <div
                        key={voice.id}
                        className={`flex items-center justify-between p-2.5 rounded-xl border transition ${
                          isSelected
                            ? "bg-sky-500/15 border-sky-500/50"
                            : isLight
                            ? "bg-white border-slate-200 hover:bg-slate-50"
                            : "bg-slate-800/60 border-slate-700/50 hover:bg-slate-800"
                        }`}
                      >
                        <div
                          className="flex-1 cursor-pointer"
                          onClick={() => handleSaveField("tts_voice", voice.id)}
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-slate-200">
                              {localSettings.language === "ar" ? voice.name : voice.name_en}
                            </span>
                            <span
                              className={`text-[9px] px-1.5 py-0.5 rounded font-mono ${
                                isArabic ? "bg-emerald-500/20 text-emerald-300" : "bg-sky-500/20 text-sky-300"
                              }`}
                            >
                              {voice.gender === "Male" ? "ذكوري" : "أنثوي"}
                            </span>
                          </div>
                          <p className="text-[10px] text-slate-400 font-mono mt-0.5">{voice.lang_name}</p>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleTestVoice(voice.id)}
                            disabled={isPlaying}
                            className={`p-1.5 rounded-lg border text-xs flex items-center gap-1 transition ${
                              isPlaying
                                ? "bg-amber-500/20 border-amber-500 text-amber-300 animate-pulse"
                                : isLight
                                ? "bg-slate-100 hover:bg-slate-200 border-slate-300 text-slate-700"
                                : "bg-slate-700 hover:bg-slate-600 border-slate-600 text-slate-200"
                            }`}
                            title="Play sample preview"
                          >
                            {isPlaying ? <Square className="w-3.5 h-3.5 fill-current" /> : <Play className="w-3.5 h-3.5 fill-current" />}
                            <span className="text-[10px]">{isPlaying ? "تشغيل..." : "تجربة"}</span>
                          </button>

                          <button
                            onClick={() => handleSaveField("tts_voice", voice.id)}
                            className={`p-1.5 rounded-lg border text-xs transition ${
                              isSelected
                                ? "bg-sky-500 border-sky-400 text-white"
                                : isLight
                                ? "bg-white border-slate-200 text-slate-400 hover:text-slate-600"
                                : "bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200"
                            }`}
                            title={isSelected ? "Selected" : "Select voice"}
                          >
                            <Check className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: QUICK ACTIONS */}
          {activeTab === "actions" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-sky-400">
                    {localSettings.language === "ar" ? "أزرار الشاشة الرئيسية الافتراضية" : "Welcome Quick Actions"}
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {localSettings.language === "ar"
                      ? "اختر الأزرار التي تظهر عند فتح الواجهة أو أضف اختصاراتك الخاصة"
                      : "Toggle or add shortcuts shown on the initial welcome companion screen"}
                  </p>
                </div>
                <button
                  onClick={() => setShowAddAction(!showAddAction)}
                  className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-sky-500 hover:bg-sky-400 text-white text-xs font-medium transition"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>{localSettings.language === "ar" ? "إضافة اختصار" : "Add Action"}</span>
                </button>
              </div>

              {/* Add Custom Action Form */}
              {showAddAction && (
                <div
                  className={`p-4 rounded-xl border space-y-3 ${
                    isLight ? "bg-sky-50 border-sky-200" : "bg-sky-950/20 border-sky-800/40"
                  }`}
                >
                  <h4 className="text-xs font-bold text-sky-300">
                    {localSettings.language === "ar" ? "إضافة بطاقة سريعة جديدة" : "Add New Quick Action"}
                  </h4>
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="text"
                      placeholder={localSettings.language === "ar" ? "عنوان الزر (مثال: فتح تيليجرام)" : "Title (e.g. Open Telegram)"}
                      value={newActionTitle}
                      onChange={(e) => setNewActionTitle(e.target.value)}
                      className={`p-2 rounded-lg text-xs border outline-none ${
                        isLight ? "bg-white border-slate-300 text-slate-800" : "bg-slate-900 border-slate-700 text-slate-200"
                      }`}
                    />
                    <input
                      type="text"
                      placeholder={localSettings.language === "ar" ? "الأمر المطلوب تنفيذه" : "Voice/Command to execute"}
                      value={newActionCommand}
                      onChange={(e) => setNewActionCommand(e.target.value)}
                      className={`p-2 rounded-lg text-xs border outline-none ${
                        isLight ? "bg-white border-slate-300 text-slate-800" : "bg-slate-900 border-slate-700 text-slate-200"
                      }`}
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => setShowAddAction(false)}
                      className="px-3 py-1 rounded-lg text-xs text-slate-400 hover:text-slate-200"
                    >
                      إلغاء
                    </button>
                    <button
                      onClick={handleAddAction}
                      className="px-3 py-1 rounded-lg text-xs bg-sky-500 hover:bg-sky-400 text-white font-medium"
                    >
                      حفظ الاختصار
                    </button>
                  </div>
                </div>
              )}

              {/* Actions List */}
              <div className="space-y-2">
                {localSettings.quick_actions.map((act) => (
                  <div
                    key={act.id}
                    className={`flex items-center justify-between p-3 rounded-xl border transition ${
                      act.enabled
                        ? isLight
                          ? "bg-white border-slate-200"
                          : "bg-slate-900/60 border-slate-800"
                        : "opacity-40 bg-slate-950/40 border-slate-800/40"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={act.enabled}
                        onChange={() => handleToggleAction(act.id)}
                        className="w-4 h-4 rounded text-sky-500 cursor-pointer"
                      />
                      <div>
                        <div className="text-xs font-semibold text-slate-200">
                          {localSettings.language === "ar" ? act.title_ar || act.title : act.title}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5">{act.command}</div>
                      </div>
                    </div>

                    <button
                      onClick={() => handleDeleteAction(act.id)}
                      className="p-1 rounded text-slate-400 hover:text-rose-400 transition"
                      title="Delete action"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 4: SYSTEM & DATA */}
          {activeTab === "system" && (
            <div className="space-y-4">
              {/* Customizable Global Hotkey */}
              <div
                className={`p-4 rounded-xl border space-y-3 ${
                  isLight ? "bg-slate-50 border-slate-200" : "bg-slate-900/60 border-slate-800"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Keyboard className="w-4 h-4 text-sky-400" />
                    <div>
                      <h3 className="text-xs font-bold uppercase tracking-wider text-sky-400">
                        {localSettings.language === "ar" ? "مفتاح الاختصار العام (Global Shortcut)" : "Global Summon Hotkey"}
                      </h3>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {localSettings.language === "ar"
                          ? "اختر الاختصار الذي يُظهر أو يُخفي التطبيق فورياً من أي نافذة"
                          : "Change the system-wide shortcut to summon/dismiss Aegis AI"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <kbd className="px-2.5 py-1 rounded bg-sky-500/20 border border-sky-500/40 text-sky-300 font-mono text-xs font-bold shadow-inner">
                      {localSettings.global_hotkey || "Alt+Space"}
                    </kbd>
                  </div>
                </div>

                {/* Preset Options Grid */}
                <div>
                  <div className="text-[11px] font-semibold text-slate-400 mb-1.5">
                    {localSettings.language === "ar" ? "اختصارات جاهزة وموصى بها:" : "Recommended Presets:"}
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                    {[
                      { id: "Alt+Space", label: "Alt + Space", desc: "Spotlight (الافتراضي)" },
                      { id: "Ctrl+Space", label: "Ctrl + Space", desc: "سريع ومألوف" },
                      { id: "Ctrl+Shift+A", label: "Ctrl + Shift + A", desc: "Aegis AI" },
                      { id: "Alt+Shift+A", label: "Alt + Shift + A", desc: "سهل الوصول" },
                      { id: "Ctrl+Alt+Space", label: "Ctrl + Alt + Space", desc: "ثلاثي فريد" },
                      { id: "F4", label: "F4", desc: "مفتاح وظيفي" },
                    ].map((hk) => {
                      const isSelected = (localSettings.global_hotkey || "Alt+Space") === hk.id;
                      return (
                        <button
                          key={hk.id}
                          onClick={() => {
                            handleSaveField("global_hotkey", hk.id);
                            setHotkeySavedNotice(true);
                            setTimeout(() => setHotkeySavedNotice(false), 3000);
                          }}
                          className={`p-2 rounded-lg border text-left transition ${
                            isSelected
                              ? "bg-sky-500/20 border-sky-500 text-sky-300 font-bold"
                              : isLight
                              ? "bg-white border-slate-200 text-slate-700 hover:bg-slate-100"
                              : "bg-slate-800/80 border-slate-700/60 text-slate-400 hover:text-slate-200"
                          }`}
                        >
                          <div className="text-xs font-mono">{hk.label}</div>
                          <div className="text-[10px] text-slate-400 truncate mt-0.5">{hk.desc}</div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Custom Shortcut Recorder */}
                <div
                  className={`p-3 rounded-lg border flex items-center justify-between gap-3 ${
                    isRecordingHotkey
                      ? "bg-sky-500/15 border-sky-500 animate-pulse"
                      : isLight
                      ? "bg-white border-slate-200"
                      : "bg-slate-950/40 border-slate-800"
                  }`}
                >
                  <div className="flex-1">
                    <div className="text-xs font-semibold text-slate-200">
                      {localSettings.language === "ar" ? "تسجيل اختصار مخصص:" : "Record Custom Shortcut:"}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      {isRecordingHotkey
                        ? localSettings.language === "ar"
                          ? "اضغط المفاتيح المطلوبة الآن معاً على لوحة المفاتيح..."
                          : "Press your desired key combination now..."
                        : localSettings.language === "ar"
                        ? "انقر لتسجيل أي تركيبة مفاتيح مخصصة تناسبك"
                        : "Click button and press your preferred keys"}
                    </div>
                  </div>

                  {isRecordingHotkey ? (
                    <input
                      type="text"
                      autoFocus
                      readOnly
                      onKeyDown={handleRecordKeyDown}
                      onBlur={() => setIsRecordingHotkey(false)}
                      placeholder={localSettings.language === "ar" ? "اضغط المفاتيح..." : "Press keys..."}
                      className="px-3 py-1.5 rounded-lg text-xs font-mono font-bold bg-sky-950 border border-sky-500 text-sky-300 text-center outline-none animate-pulse w-36"
                    />
                  ) : (
                    <button
                      onClick={() => setIsRecordingHotkey(true)}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 transition"
                    >
                      {localSettings.language === "ar" ? "تسجيل اختصار" : "Record Shortcut"}
                    </button>
                  )}
                </div>

                {/* Instant Feedback Notice */}
                {hotkeySavedNotice && (
                  <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                    <Check className="w-3.5 h-3.5" />
                    <span>
                      {localSettings.language === "ar"
                        ? "تم تحديث الاختصار وتفعيله فوراً على نظام ويندوز!"
                        : "Shortcut updated and activated live across Windows!"}
                    </span>
                  </div>
                )}
              </div>

              {/* Clear History */}
              <div
                className={`p-4 rounded-xl border flex items-center justify-between ${
                  isLight ? "bg-rose-50 border-rose-200" : "bg-rose-950/20 border-rose-800/40"
                }`}
              >
                <div>
                  <h3 className="text-xs font-bold text-rose-300">
                    {localSettings.language === "ar" ? "مسح سجل المحادثة للجلسة الحالية" : "Clear Chat History"}
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {localSettings.language === "ar"
                      ? "حذف جميع الرسائل والعمليات السابقة وبدء شاشة نظيفة جديدة"
                      : "Permanently delete messages and tool cards for the active session"}
                  </p>
                </div>
                <button
                  onClick={handleClearHistory}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium transition"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  <span>{clearSuccess ? "تم المسح!" : localSettings.language === "ar" ? "مسح السجل" : "Clear History"}</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          className={`flex items-center justify-between px-5 py-3 border-t shrink-0 ${
            isLight ? "bg-slate-50 border-slate-200" : "bg-slate-900 border-slate-800"
          }`}
        >
          <span className="text-[11px] text-slate-400 font-mono">
            Aegis AI v0.2.0 • 100% Local & Zero Cloud Lock-in
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-sky-500 hover:bg-sky-400 text-white text-xs font-semibold transition"
          >
            {localSettings.language === "ar" ? "تم وحفظ" : "Done"}
          </button>
        </div>
      </div>
    </div>
  );
};
export default SettingsModal;
