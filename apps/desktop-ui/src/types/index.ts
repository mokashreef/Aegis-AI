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

export interface AIRuntimeStatus {
  active_provider: string;
  ollama: {
    available: boolean;
    host: string;
    models: string[];
  };
  pollinations_fallback: {
    available: boolean;
    enabled: boolean;
  };
  zero_api_keys_enforced: boolean;
}

export interface VoiceStatus {
  enabled: boolean;
  state: "idle" | "listening" | "transcribing" | "speaking";
  whisper_model: string;
  piper_voice: string;
}
