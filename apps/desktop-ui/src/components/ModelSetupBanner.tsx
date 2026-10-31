import React, { useState } from "react";
import {
  Download,
  AlertCircle,
  CheckCircle2,
  Play,
  Loader2,
  Cpu,
  ExternalLink,
  Sparkles,
} from "lucide-react";
import { OllamaHealth, PullProgress, RecommendedModel } from "../types";
import { pullModelStream, startOllamaServer } from "../services/api";

interface ModelSetupBannerProps {
  ollama: OllamaHealth | null;
  onRefresh: () => void;
}

const DEFAULT_RECOMMENDED: RecommendedModel[] = [
  {
    id: "qwen2.5:1.5b",
    name: "Qwen 2.5 (1.5B)",
    size_mb: 986,
    description: "Ultra-fast CPU inference. Optimal for standard laptops & 8GB-16GB RAM.",
  },
  {
    id: "llama3.2:1b",
    name: "Llama 3.2 (1B)",
    size_mb: 1300,
    description: "Lightweight Meta architecture. Highly capable reasoning with low memory.",
  },
  {
    id: "llama3.2:3b",
    name: "Llama 3.2 (3B)",
    size_mb: 2000,
    description: "High-accuracy model for PCs with discrete GPU or 16GB+ RAM.",
  },
];

