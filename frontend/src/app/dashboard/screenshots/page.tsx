"use client";

import { useEffect, useState, useMemo } from "react";
import { apiClient } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import { isAtLeast } from "@/lib/roles";
import {
  Camera,
  ChevronLeft,
  ChevronRight,
  ImageOff,
  Users,
  CalendarDays,
  Monitor,
} from "lucide-react";

// ── Types ──

interface ScreenshotItem {
  id: string;
  user_id: string;
  user_name: string | null;
  user_email: string | null;
  time_entry_id: string;
  file_path: string;
  thumbnail_path: string | null;
  activity_percent: number;
  captured_at: string;
  is_blurred: boolean;
  active_app: string | null;
  active_window_title: string | null;
  active_url: string | null;
}

interface ScreenshotData {
  screenshots: ScreenshotItem[];
  total: number;
  page: number;
  per_page: number;
}

interface TeamMember {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
}

/** Group of screenshots within a 10-minute slot */
interface TimeSlot {
  label: string; // "09:00 - 09:10"
  startMinute: number; // minutes from midnight, for sorting
  screenshots: ScreenshotItem[];
}

// ── Helpers ──

function formatDate(d: Date): string {
  return d.toISOString().split("T")[0]; // "2026-04-06"
}

function formatDisplayDate(d: Date): string {
  return d.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function padTime(n: number): string {
  return String(n).padStart(2, "0");
}

/**
 * Group screenshots into 10-minute time slots.
 * E.g. 09:00-09:10, 09:10-09:20, etc.
 */
function groupIntoTimeSlots(screenshots: ScreenshotItem[]): TimeSlot[] {
  const slotMap = new Map<string, ScreenshotItem[]>();

  for (const shot of screenshots) {
    const d = new Date(shot.captured_at);
    const h = d.getHours();
    const m = d.getMinutes();
    const slotStart = Math.floor(m / 10) * 10;
    const slotEnd = slotStart + 10;
    const key = `${padTime(h)}:${padTime(slotStart)}`;
    const label = `${padTime(h)}:${padTime(slotStart)} - ${
      slotEnd >= 60
        ? `${padTime(h + 1)}:00`
        : `${padTime(h)}:${padTime(slotEnd)}`
    }`;

    if (!slotMap.has(key)) {
      slotMap.set(key, []);
    }
    slotMap.get(key)!.push(shot);
  }

  const slots: TimeSlot[] = [];
  for (const [key, shots] of Array.from(slotMap.entries())) {
    const [hStr, mStr] = key.split(":");
    const h = parseInt(hStr);
    const m = parseInt(mStr);
    const slotEnd = m + 10;
    const label = `${padTime(h)}:${padTime(m)} - ${
      slotEnd >= 60
        ? `${padTime(h + 1)}:00`
        : `${padTime(h)}:${padTime(slotEnd)}`
    }`;

    slots.push({
      label,
      startMinute: h * 60 + m,
      screenshots: shots.sort(
        (a: ScreenshotItem, b: ScreenshotItem) =>
          new Date(a.captured_at).getTime() - new Date(b.captured_at).getTime()
      ),
    });
  }

  // Sort earliest first
  return slots.sort((a, b) => a.startMinute - b.startMinute);
}

// ── Main Component ──

export default function ScreenshotsPage() {
  const { user } = useAuthStore();
  const userRole = user?.role || "employee";

  // State
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [selectedMemberId, setSelectedMemberId] = useState<string>(""); // "" = self
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [data, setData] = useState<ScreenshotData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedShot, setSelectedShot] = useState<ScreenshotItem | null>(null);

  const canViewTeam = isAtLeast(userRole, "manager");

  // Load team members for the dropdown (manager+ only)
  useEffect(() => {
    if (!canViewTeam) return;
    const loadMembers = async () => {
      try {
        const res = await apiClient.get("/users?per_page=100");
        const members = res.data?.users || res.data || [];
        setTeamMembers(members);
      } catch {
        // silently fail
      }
    };
    loadMembers();
  }, [canViewTeam]);

  // Fetch screenshots for the selected date + member
  useEffect(() => {
    const fetchScreenshots = async () => {
      setLoading(true);
      try {
        const dateStr = formatDate(selectedDate);
        const dateFrom = `${dateStr}T00:00:00`;
        const dateTo = `${dateStr}T23:59:59`;

        let url = `/activity/screenshots?date_from=${dateFrom}&date_to=${dateTo}&per_page=200&page=1`;
        if (selectedMemberId) {
          url += `&user_id=${selectedMemberId}`;
        } else if (!canViewTeam) {
          // Employee viewing their own — no user_id filter needed, backend scopes automatically
        }
        const res = await apiClient.get(url);
        setData(res.data);
      } catch {
        setData(null);
      } finally {
        setLoading(false);
      }
    };
    fetchScreenshots();
  }, [selectedDate, selectedMemberId, canViewTeam]);

  // Group screenshots into 10-min slots
  const timeSlots = useMemo(() => {
    if (!data?.screenshots) return [];
    return groupIntoTimeSlots(data.screenshots);
  }, [data]);

  // Date navigation
  const goToPrevDay = () => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() - 1);
    setSelectedDate(d);
  };
  const goToNextDay = () => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() + 1);
    const today = new Date();
    if (d <= today) setSelectedDate(d);
  };
  const isToday =
    formatDate(selectedDate) === formatDate(new Date());

  // The currently selected member's name (for display)
  const selectedMember = teamMembers.find((m) => m.id === selectedMemberId);
  const displayName = selectedMember
    ? `${selectedMember.first_name} ${selectedMember.last_name}`
    : user
    ? `${user.first_name} ${user.last_name}`
    : "You";

  return (
    <div className="p-8 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
          <Camera className="w-8 h-8 text-primary-600" />
          Screenshots
        </h1>
        <p className="text-slate-600 mt-1">
          View periodic screenshots captured during work sessions
        </p>
      </div>

      {/* Controls Bar: Date picker + Member dropdown */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 mb-6">
        <div className="flex flex-wrap items-center gap-4">
          {/* Date navigation */}
          <div className="flex items-center gap-2">
            <CalendarDays className="w-5 h-5 text-slate-400" />
            <button
              onClick={goToPrevDay}
              className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <ChevronLeft className="w-4 h-4 text-slate-600" />
            </button>
            <div className="flex items-center gap-2">
              <input
                type="date"
                value={formatDate(selectedDate)}
                max={formatDate(new Date())}
                onChange={(e) => {
                  if (e.target.value) setSelectedDate(new Date(e.target.value + "T12:00:00"));
                }}
                className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
              {!isToday && (
                <button
                  onClick={() => setSelectedDate(new Date())}
                  className="px-3 py-2 text-xs font-medium text-primary-600 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors"
                >
                  Today
                </button>
              )}
            </div>
            <button
              onClick={goToNextDay}
              disabled={isToday}
              className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors disabled:opacity-30"
            >
              <ChevronRight className="w-4 h-4 text-slate-600" />
            </button>
          </div>

          {/* Divider */}
          <div className="h-8 w-px bg-slate-200" />

          {/* Member dropdown (manager+ only) */}
          {canViewTeam && teamMembers.length > 0 && (
            <div className="flex items-center gap-2">
              <Users className="w-5 h-5 text-slate-400" />
              <select
                value={selectedMemberId}
                onChange={(e) => setSelectedMemberId(e.target.value)}
                className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none min-w-[200px]"
              >
                <option value="">All Members</option>
                {teamMembers.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.first_name} {m.last_name} ({m.role})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Stats */}
          <div className="ml-auto text-sm text-slate-500">
            {data ? (
              <>
                <span className="font-semibold text-slate-900">
                  {data.total}
                </span>{" "}
                screenshots on{" "}
                <span className="font-medium">
                  {formatDisplayDate(selectedDate)}
                </span>
              </>
            ) : (
              "Loading..."
            )}
          </div>
        </div>
      </div>

      {/* Timeline View */}
      {loading ? (
        <div className="space-y-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
              <div className="h-5 w-32 bg-slate-200 rounded animate-pulse mb-4" />
              <div className="flex gap-4">
                {[1, 2, 3].map((j) => (
                  <div
                    key={j}
                    className="w-64 h-36 bg-slate-100 rounded-lg animate-pulse"
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : timeSlots.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-16 text-center">
          <Camera className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <p className="text-lg font-medium text-slate-600">
            No screenshots for this date
          </p>
          <p className="text-sm text-slate-400 mt-2">
            {selectedMember
              ? `${selectedMember.first_name} has no screenshots on ${formatDisplayDate(selectedDate)}`
              : `No screenshots were captured on ${formatDisplayDate(selectedDate)}`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {timeSlots.map((slot) => (
            <div
              key={slot.label}
              className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden"
            >
              {/* Time slot header */}
              <div className="px-5 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
                    <Monitor className="w-4 h-4 text-primary-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">
                      {slot.label}
                    </p>
                    <p className="text-xs text-slate-500">
                      {slot.screenshots.length} screenshot
                      {slot.screenshots.length !== 1 ? "s" : ""}
                    </p>
                  </div>
                </div>
                {/* Show member name if viewing "All Members" */}
                {!selectedMemberId &&
                  slot.screenshots[0]?.user_name &&
                  canViewTeam && (
                    <span className="text-xs font-medium text-primary-600 bg-primary-50 px-2.5 py-1 rounded-full">
                      {slot.screenshots[0].user_name}
                    </span>
                  )}
              </div>

              {/* Screenshots grid — 3 per row like WebWork */}
              <div className="p-4">
                <div className="flex gap-4 overflow-x-auto">
                  {slot.screenshots.map((shot) => (
                    <div
                      key={shot.id}
                      className="flex-shrink-0 w-72 group cursor-pointer"
                      onClick={() => setSelectedShot(shot)}
                    >
                      {/* Image */}
                      <div className="aspect-video bg-slate-100 rounded-lg overflow-hidden relative border border-slate-200 hover:border-primary-300 transition-colors">
                        <ScreenshotImage screenshotId={shot.id} />

                        {/* Activity badge */}
                        <div className="absolute bottom-2 left-2">
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${
                              shot.activity_percent >= 70
                                ? "bg-green-100 text-green-700"
                                : shot.activity_percent >= 30
                                ? "bg-amber-100 text-amber-700"
                                : "bg-red-100 text-red-700"
                            }`}
                          >
                            {shot.activity_percent.toFixed(0)}%
                          </span>
                        </div>

                        {/* Hover overlay */}
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors flex items-center justify-center">
                          <span className="opacity-0 group-hover:opacity-100 text-white text-xs font-medium bg-black/60 px-3 py-1.5 rounded-full transition-opacity">
                            Click to enlarge
                          </span>
                        </div>
                      </div>

                      {/* Timestamp + user */}
                      <div className="mt-2 flex items-center justify-between">
                        <p className="text-xs text-slate-500">
                          {new Date(shot.captured_at).toLocaleTimeString(
                            "en-US",
                            {
                              hour: "2-digit",
                              minute: "2-digit",
                              second: "2-digit",
                            }
                          )}
                        </p>
                        {/* Show member name per screenshot when "All Members" */}
                        {!selectedMemberId && shot.user_name && canViewTeam && (
                          <p className="text-[10px] font-medium text-slate-400 truncate max-w-[120px]">
                            {shot.user_name}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Full-screen lightbox */}
      {selectedShot && (
        <div
          className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-8"
          onClick={() => setSelectedShot(null)}
        >
          <div
            className="max-w-5xl w-full bg-white rounded-xl overflow-hidden shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="bg-slate-900">
              <ScreenshotImage
                screenshotId={selectedShot.id}
                className="w-full max-h-[70vh] object-contain"
              />
            </div>
            <div className="p-4 flex items-center justify-between">
              <div>
                {selectedShot.user_name && (
                  <p className="text-sm font-semibold text-primary-700 mb-0.5">
                    {selectedShot.user_name}
                  </p>
                )}
                <p className="text-sm font-medium text-slate-900">
                  {new Date(selectedShot.captured_at).toLocaleString("en-US", {
                    weekday: "short",
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  })}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  Activity: {selectedShot.activity_percent.toFixed(0)}%
                  {selectedShot.active_window_title &&
                    ` — ${selectedShot.active_window_title}`}
                </p>
              </div>
              <button
                onClick={() => setSelectedShot(null)}
                className="px-4 py-2 text-sm font-medium bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Screenshot Image Component ──

function ScreenshotImage({
  screenshotId,
  className = "w-full h-full object-cover",
}: {
  screenshotId: string;
  className?: string;
}) {
  const [src, setSrc] = useState<string | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const loadImage = async () => {
      try {
        const res = await apiClient.get(
          `/activity/screenshots/${screenshotId}/image`,
          { responseType: "blob" }
        );
        if (cancelled) return;
        const url = URL.createObjectURL(res.data);
        setSrc(url);
      } catch {
        if (!cancelled) setError(true);
      }
    };

    loadImage();

    return () => {
      cancelled = true;
      if (src) URL.revokeObjectURL(src);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [screenshotId]);

  if (error) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center text-slate-300 bg-slate-50">
        <ImageOff className="w-8 h-8 mb-1" />
        <span className="text-xs">Failed to load</span>
      </div>
    );
  }

  if (!src) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-5 w-5 border-2 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  return <img src={src} alt="Screenshot" className={className} />;
}
