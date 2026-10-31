import React from "react";
import { Terminal, CheckCircle2, AlertTriangle, Loader2 } from "lucide-react";
import { ToolActivity } from "../types";

interface ActionCardProps {
  activity: ToolActivity;
  onConfirm?: (toolName: string, args: Record<string, unknown>) => void;
}

export const ActionCard: React.FC<ActionCardProps> = ({ activity, onConfirm }) => {
  const isPending = activity.status === "pending";
  const isSuccess = activity.status === "success";
  const isError = activity.status === "error";

  return (
    <div className="my-2 p-3 rounded-xl glass-card flex flex-col gap-2 transition-all">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400">
            <Terminal className="w-4 h-4" />
          </div>
          <span className="font-mono text-xs font-semibold text-sky-300">
            {activity.toolName}
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-xs">
          {isPending && (
            <span className="flex items-center gap-1 text-amber-400">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Executing
            </span>
          )}
          {isSuccess && (
            <span className="flex items-center gap-1 text-emerald-400">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Completed
            </span>
          )}
          {isError && (
            <span className="flex items-center gap-1 text-rose-400">
              <AlertTriangle className="w-3.5 h-3.5" />
              Failed
            </span>
          )}
        </div>
      </div>

      <div className="text-xs font-mono text-slate-400 bg-slate-950/40 p-2 rounded-lg overflow-x-auto">
        {JSON.stringify(activity.arguments, null, 2)}
      </div>

      {activity.status === "requires_confirmation" && onConfirm && (
        <div className="mt-2 flex items-center justify-between bg-amber-500/10 border border-amber-500/30 p-2 rounded-lg">
          <span className="text-xs text-amber-300">Requires confirmation</span>
          <button
            onClick={() => onConfirm(activity.toolName, activity.arguments)}
            className="px-3 py-1 bg-amber-500 hover:bg-amber-600 text-slate-950 text-xs font-semibold rounded-md transition"
          >
            Allow Execution
          </button>
        </div>
      )}
    </div>
  );
};

