import React from "react";
import { X, Cpu, HardDrive, ShieldCheck, Activity } from "lucide-react";
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
      <div className="w-full max-w-lg rounded-2xl glass-panel p-6 shadow-2xl relative border border-slate-700/60">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 mb-6">
          <Activity className="w-6 h-6 text-sky-400" />
          <h2 className="text-lg font-bold text-slate-100">Windows System Telemetry</h2>
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

        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 mb-4">
          <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-300">
            <ShieldCheck className="w-4 h-4 text-sky-400" />
            <span>AI Runtime Status (Zero API Keys Enforced)</span>
          </div>
          {runtimeStatus ? (
            <div className="text-xs space-y-1 text-slate-400 font-mono">
              <p>Active Provider: <span className="text-sky-300 font-bold">{runtimeStatus.active_provider}</span></p>
              <p>Local Ollama: <span className={runtimeStatus.ollama.available ? "text-emerald-400" : "text-amber-400"}>
                {runtimeStatus.ollama.available ? "Online (Air-Gapped)" : "Offline (Standby)"}
              </span></p>
              <p>Pollinations Free Fallback: <span className="text-emerald-400">Active</span></p>
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
