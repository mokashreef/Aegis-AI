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
