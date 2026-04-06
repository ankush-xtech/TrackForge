"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import {
  Camera,
  ChevronLeft,
  ChevronRight,
  Monitor,
  Globe,
  Trash2,
  Eye,
  EyeOff,
} from "lucide-react";

interface ScreenshotItem {
  id: string;
  user_id: string;
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

function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function ScreenshotsPage() {
  const [data, setData] = useState<ScreenshotData | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const perPage = 12;

  const fetchScreenshots = async (p: number) => {
    setLoading(true);
    try {
      const res = await apiClient.get(
        `/activity/screenshots?page=${p}&per_page=${perPage}`
      );
      setData(res.data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchScreenshots(page);
  }, [page]);

  const totalPages = data ? Math.ceil(data.total / perPage) : 0;

  const handleDelete = async (id: string) => {
    if (!window.confirm("Delete this screenshot?")) return;
    try {
      await apiClient.delete(`/activity/screenshots/${id}`);
      fetchScreenshots(page);
    } catch {
      // silently fail
    }
  };

  return (
    <div className="p-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
          <Camera className="w-8 h-8 text-primary-600" />
          Screenshots
        </h1>
        <p className="text-slate-600 mt-2">
          Periodic screenshots captured during work sessions
        </p>
      </div>

      {/* Stats bar */}
      {data && (
        <div className="flex items-center gap-4 mb-6">
          <span className="text-sm text-slate-500">
            {data.total} total screenshots
          </span>
          <span className="text-sm text-slate-300">|</span>
          <span className="text-sm text-slate-500">
            Page {page} of {totalPages || 1}
          </span>
        </div>
      )}

      {/* Gallery grid */}
      {loading && !data ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="bg-slate-100 rounded-xl aspect-video animate-pulse"
            />
          ))}
        </div>
      ) : !data || data.screenshots.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-16 text-center">
          <Camera className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <p className="text-lg font-medium text-slate-600">
            No screenshots yet
          </p>
          <p className="text-sm text-slate-400 mt-2">
            Screenshots will appear here once the desktop agent starts capturing
            them during work sessions.
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {data.screenshots.map((shot) => (
              <div
                key={shot.id}
                className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden group hover:shadow-md transition-shadow"
              >
                {/* Thumbnail area */}
                <div className="aspect-video bg-slate-100 relative flex items-center justify-center">
                  {shot.is_blurred ? (
                    <div className="flex flex-col items-center text-slate-400">
                      <EyeOff className="w-8 h-8 mb-1" />
                      <span className="text-xs">Blurred</span>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center text-slate-300">
                      <Monitor className="w-10 h-10 mb-1" />
                      <span className="text-xs text-slate-400">
                        {shot.active_app || "Desktop"}
                      </span>
                    </div>
                  )}

                  {/* Delete overlay */}
                  <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleDelete(shot.id)}
                      className="p-1.5 bg-white/90 rounded-lg text-slate-400 hover:text-red-600 shadow-sm"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Activity badge */}
                  <div className="absolute bottom-2 left-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        shot.activity_percent >= 70
                          ? "bg-green-100 text-green-700"
                          : shot.activity_percent >= 30
                          ? "bg-amber-100 text-amber-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {shot.activity_percent.toFixed(0)}% activity
                    </span>
                  </div>
                </div>

                {/* Meta */}
                <div className="p-3">
                  <p className="text-xs text-slate-500 mb-1">
                    {formatDateTime(shot.captured_at)}
                  </p>
                  {shot.active_window_title && (
                    <p className="text-xs text-slate-600 truncate font-medium">
                      {shot.active_window_title}
                    </p>
                  )}
                  {shot.active_url && (
                    <div className="flex items-center gap-1 mt-1">
                      <Globe className="w-3 h-3 text-slate-400" />
                      <p className="text-xs text-slate-400 truncate">
                        {shot.active_url}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-8">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              {Array.from({ length: Math.min(totalPages, 5) }).map((_, i) => {
                const pageNum = i + 1;
                return (
                  <button
                    key={pageNum}
                    onClick={() => setPage(pageNum)}
                    className={`w-9 h-9 rounded-lg text-sm font-medium transition-colors ${
                      page === pageNum
                        ? "bg-primary-600 text-white"
                        : "border border-slate-200 text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
