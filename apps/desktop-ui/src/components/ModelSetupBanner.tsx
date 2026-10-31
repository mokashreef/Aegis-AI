import React, { useState } from "react";
import { Download, AlertCircle, CheckCircle2, Play, Loader2 } from "lucide-react";
import { OllamaHealth, PullProgress } from "../types";
import { pullModelStream, startOllamaServer } from "../services/api";

interface ModelSetupBannerProps {
  ollama: OllamaHealth | null;
  onRefresh: () => void;
}

export const ModelSetupBanner: React.FC<ModelSetupBannerProps> = ({ ollama, onRefresh }) => {
  const [isPulling, setIsPulling] = useState(false);
  const [pullProgress, setPullProgress] = useState<PullProgress | null>(null);
  const [isStartingServer, setIsStartingServer] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!ollama) return null;

  // If server is ready and has models, do not show banner
  if (ollama.status === "ready" && ollama.models.length > 0) {
    return null;
  }

  const handlePull = async (modelName: string) => {
    setIsPulling(true);
    setErrorMsg(null);
    try {
      await pullModelStream(modelName, (prog) => {
        setPullProgress(prog);
        if (prog.status === "success") {
          setIsPulling(false);
          onRefresh();
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
      setErrorMsg("Failed to start Ollama server.");
    } finally {
      setIsStartingServer(false);
    }
  };

  return (
    <div className="mx-5 my-3 p-4 rounded-2xl bg-gradient-to-r from-amber-500/10 via-amber-600/10 to-slate-900 border border-amber-500/30 text-slate-200">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-amber-300">
              {ollama.status === "offline"
                ? "Ollama Server Offline"
                : "Local AI Model Required (Zero API Keys)"}
            </h4>
            <p className="text-xs text-slate-300 mt-1 max-w-lg">
              {ollama.status === "offline"
                ? "Ollama was detected on your PC but is not running. Start the service to enable local inference."
                : "Ollama is active, but no models are downloaded yet. Install a fast model for 100% offline, private intelligence."}
            </p>
          </div>
        </div>

        {ollama.status === "offline" ? (
          <button
            onClick={handleStartServer}
            disabled={isStartingServer}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition shadow-md shrink-0"
          >
            {isStartingServer ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
            Start Server
          </button>
        ) : (
          !isPulling && (
            <button
              onClick={() => handlePull("qwen2.5:1.5b")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition shadow-md shrink-0"
            >
              <Download className="w-3.5 h-3.5" />
              Install Qwen 2.5 (986MB)
            </button>
          )
        )}
      </div>

      {isPulling && pullProgress && (
        <div className="mt-3 pt-3 border-t border-amber-500/20">
          <div className="flex items-center justify-between text-xs text-amber-200 mb-1.5">
            <span className="font-mono">
              Downloading {pullProgress.model}: {pullProgress.status}
            </span>
            <span className="font-mono font-bold">{pullProgress.percent}%</span>
          </div>

          <div className="w-full h-2 rounded-full bg-slate-900/80 overflow-hidden border border-slate-700/60">
            <div
              className="h-full bg-gradient-to-r from-amber-500 to-sky-400 transition-all duration-300 rounded-full"
              style={{ width: `${pullProgress.percent}%` }}
            />
          </div>

          {pullProgress.status === "success" && (
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 mt-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>Model installed successfully! Aegis AI is now 100% local.</span>
            </div>
          )}
        </div>
      )}

      {errorMsg && (
        <p className="mt-2 text-xs text-rose-400 font-mono">Error: {errorMsg}</p>
      )}
    </div>
  );
};
