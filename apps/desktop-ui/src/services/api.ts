import { AIRuntimeStatus, SystemTelemetry, VoiceStatus } from "../types";

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