function formatBytes(bytes?: number): string {
  if (!bytes || bytes <= 0) return "";
  if (bytes >= 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const ModelSetupBanner: React.FC<ModelSetupBannerProps> = ({ ollama, onRefresh }) => {
  const [selectedModel, setSelectedModel] = useState<string>("qwen2.5:1.5b");
  const [isPulling, setIsPulling] = useState(false);
  const [pullProgress, setPullProgress] = useState<PullProgress | null>(null);
  const [isStartingServer, setIsStartingServer] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!ollama) return null;

  // If server is ready and already has at least one model, do not show wizard
  if (ollama.status === "ready" && ollama.models.length > 0) {
    return null;
  }

  const modelsList =
    ollama.recommended_models && ollama.recommended_models.length > 0
      ? ollama.recommended_models
      : DEFAULT_RECOMMENDED;

  const handlePull = async (modelId: string) => {
    setIsPulling(true);
    setErrorMsg(null);
    try {
      await pullModelStream(modelId, (prog) => {
        setPullProgress(prog);
        if (prog.status === "success") {
          setIsPulling(false);
          setTimeout(onRefresh, 1200);
        }
      });
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Failed to download model.");
      setIsPulling(false);
    }
  };

  const handleStartServer = async () => {
    setIsStartingServer(true);
    setErrorMsg(null);
    try {
      await startOllamaServer();
      setTimeout(onRefresh, 2000);
    } catch {
      setErrorMsg("Failed to start local Ollama server.");
    } finally {
      setIsStartingServer(false);
    }
  };

  const handleOpenOllamaWeb = () => {
    window.open("https://ollama.com/download", "_blank");
  };

  return (
    <div className="mx-5 my-3 p-4 rounded-3xl bg-gradient-to-br from-slate-900/90 via-slate-900/95 to-slate-950 border border-amber-500/30 text-slate-200 shadow-xl backdrop-blur-md">
      {/* Header Info */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-start gap-2.5">
          <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 shrink-0">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-amber-300">
                {ollama.status === "offline"
                  ? !ollama.installed_on_host
                    ? "Offline Intelligence Setup (Optional)"
                    : "Ollama Server Offline"
                  : "Local Model Download Wizard"}
              </h4>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20">
                Zero Cloud Lock-in
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1 max-w-xl leading-relaxed">
              {ollama.status === "offline"
                ? !ollama.installed_on_host
                  ? "Aegis AI is currently using anonymous fallback mode. For 100% offline air-gapped privacy on your local CPU/GPU, install Ollama."
                  : "Ollama is installed on your PC but not running. Start the service to enable offline models."
                : "Ollama is active, but no models are downloaded yet. Select a lightweight local model below for 1-click installation."}
            </p>
          </div>
        </div>

        {/* Action Controls for Offline/Missing State */}
        {ollama.status === "offline" && (
          <div className="shrink-0">
            {!ollama.installed_on_host ? (
              <button
                onClick={handleOpenOllamaWeb}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 text-xs font-bold transition shadow-md"
              >
                <ExternalLink className="w-3.5 h-3.5" />
                Get Ollama (ollama.com)
              </button>
            ) : (
              <button
                onClick={handleStartServer}
                disabled={isStartingServer}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition shadow-md"
              >
                {isStartingServer ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Play className="w-3.5 h-3.5 fill-current" />
                )}
                Start Ollama
              </button>
            )}
          </div>
        )}
      </div>

      {/* Model Selection Wizard Grid (Active when Ollama is running & models needed) */}
      {ollama.status === "needs_model" && !isPulling && (
        <div className="mt-3 pt-3 border-t border-slate-800">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 mb-3">
            {modelsList.map((model) => {
              const isSelected = selectedModel === model.id;
              return (
                <div
                  key={model.id}
                  onClick={() => setSelectedModel(model.id)}
                  className={`p-3 rounded-2xl cursor-pointer transition-all border text-left flex flex-col justify-between ${
                    isSelected
                      ? "bg-sky-500/10 border-sky-500/60 shadow-lg shadow-sky-500/10 ring-1 ring-sky-500/30"
                      : "bg-slate-800/40 border-slate-700/50 hover:bg-slate-800/80 hover:border-slate-600"
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-1.5">
                        <Cpu className={`w-3.5 h-3.5 ${isSelected ? "text-sky-400" : "text-slate-400"}`} />
                        <span className="text-xs font-bold text-slate-100">{model.name}</span>
                      </div>
                      <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                        {model.size_mb} MB
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-snug">{model.description}</p>
                  </div>

                  {model.id === "qwen2.5:1.5b" && (
                    <div className="mt-2 text-[10px] text-emerald-400 font-mono font-medium flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> Recommended for CPU
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          <div className="flex items-center justify-between pt-1">
            <span className="text-xs text-slate-400 font-mono">
              Selected: <strong className="text-slate-200">{selectedModel}</strong>
            </span>
            <button
              onClick={() => handlePull(selectedModel)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-sky-500 to-cyan-400 hover:from-sky-400 hover:to-cyan-300 text-slate-950 text-xs font-bold transition shadow-lg shadow-sky-500/25"
            >
              <Download className="w-4 h-4" />
              Download & Activate Model
            </button>
          </div>
        </div>
      )}

      {/* Live Pulling Progress Display */}
      {isPulling && pullProgress && (
        <div className="mt-3 pt-3 border-t border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-200 mb-1.5 font-mono">
            <div className="flex items-center gap-2">
              <Loader2 className="w-3.5 h-3.5 text-sky-400 animate-spin" />
              <span className="text-sky-300 font-bold">{pullProgress.model}</span>
              <span className="text-slate-400 capitalize">({pullProgress.status})</span>
            </div>
            <div className="flex items-center gap-2 font-mono">
              {pullProgress.completed_bytes ? (
                <span className="text-slate-400 text-[11px]">
                  {formatBytes(pullProgress.completed_bytes)} / {formatBytes(pullProgress.total_bytes)}
                </span>
              ) : null}
              <span className="text-sky-400 font-bold">{pullProgress.percent}%</span>
            </div>
          </div>

          <div className="w-full h-2.5 rounded-full bg-slate-950 overflow-hidden border border-slate-800">
            <div
              className="h-full bg-gradient-to-r from-sky-500 via-cyan-400 to-emerald-400 transition-all duration-300 rounded-full shadow-sm shadow-cyan-400/50"
              style={{ width: `${Math.max(2, pullProgress.percent)}%` }}
            />
          </div>

          {pullProgress.status === "success" && (
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 mt-2.5 font-medium">
              <CheckCircle2 className="w-4 h-4" />
              <span>Model downloaded and verified! Aegis AI is now running 100% locally.</span>
            </div>
          )}
        </div>
      )}

      {/* Error Message */}
      {errorMsg && (
        <p className="mt-2.5 text-xs text-rose-400 font-mono bg-rose-500/10 p-2 rounded-xl border border-rose-500/20">
          Error: {errorMsg}
        </p>
      )}
    </div>
  );
};
