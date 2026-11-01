import React, { useState } from "react";
import {
  Terminal,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Globe,
  AppWindow,
  Volume2,
  Camera,
  Layers,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { ToolActivity } from "../types";

interface ActionCardProps {
  activity: ToolActivity;
  onConfirm?: (toolName: string, args: Record<string, unknown>) => void;
}

export const ActionCard: React.FC<ActionCardProps> = ({ activity, onConfirm }) => {
  const [showDetails, setShowDetails] = useState(false);
  const isPending = activity.status === "pending";
  const isSuccess = activity.status === "success";
  const isError = activity.status === "error";

  const getToolMeta = () => {
    switch (activity.toolName) {
      case "open_url":
        return {
          icon: <Globe className="w-4 h-4 text-sky-400" />,
          title: "Open Website",
          titleAr: "فتح موقع ويب",
          summary: String(activity.arguments?.url || ""),
          badge: activity.arguments?.browser ? String(activity.arguments.browser).toUpperCase() : "DEFAULT",
        };
      case "launch_application":
        return {
          icon: <AppWindow className="w-4 h-4 text-emerald-400" />,
          title: "Launch Application",
          titleAr: "تشغيل تطبيق",
          summary: String(activity.arguments?.app_name || ""),
          badge: "APP",
        };
      case "control_volume":
        return {
          icon: <Volume2 className="w-4 h-4 text-purple-400" />,
          title: "Volume Control",
          titleAr: "التحكم بالصوت",
          summary: `${String(activity.arguments?.action || "")} ${activity.arguments?.level ? activity.arguments.level + "%" : ""}`,
          badge: "AUDIO",
        };
      case "capture_screen":
        return {
          icon: <Camera className="w-4 h-4 text-amber-400" />,
          title: "Screen Capture",
          titleAr: "تصوير الشاشة",
          summary: "Full screen snapshot",
          badge: "DISPLAY",
        };
      case "minimize_all_windows":
        return {
          icon: <Layers className="w-4 h-4 text-indigo-400" />,
          title: "Show Desktop",
          titleAr: "إظهار سطح المكتب",
          summary: "Minimize all active windows",
          badge: "WINDOW",
        };
      default:
        return {
          icon: <Terminal className="w-4 h-4 text-cyan-400" />,
          title: activity.toolName.replace(/_/g, " "),
          titleAr: activity.toolName,
          summary: Object.values(activity.arguments || {}).join(", "),
          badge: "TOOL",
        };
    }
  };

  const meta = getToolMeta();

  return (
      <div className="my-2.5 p-3.5 rounded-2xl bg-slate-900/60 border border-slate-700/60 backdrop-blur-md shadow-sm transition-all hover:border-slate-600/70">
        <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-slate-800/80 border border-slate-700/50 shadow-inner">
                  {meta.icon}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-xs text-slate-200">
                      {meta.title}
                    </span>
                    <span className="text-[10px] text-slate-400 font-sans">
                      ({meta.titleAr})
                    </span>
                    {meta.badge && (
                      <span className="px-1.5 py-0.5 rounded-md bg-slate-800 text-[10px] font-mono text-slate-300 border border-slate-700/50">
                        {meta.badge}
                      </span>
                    )}
                  </div>
                  {meta.summary && (
                    <p className="text-xs text-sky-300 font-mono mt-0.5 truncate max-w-sm">
                      {meta.summary}
                    </p>
                  )}
                </div>
              </div>

                <div className="flex items-center gap-2 text-xs">
                  {isPending && (
                      <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/20 font-medium">
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />
                        Executing
                      </span>
          )}
                      {isSuccess && (
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              Completed
            </span>
          )}
          {isError && (
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/20 font-medium">
              <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
              Failed
            </span>
          )}

          <button
            onClick={() => setShowDetails(!showDetails)}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
            title="Toggle raw details"
          >
            {showDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {showDetails && (
                        <div className="mt-2.5 pt-2 border-t border-slate-800/80 text-[11px] font-mono text-slate-400 bg-slate-950/50 p-2.5 rounded-xl overflow-x-auto">
                          {JSON.stringify(activity.arguments, null, 2)}
                        </div>
                      )}

                      {activity.status === "requires_confirmation" && onConfirm && (
                          <div className="mt-2.5 flex items-center justify-between bg-amber-500/10 border border-amber-500/30 p-2.5 rounded-xl">
                            <span className="text-xs text-amber-300 font-medium">Requires user confirmation</span>
                            <button
                              onClick={() => onConfirm(activity.toolName, activity.arguments)}
                              className="px-3.5 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-semibold rounded-lg shadow-sm transition"
                            >
                              Confirm & Run
                            </button>
                          </div>
      )}
                        </div>
                      );
};
