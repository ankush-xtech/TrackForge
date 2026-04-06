"use client";

import { Clock, CheckCircle, XCircle } from "lucide-react";

interface IdlePopupProps {
  /** How many seconds the user has been idle */
  idleSeconds: number;
  /** Called when user confirms they were working */
  onYesWorking: () => void;
  /** Called when user says they were NOT working (discard idle time) */
  onNotWorking: () => void;
}

function formatIdleTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function IdlePopup({
  idleSeconds,
  onYesWorking,
  onNotWorking,
}: IdlePopupProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-sm mx-4 text-center animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="mb-2">
          <h2 className="text-xl font-bold text-slate-900">
            Were you working?
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            You haven't typed or clicked on anything
          </p>
        </div>

        {/* Timer display */}
        <div className="my-6 flex items-center justify-center gap-3">
          <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
            <Clock className="w-6 h-6 text-primary-600" />
          </div>
          <span className="text-5xl font-bold text-slate-900 font-mono tracking-wider">
            {formatIdleTime(idleSeconds)}
          </span>
        </div>

        <p className="text-xs text-slate-400 mb-6">
          of inactivity detected
        </p>

        {/* Action buttons */}
        <div className="flex gap-3">
          <button
            onClick={onNotWorking}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-semibold text-sm border-2 border-slate-200 text-slate-700 hover:bg-slate-50 hover:border-slate-300 transition-colors"
          >
            <XCircle className="w-5 h-5" />
            No, I wasn't
          </button>
          <button
            onClick={onYesWorking}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-semibold text-sm bg-primary-600 text-white hover:bg-primary-700 transition-colors shadow-lg shadow-primary-600/20"
          >
            <CheckCircle className="w-5 h-5" />
            Yes, I was
          </button>
        </div>
      </div>
    </div>
  );
}
