import {
  AIRuntimeStatus,
  PullProgress,
  SystemTelemetry,
  VoiceStatus,
  WakeWordStatus,
  UserSettings,
  VoiceCatalogItem,
  InstallerStatus,
  DocumentItem,
  DocumentQueryResult,
} from "../types";

const API_BASE = "http://127.0.0.1:8420/api";

export async function fetchSystemStatus(): Promise<{
  telemetry: SystemTelemetry;
  ai_runtime: AIRuntimeStatus;
  voice: VoiceStatus;
  wake_word?: WakeWordStatus;
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

export async function triggerVoiceSpeech(
  text: string,
  voice?: string,
  rate?: string
): Promise<boolean> {
  const response = await fetch(`${API_BASE}/voice/speak`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice, rate }),
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

export async function fetchWakeWordStatus(): Promise<WakeWordStatus> {
  const response = await fetch(`${API_BASE}/voice/wakeword/status`);
  return response.json();
}

export async function toggleWakeWord(): Promise<WakeWordStatus> {
  const response = await fetch(`${API_BASE}/voice/wakeword/toggle`, { method: "POST" });
  return response.json();
}

export async function configureWakeWord(config: {
  wake_word?: string;
  confidence_threshold?: number;
}): Promise<WakeWordStatus> {
  const response = await fetch(`${API_BASE}/voice/wakeword/config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  return response.json();
}

export async function fetchSettings(): Promise<UserSettings> {
  const response = await fetch(`${API_BASE}/settings`);
  if (!response.ok) {
    throw new Error("Failed fetching user settings");
  }
  return response.json();
}

export async function updateSettings(settings: Partial<UserSettings>): Promise<UserSettings> {
  const response = await fetch(`${API_BASE}/settings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(settings),
  });
  if (!response.ok) {
    throw new Error("Failed updating user settings");
  }
  return response.json();
}

export async function fetchVoiceCatalog(): Promise<VoiceCatalogItem[]> {
  const response = await fetch(`${API_BASE}/voice/catalog`);
  if (!response.ok) {
    throw new Error("Failed fetching voice catalog");
  }
  return response.json();
}

let activePreviewAudio: HTMLAudioElement | null = null;

export async function playVoicePreview(voice: string, rate = "+0%", text?: string): Promise<void> {
  if (activePreviewAudio) {
    activePreviewAudio.pause();
    activePreviewAudio = null;
  }

  const response = await fetch(`${API_BASE}/voice/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ voice, rate, text }),
  });

  if (!response.ok) {
    throw new Error("Failed synthesizing voice preview");
  }

  const blob = await response.blob();
  const audioUrl = URL.createObjectURL(blob);
  const audio = new Audio(audioUrl);
  activePreviewAudio = audio;
  audio.onended = () => {
    URL.revokeObjectURL(audioUrl);
    activePreviewAudio = null;
  };
  await audio.play();
}

export async function clearSessionHistory(sessionId: string): Promise<boolean> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/clear`, {
    method: "POST",
  });
  return response.ok;
}

export async function fetchInstallerStatus(): Promise<InstallerStatus> {
  const response = await fetch(`${API_BASE}/desktop/installer/status`);
  if (!response.ok) {
    throw new Error("Failed fetching installer status");
  }
  return response.json();
}

export async function buildOneClickInstaller(): Promise<InstallerStatus> {
  const response = await fetch(`${API_BASE}/desktop/installer/build`, {
    method: "POST",
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Build failed" }));
    throw new Error(err.detail || "Failed to build installer");
  }
  return response.json();
}

export async function openInstallerFolder(): Promise<void> {
  await fetch(`${API_BASE}/desktop/installer/open-folder`, {
    method: "POST",
  });
}

export async function launchInstaller(): Promise<void> {
  await fetch(`${API_BASE}/desktop/installer/run`, {
    method: "POST",
  });
}


export async function uploadDocument(file: File): Promise<DocumentItem> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Failed to upload document");
  }

  const data = await response.json();
  return data.document || data;
}

export async function fetchDocuments(): Promise<DocumentItem[]> {
  const response = await fetch(`${API_BASE}/documents`);
  if (!response.ok) {
    throw new Error("Failed to fetch documents");
  }
  return response.json();
}

export async function deleteDocument(docId: string): Promise<boolean> {
  const response = await fetch(`${API_BASE}/documents/${docId}`, {
    method: "DELETE",
  });
  return response.ok;
}

export async function queryDocument(query: string, docId?: string): Promise<DocumentQueryResult> {
  const response = await fetch(`${API_BASE}/documents/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, doc_id: docId }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: "Query failed" }));
    throw new Error(err.detail || "Failed to query document");
  }
  return response.json();
}
