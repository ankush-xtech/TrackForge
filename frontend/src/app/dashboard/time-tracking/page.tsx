"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  useTimeTrackingStore,
  type TimeEntry,
} from "@/stores/time-tracking-store";
import { useIdleDetection } from "@/hooks/use-idle-detection";
import { useScreenshotCapture } from "@/hooks/use-screenshot-capture";
import { IdlePopup } from "@/components/tracking/idle-popup";
import {
  Clock,
  Play,
  Square,
  BarChart3,
  Trash2,
  CalendarDays,
  Timer,
  TrendingUp,
  Zap,
  ChevronDown,
  Camera,
  CameraOff,
  Monitor,
  AlertTriangle,
} from "lucide-react";

// ── Helpers ──

function formatDuration(totalSeconds: number): string {
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  const s = totalSeconds % 60;
  return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function formatHoursMinutes(totalSeconds: number): string {
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  if (h === 0 && m === 0) return "0m";
  if (h === 0) return `${m}m`;
  return `${h}h ${m}m`;
}

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function formatTime(isoString: string): string {
  return new Date(isoString).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ── Project type ──

interface Project {
  id: string;
  name: string;
  color: string;
}

async function fetchProjects(): Promise<Project[]> {
  try {
    const res = await apiClient.get("/projects");
    return res.data?.projects || res.data || [];
  } catch {
    return [];
  }
}

// ── Main Component ──

export default function TimeTrackingPage() {
  const {
    activeEntry,
    entries,
    summary,
    isLoading,
    error,
    elapsed,
    idleDeducted,
    screenshotCount,
    setElapsed,
    deductIdleTime,
    incrementScreenshots,
    fetchActiveEntry,
    fetchEntries,
    fetchSummary,
    startTimer,
    stopTimer,
    deleteEntry,
    clearError,
  } = useTimeTrackingStore();

  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [description, setDescription] = useState("");
  const [showProjectDropdown, setShowProjectDropdown] = useState(false);
  const [showIdlePopup, setShowIdlePopup] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isTracking = !!activeEntry;

  // ── Idle Detection ──
  const { isIdle, idleSeconds } = useIdleDetection({
    timeout: 5 * 60 * 1000, // 5 minutes
    enabled: isTracking,
    onIdle: () => {
      setShowIdlePopup(true);
    },
    onActive: () => {
      // Auto-dismiss if user starts moving before clicking a button
      // (but we keep it shown so they must click Yes/No)
    },
  });

  const handleYesWorking = useCallback(() => {
    // User confirmed they were working — keep the time, dismiss popup
    setShowIdlePopup(false);
  }, []);

  const handleNotWorking = useCallback(() => {
    // User was NOT working — deduct the idle seconds from the session
    deductIdleTime(idleSeconds);
    setShowIdlePopup(false);
  }, [deductIdleTime, idleSeconds]);

  // ── Screenshot Capture ──
  const {
    hasPermission: hasScreenshotPermission,
    isCapturing,
    captureCount,
    requestPermission: requestScreenshotPermission,
    stopCapture: stopScreenshotCapture,
  } = useScreenshotCapture({
    interval: 200 * 1000, // ~3m20s → 3 screenshots per 10 minutes
    enabled: isTracking && !showIdlePopup, // pause captures during idle popup
    timeEntryId: activeEntry?.id || null,
    onCapture: () => {
      incrementScreenshots();
    },
  });

  // Fetch projects
  const { data: projects = [] } = useQuery({
    queryKey: ["projects"],
    queryFn: fetchProjects,
  });

  // Initial data load
  useEffect(() => {
    fetchActiveEntry();
    fetchEntries();
    fetchSummary();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Live timer tick
  useEffect(() => {
    if (activeEntry) {
      const startMs = new Date(activeEntry.start_time).getTime();
      const tick = () => {
        const now = Date.now();
        setElapsed(Math.floor((now - startMs) / 1000));
      };
      tick();
      timerRef.current = setInterval(tick, 1000);
      return () => {
        if (timerRef.current) clearInterval(timerRef.current);
      };
    } else {
      setElapsed(0);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  }, [activeEntry, setElapsed]);

  // Auto-clear errors
  useEffect(() => {
    if (error) {
      const t = setTimeout(clearError, 5000);
      return () => clearTimeout(t);
    }
  }, [error, clearError]);

  const handleStart = async () => {
    await startTimer({
      project_id: selectedProjectId || undefined,
      description: description || undefined,
    });
    // Prompt for screen share permission if not already granted
    if (!hasScreenshotPermission) {
      requestScreenshotPermission();
    }
  };

  const handleStop = async () => {
    stopScreenshotCapture();
    setShowIdlePopup(false);
    await stopTimer();
    setDescription("");
    setSelectedProjectId("");
  };

  const handleDelete = async (entryId: string) => {
    if (window.confirm("Delete this time entry?")) {
      await deleteEntry(entryId);
    }
  };

  const selectedProject = projects.find((p) => p.id === selectedProjectId);

  // The effective elapsed minus any idle deductions
  const effectiveElapsed = Math.max(0, elapsed - idleDeducted);

  return (
    <div className="p-8 max-w-6xl">
      {/* Idle Detection Popup */}
      {showIdlePopup && isTracking && (
        <IdlePopup
          idleSeconds={idleSeconds}
          onYesWorking={handleYesWorking}
          onNotWorking={handleNotWorking}
        />
      )}

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

      {/* Error banner */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Timer + Stats grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Timer Widget */}
        <div className="lg:col-span-1 bg-white rounded-xl border border-slate-100 shadow-sm p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Timer className="w-5 h-5 text-primary-600" />
            Timer
          </h2>

          {/* Timer display */}
          <div
            className={`rounded-lg p-6 text-center mb-5 border transition-colors ${
              isTracking
                ? "bg-gradient-to-br from-green-50 to-emerald-50 border-green-200"
                : "bg-gradient-to-br from-primary-50 to-blue-50 border-primary-200"
            }`}
          >
            <div
              className={`text-5xl font-bold font-mono tracking-wider ${
                isTracking ? "text-green-700" : "text-primary-700"
              }`}
            >
              {formatDuration(effectiveElapsed)}
            </div>
            {isTracking && (
              <p className="text-xs text-green-600 mt-2 font-medium">
                Recording...
              </p>
            )}
            {isTracking && idleDeducted > 0 && (
              <p className="text-xs text-amber-600 mt-1 flex items-center justify-center gap-1">
                <AlertTriangle className="w-3 h-3" />
                {formatHoursMinutes(idleDeducted)} idle deducted
              </p>
            )}
          </div>

          {/* Screenshot & Idle status indicators (when tracking) */}
          {isTracking && (
            <div className="flex items-center gap-3 mb-5 p-3 bg-slate-50 rounded-lg">
              {/* Screenshot status */}
              <div className="flex items-center gap-2 flex-1">
                {hasScreenshotPermission ? (
                  <>
                    <Camera className="w-4 h-4 text-green-600" />
                    <div>
                      <p className="text-xs font-medium text-green-700">
                        {isCapturing ? "Capturing..." : "Screenshots On"}
                      </p>
                      <p className="text-[10px] text-slate-500">
                        {screenshotCount || captureCount} taken
                      </p>
                    </div>
                  </>
                ) : (
                  <>
                    <CameraOff className="w-4 h-4 text-slate-400" />
                    <div>
                      <p className="text-xs font-medium text-slate-600">
                        Screenshots Off
                      </p>
                      <button
                        onClick={requestScreenshotPermission}
                        className="text-[10px] text-primary-600 hover:text-primary-700 underline"
                      >
                        Enable
                      </button>
                    </div>
                  </>
                )}
              </div>

              {/* Activity status */}
              <div className="flex items-center gap-2 flex-1">
                <Monitor
                  className={`w-4 h-4 ${
                    isIdle ? "text-amber-500" : "text-green-600"
                  }`}
                />
                <div>
                  <p
                    className={`text-xs font-medium ${
                      isIdle ? "text-amber-700" : "text-green-700"
                    }`}
                  >
                    {isIdle ? "Idle" : "Active"}
                  </p>
                  <p className="text-[10px] text-slate-500">
                    Activity monitor
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Project selector */}
          {!isTracking && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                Project (optional)
              </label>
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowProjectDropdown(!showProjectDropdown)}
                  className="w-full flex items-center justify-between px-3 py-2.5 border border-slate-300 rounded-lg text-sm text-left hover:border-slate-400 transition-colors"
                >
                  <span
                    className={
                      selectedProject ? "text-slate-900" : "text-slate-400"
                    }
                  >
                    {selectedProject?.name || "No project"}
                  </span>
                  <ChevronDown className="w-4 h-4 text-slate-400" />
                </button>
                {showProjectDropdown && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                    <button
                      onClick={() => {
                        setSelectedProjectId("");
                        setShowProjectDropdown(false);
                      }}
                      className="w-full text-left px-3 py-2 text-sm text-slate-500 hover:bg-slate-50"
                    >
                      No project
                    </button>
                    {projects.map((p) => (
                      <button
                        key={p.id}
                        onClick={() => {
                          setSelectedProjectId(p.id);
                          setShowProjectDropdown(false);
                        }}
                        className="w-full text-left px-3 py-2 text-sm text-slate-900 hover:bg-primary-50 flex items-center gap-2"
                      >
                        <span
                          className="w-3 h-3 rounded-full flex-shrink-0"
                          style={{ backgroundColor: p.color || "#6366f1" }}
                        />
                        {p.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Description */}
          {!isTracking && (
            <div className="mb-5">
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                What are you working on?
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g., Fixing login bug"
                className="w-full px-3 py-2.5 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
            </div>
          )}

          {/* Currently tracking info */}
          {isTracking && activeEntry?.description && (
            <div className="mb-5 p-3 bg-slate-50 rounded-lg">
              <p className="text-xs text-slate-500 mb-0.5">Working on</p>
              <p className="text-sm font-medium text-slate-900">
                {activeEntry.description}
              </p>
            </div>
          )}

          {/* Start / Stop button */}
          <button
            onClick={isTracking ? handleStop : handleStart}
            disabled={isLoading}
            className={`w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-semibold transition-colors disabled:opacity-50 ${
              isTracking
                ? "bg-red-600 text-white hover:bg-red-700"
                : "bg-green-600 text-white hover:bg-green-700"
            }`}
          >
            {isLoading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
            ) : isTracking ? (
              <>
                <Square className="w-5 h-5" />
                Stop Timer
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                Start Timer
              </>
            )}
          </button>
        </div>

        {/* Stats cards */}
        <div className="lg:col-span-2 grid grid-cols-2 gap-4">
          <StatCard
            label="Today"
            value={formatHoursMinutes(summary?.today_seconds || 0)}
            detail={`${summary?.entries_today || 0} entries`}
            icon={<CalendarDays className="w-5 h-5 text-blue-600" />}
          />
          <StatCard
            label="This Week"
            value={formatHoursMinutes(summary?.week_seconds || 0)}
            icon={<BarChart3 className="w-5 h-5 text-purple-600" />}
          />
          <StatCard
            label="This Month"
            value={formatHoursMinutes(summary?.month_seconds || 0)}
            icon={<TrendingUp className="w-5 h-5 text-emerald-600" />}
          />
          <StatCard
            label="Avg. Activity"
            value={`${summary?.avg_activity_percent || 0}%`}
            detail="Today's average"
            icon={<Zap className="w-5 h-5 text-amber-600" />}
          />
        </div>
      </div>

      {/* Time entries table */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-primary-600" />
            Recent Entries
          </h2>
          <span className="text-sm text-slate-500">
            {entries.length} entries
          </span>
        </div>

        {entries.length === 0 ? (
          <div className="text-center py-12">
            <Clock className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-600">No time entries yet</p>
            <p className="text-sm text-slate-500 mt-2">
              Start the timer to create your first entry
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                    Description
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                    Start
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                    End
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                    Activity
                  </th>
                  <th className="px-6 py-3 text-right text-sm font-semibold text-slate-900">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {entries.map((entry: TimeEntry) => (
                  <tr
                    key={entry.id}
                    className="hover:bg-slate-50 transition-colors"
                  >
                    <td className="px-6 py-4">
                      <p className="text-sm font-medium text-slate-900">
                        {entry.description || "No description"}
                      </p>
                      {entry.is_manual && (
                        <span className="text-xs text-slate-400">Manual</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600">
                      {formatDate(entry.start_time)}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600">
                      {formatTime(entry.start_time)}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600">
                      {entry.end_time ? (
                        formatTime(entry.end_time)
                      ) : (
                        <span className="inline-flex items-center gap-1 text-green-600 font-medium">
                          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                          Running
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm font-mono font-medium text-slate-900">
                      {entry.end_time
                        ? formatHoursMinutes(entry.duration_seconds)
                        : "—"}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-slate-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary-500 rounded-full"
                            style={{
                              width: `${Math.min(
                                entry.activity_percent,
                                100
                              )}%`,
                            }}
                          />
                        </div>
                        <span className="text-xs text-slate-500">
                          {entry.activity_percent.toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {entry.end_time && (
                        <button
                          onClick={() => handleDelete(entry.id)}
                          className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                          title="Delete entry"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Stat Card Component ──

function StatCard({
  label,
  value,
  detail,
  icon,
}: {
  label: string;
  value: string;
  detail?: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm text-slate-600">{label}</p>
        {icon}
      </div>
      <p className="text-3xl font-bold text-slate-900">{value}</p>
      {detail && <p className="text-xs text-slate-500 mt-2">{detail}</p>}
    </div>
  );
}
