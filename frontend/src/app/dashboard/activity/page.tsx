"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { Users, Wifi, WifiOff, Clock, Zap, RefreshCw } from "lucide-react";

interface TeamMember {
  user_id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  is_tracking: boolean;
  today_seconds: number;
  active_entry_description: string | null;
  active_entry_start_time: string | null;
  avg_activity_percent: number;
}

interface TeamActivity {
  members: TeamMember[];
  total_members: number;
  members_tracking: number;
}

function formatHM(s: number): string {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (h === 0 && m === 0) return "0m";
  if (h === 0) return `${m}m`;
  return `${h}h ${m}m`;
}

function formatElapsed(isoStart: string): string {
  const elapsed = Math.floor((Date.now() - new Date(isoStart).getTime()) / 1000);
  const h = Math.floor(elapsed / 3600);
  const m = Math.floor((elapsed % 3600) / 60);
  if (h === 0) return `${m}m`;
  return `${h}h ${m}m`;
}

export default function TeamActivityPage() {
  const [data, setData] = useState<TeamActivity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get("/activity/team");
      setData(res.data);
    } catch (err: any) {
      const msg = err.response?.data?.detail || "Failed to load team activity";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8 max-w-6xl">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <Users className="w-8 h-8 text-primary-600" />
            Team Activity
          </h1>
          <p className="text-slate-600 mt-2">
            Real-time view of your team's tracking status
          </p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Summary cards */}
      {data && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-500">Total Members</p>
              <Users className="w-4 h-4 text-blue-500" />
            </div>
            <p className="text-3xl font-bold text-slate-900">
              {data.total_members}
            </p>
          </div>
          <div className="bg-white rounded-xl border border-green-100 shadow-sm p-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-500">Currently Tracking</p>
              <Wifi className="w-4 h-4 text-green-500" />
            </div>
            <p className="text-3xl font-bold text-green-600">
              {data.members_tracking}
            </p>
          </div>
          <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-500">Offline</p>
              <WifiOff className="w-4 h-4 text-slate-400" />
            </div>
            <p className="text-3xl font-bold text-slate-900">
              {data.total_members - data.members_tracking}
            </p>
          </div>
        </div>
      )}

      {/* Team Members List */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <h2 className="text-lg font-semibold text-slate-900">Members</h2>
        </div>

        {loading && !data ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-600 border-t-transparent mx-auto mb-4" />
            <p className="text-slate-500 text-sm">Loading team data...</p>
          </div>
        ) : !data || data.members.length === 0 ? (
          <div className="p-12 text-center">
            <Users className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 text-sm">No team members found</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {data.members.map((member) => (
              <div
                key={member.user_id}
                className="px-6 py-4 flex items-center justify-between hover:bg-slate-50 transition-colors"
              >
                {/* Left: Avatar + Info */}
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <div className="w-10 h-10 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-sm font-bold text-white">
                      {member.first_name[0]}
                      {member.last_name[0]}
                    </div>
                    {member.is_tracking && (
                      <span className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-green-500 border-2 border-white rounded-full" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">
                      {member.first_name} {member.last_name}
                    </p>
                    <p className="text-xs text-slate-500">{member.email}</p>
                  </div>
                </div>

                {/* Center: Status */}
                <div className="flex-1 mx-8">
                  {member.is_tracking ? (
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      <span className="text-sm text-green-700 font-medium">
                        Tracking
                      </span>
                      {member.active_entry_description && (
                        <span className="text-xs text-slate-400 ml-2 truncate max-w-[200px]">
                          {member.active_entry_description}
                        </span>
                      )}
                      {member.active_entry_start_time && (
                        <span className="text-xs text-slate-400 ml-1">
                          ({formatElapsed(member.active_entry_start_time)})
                        </span>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 bg-slate-300 rounded-full" />
                      <span className="text-sm text-slate-400">Offline</span>
                    </div>
                  )}
                </div>

                {/* Right: Stats */}
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <div className="flex items-center gap-1 text-sm font-medium text-slate-900">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      {formatHM(member.today_seconds)}
                    </div>
                    <p className="text-xs text-slate-400">today</p>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center gap-1 text-sm font-medium text-slate-900">
                      <Zap className="w-3.5 h-3.5 text-amber-400" />
                      {member.avg_activity_percent}%
                    </div>
                    <p className="text-xs text-slate-400">activity</p>
                  </div>
                  <span
                    className={`text-xs px-2 py-1 rounded-full font-medium capitalize ${
                      member.role === "org_admin"
                        ? "bg-purple-50 text-purple-700"
                        : member.role === "manager"
                        ? "bg-blue-50 text-blue-700"
                        : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {member.role.replace("_", " ")}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}