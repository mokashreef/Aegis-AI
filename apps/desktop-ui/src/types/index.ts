export type MessageRole = "system" | "user" | "assistant" | "tool";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  model?: string;
  provider?: string;
  toolCalls?: Array<{
    name: string;
    arguments: Record<string, unknown>;
  }>;
}

export interface ToolActivity {
  toolName: string;
  arguments: Record<string, unknown>;
  status: "pending" | "success" | "error" | "requires_confirmation";
  result?: Record<string, unknown>;
}

export interface SystemTelemetry {
  os: {
    system: string;
    release: string;
    version: string;
    architecture: string;
  };
  cpu: {
    physical_cores: number;
    logical_cores: number;
    usage_percent: number;
  };
  memory: {
    total_gb: number;
    available_gb: number;
    percent_used: number;
  };
  disk: {
    total_gb: number;
    free_gb: number;
    percent_used: number;
  };
}

export interface RecommendedModel {
  id: string;
  name: string;
  size_mb: number;
  description: string;
}

export interface OllamaHealth {
  server_running: boolean;
  installed_on_host: boolean;
  status: "ready" | "needs_model" | "offline";
  reason: string | null;
  models: string[];
  model_count: number;
  host: string;
  recommended_models: RecommendedModel[];
}

export interface AIRuntimeStatus {
  active_provider: string;
  tokens_per_second: number;
  ollama: OllamaHealth;
  pollinations_fallback: {
    available: boolean;
    enabled: boolean;
    notice: string;
  };
  zero_api_keys_enforced: boolean;
}

export interface VoiceStatus {
  enabled: boolean;
  state: "idle" | "listening" | "transcribing" | "speaking";
  whisper_model: string;
  piper_voice: string;
}

export interface PullProgress {
  status: string;
  digest?: string;
  total_bytes?: number;
  completed_bytes?: number;
  percent: number;
  model: string;
}

export interface WakeWordStatus {
  is_running: boolean;
  active_model: string;
  available_models: string[];
  confidence_threshold: number;
  cooldown_seconds: number;
  engine_initialized: boolean;
}

export interface QuickActionItem {
  id: string;
  title: string;
  title_ar: string;
  command: string;
  icon: "globe" | "app" | "camera" | "layers" | "terminal" | "volume" | "clipboard";
  enabled: boolean;
}

export interface VoiceCatalogItem {
  id: string;
  name: string;
  name_en: string;
  gender: "Male" | "Female";
  lang: string;
  lang_name: string;
  sample_text: string;
}

export interface PresetHotkey {
  id: string;
  label: string;
  desc_ar?: string;
}

export interface UserSettings {
  theme: "dark" | "light" | "system";
  language: "auto" | "ar" | "en";
  auto_speak: boolean;
  tts_voice: string;
  tts_rate: string;
  default_browser: "chrome" | "comet" | "msedge" | "brave" | "firefox" | "default";
  global_hotkey?: string;
  preset_hotkeys?: PresetHotkey[];
  start_with_windows: boolean;
  wake_word_enabled?: boolean;
  quick_actions: QuickActionItem[];
}

export interface InstallerStatus {
  available: boolean;
  version: string;
  file_name: string | null;
  file_path: string | null;
  size_bytes: number;
  size_mb: number;
  sha256: string | null;
  last_modified: string | null;
}


export interface DocumentItem {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  chunk_count: number;
  summary?: string;
  created_at: string;
}

export interface DocumentSource {
  page: number;
  chunk_index: number;
  snippet: string;
}

export interface DocumentQueryResult {
  success: boolean;
  query: string;
  answer: string;
  doc_id?: string;
  filename?: string;
  sources: DocumentSource[];
  chunks_retrieved?: number;
}


export interface ReminderItem {
  id: string;
  title: string;
  due_timestamp: number;
  due_time_str: string;
  duration_seconds: number;
  remind_type: "timer" | "reminder" | "alarm";
  status: "active" | "completed" | "cancelled";
  created_at: string;
  remaining_seconds?: number;
}
