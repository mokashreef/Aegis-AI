import { AIRuntimeStatus, PullProgress, SystemTelemetry, VoiceStatus } from "../types";

const API_BASE = "http://127.0.0.1:8420/api";

export async function fetchSystemStatus(): Promise<{
  telemetry: SystemTelemetry;
  ai_runtime: AIRuntimeStatus;
  voice: VoiceStatus;
  version: string;
}> {
  const response = await fetch(`${API_BASE}/system/status`);
  if (!response.ok) {
    throw new Error(`Failed to fetch system status: ${response.statusText}`);
  }
  return response.json();
}

export async function executeToolDirectly(
  toolName: string,
  args: Record<string, unknown>,
  confirmed = false
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  const response = await fetch(`${API_BASE}/tools/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tool_name: toolName,
      arguments: args,
      user_confirmed: confirmed,
    }),
  });
  return response.json();
}

export async function triggerVoiceSpeech(text: string): Promise<boolean> {
  const response = await fetch(`${API_BASE}/voice/speak`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  const data = await response.json();
  return Boolean(data.success);
}

export async function startOllamaServer(): Promise<{ started: boolean; installed: boolean }> {
  const response = await fetch(`${API_BASE}/ollama/start`, {
    method: "POST",
  });
  return response.json();
}

export async function pullModelStream(
  modelName: string,
  onProgress: (progress: PullProgress) => void
): Promise<void> {
  const response = await fetch(`${API_BASE}/models/pull`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: modelName }),
  });

  if (!response.ok || !response.body) {
    throw new Error(`Failed to initiate pull: ${response.statusText}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          onProgress(data);
        } catch {
          // Ignore partial frames
        }
      }
    }
  }
}
