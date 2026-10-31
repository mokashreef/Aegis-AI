import React from "react";
import { X, Cpu, HardDrive, ShieldCheck, Activity, Zap, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { SystemTelemetry, AIRuntimeStatus } from "../types";

interface SystemTelemetryModalProps {
  telemetry: SystemTelemetry | null;
  runtimeStatus: AIRuntimeStatus | null;
  onClose: () => void;
}

export const SystemTelemetryModal: React.FC<SystemTelemetryModalProps> = ({
  telemetry,
  runtimeStatus,
  onClose,
}) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl glass-panel p-6 shadow-2xl relative border border-slate-700/60 max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 mb-6">
          <Activity className="w-6 h-6 text-sky-400" />
          <h2 className="text-lg font-bold text-slate-100">Windows System & AI Telemetry</h2>
        </div>

        {telemetry && (
          <div className="grid grid-cols-2 gap-3 mb-6">
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col gap-1">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <Cpu className="w-4 h-4 text-sky-400" />
                <span>Processor</span>
              </div>
              <span className="text-xl font-bold text-slate-100">
                {telemetry.cpu.usage_percent}%
              </span>
              <span className="text-xs text-slate-500">
                {telemetry.cpu.logical_cores} Cores Active
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col gap-1">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <HardDrive className="w-4 h-4 text-emerald-400" />
                <span>System RAM</span>
              </div>
              <span className="text-xl font-bold text-slate-100">
                {telemetry.memory.percent_used}%
              </span>
              <span className="text-xs text-slate-500">
                {telemetry.memory.available_gb} GB Free / {telemetry.memory.total_gb} GB
              </span>
            </div>
          </div>
        )}

        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 mb-4 space-y-3">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-sky-400" />
              <span>AI Inference Engine</span>
            </div>
            {runtimeStatus?.tokens_per_second ? (
              <span className="flex items-center gap-1 font-mono text-emerald-400">
                <Zap className="w-3.5 h-3.5" />
                {runtimeStatus.tokens_per_second} tok/s
              </span>
            ) : null}
          </div>

          {runtimeStatus ? (
            <div className="text-xs space-y-2 text-slate-400">
              <div className="flex items-center justify-between">
                <span>Active Provider:</span>
                <span className="text-sky-300 font-bold uppercase font-mono">{runtimeStatus.active_provider}</span>
              </div>

              <div className="flex items-center justify-between">
                <span>Ollama Daemon:</span>
                <span className="flex items-center gap-1">
                  {runtimeStatus.ollama.status === "ready" && (
                    <span className="text-emerald-400 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Ready (Air-Gapped)
                    </span>
                  )}
                  {runtimeStatus.ollama.status === "needs_model" && (
                    <span className="text-amber-400 flex items-center gap-1">
                      <AlertTriangle className="w-3.5 h-3.5" /> Needs Model Download
                    </span>
                  )}
                  {runtimeStatus.ollama.status === "offline" && (
                    <span className="text-rose-400 flex items-center gap-1">
                      <XCircle className="w-3.5 h-3.5" /> Offline
                    </span>
                  )}
                </span>
              </div>

              {runtimeStatus.ollama.reason && (
                <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px]">
                  {runtimeStatus.ollama.reason}
                </div>
              )}

              <div>
                <span className="block mb-1 text-slate-300 font-medium">Installed Local Models:</span>
                {runtimeStatus.ollama.models.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {runtimeStatus.ollama.models.map((m, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700 text-sky-300 font-mono text-[11px]">
                        {m}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-slate-500 italic text-[11px]">None downloaded yet</span>
                )}
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500">Loading telemetry...</p>
          )}
        </div>

        <button
          onClick={onClose}
          className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-xl transition"
        >
          Close
        </button>
      </div>
    </div>
  );
};
