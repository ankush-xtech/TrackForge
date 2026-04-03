"use client";

import { Clock, Play, Square, BarChart3 } from "lucide-react";
import { useState } from "react";

export default function TimeTrackingPage() {
  const [isTracking, setIsTracking] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  return (
    <div className="p-8 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
          <Clock className="w-8 h-8 text-primary-600" />
          Time Tracking
        </h1>
        <p className="text-slate-600 mt-2">
          Track your work hours and productivity
        </p>
      </div>

      {/* Timer Widget */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-1 bg-white rounded-xl border border-slate-100 shadow-sm p-8">
          <h2 className="text-lg font-semibold text-slate-900 mb-6">
            Timer
          </h2>

          <div className="bg-gradient-to-br from-primary-50 to-blue-50 rounded-lg p-8 text-center mb-6 border border-primary-200">
            <div className="text-5xl font-bold text-primary-700 font-mono tracking-wider">
              {Math.floor(elapsed / 3600)}
              :
              {String(Math.floor((elapsed % 3600) / 60)).padStart(2, "0")}
              :
              {String(elapsed % 60).padStart(2, "0")}
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => setIsTracking(!isTracking)}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-semibold transition-colors ${
                isTracking
                  ? "bg-red-600 text-white hover:bg-red-700"
                  : "bg-green-600 text-white hover:bg-green-700"
              }`}
            >
              {isTracking ? (
                <>
                  <Square className="w-5 h-5" />
                  Stop
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  Start
                </>
              )}
            </button>
          </div>

          <p className="text-xs text-slate-500 text-center mt-4">
            Click Start to begin tracking time
          </p>
        </div>

        {/* Quick Stats */}
        <div className="lg:col-span-2 grid grid-cols-2 gap-4">
          <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
            <p className="text-sm text-slate-600 mb-2">Today</p>
            <p className="text-3xl font-bold text-slate-900">0h 0m</p>
            <p className="text-xs text-slate-500 mt-2">No entries yet</p>
          </div>
          <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
            <p className="text-sm text-slate-600 mb-2">This Week</p>
            <p className="text-3xl font-bold text-slate-900">0h 0m</p>
            <p className="text-xs text-slate-500 mt-2">No entries yet</p>
          </div>
          <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
            <p className="text-sm text-slate-600 mb-2">This Month</p>
            <p className="text-3xl font-bold text-slate-900">0h 0m</p>
            <p className="text-xs text-slate-500 mt-2">No entries yet</p>
          </div>
          <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
            <p className="text-sm text-slate-600 mb-2">Project Hours</p>
            <p className="text-3xl font-bold text-slate-900">0h 0m</p>
            <p className="text-xs text-slate-500 mt-2">No entries yet</p>
          </div>
        </div>
      </div>

      {/* Time Entries */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-6 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-primary-600" />
          Recent Entries
        </h2>

        <div className="text-center py-12">
          <Clock className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-600">No time entries yet</p>
          <p className="text-sm text-slate-500 mt-2">
            Start tracking time to see entries here
          </p>
        </div>
      </div>
    </div>
  );
}
