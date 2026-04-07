"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Area,
  AreaChart,
} from "recharts";
import {
  BarChart3,
  TrendingUp,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  Zap,
  CalendarDays,
  Minus,
} from "lucide-react";

interface DailyItem {
  date: string;
  total_seconds: number;
  entries: number;
  avg_activity_percent: number;
}

interface WeeklyReport {
  this_week_seconds: number;
  this_week_entries: number;
  this_week_avg_activity: number;
  last_week_seconds: number;
  last_week_entries: number;
  last_week_avg_activity: number;
  change_percent: number;
}

interface TrendItem {
  date: string;
  avg_activity_percent: number;
  total_seconds: number;
}

interface AppItem {
  app_name: string;
  category: string;
  total_seconds: number;
  session_count: number;
}

function formatHM(s: number): string {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (h === 0 && m === 0) return "0m";
  if (h === 0) return `${m}m`;
  return `${h}h ${m}m`;
}

function formatDateShort(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default function ReportsPage() {
  const [daily, setDaily] = useState<DailyItem[]>([]);
  const [weekly, setWeekly] = useState<WeeklyReport | null>(null);
  const [trend, setTrend] = useState<TrendItem[]>([]);
  const [apps, setApps] = useState<AppItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      const [dailyRes, weeklyRes, trendRes, appRes] = await Promise.allSettled([
        apiClient.get("/reports/daily-breakdown"),
        apiClient.get("/reports/weekly"),
        apiClient.get("/reports/productivity-trend?days=14"),
        apiClient.get("/reports/app-usage"),
      ]);

      if (dailyRes.status === "fulfilled") setDaily(dailyRes.value.data.days || []);
      if (weeklyRes.status === "fulfilled") setWeekly(weeklyRes.value.data);
      if (trendRes.status === "fulfilled") setTrend(trendRes.value.data.days || []);
      if (appRes.status === "fulfilled") setApps(appRes.value.data.apps || []);
      setLoading(false);
    };
    load();
  }, []);

  const chartData = daily.map((d) => ({
    name: formatDateShort(d.date),
    hours: +(d.total_seconds / 3600).toFixed(1),
    activity: d.avg_activity_percent,
    entries: d.entries,
  }));

  const trendData = trend.map((t) => ({
    name: formatDateShort(t.date),
    activity: t.avg_activity_percent,
    hours: +(t.total_seconds / 3600).toFixed(1),
  }));

  const changeIsPositive = (weekly?.change_percent || 0) >= 0;

  return (
    <div className="p-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
          <BarChart3 className="w-8 h-8 text-primary-600" />
          Reports & Analytics
        </h1>
        <p className="text-slate-600 mt-2">
          Track your productivity trends and work patterns
        </p>
      </div>

      {/* Weekly Comparison Cards */}
      {weekly && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-500">This Week</p>
              <Clock className="w-4 h-4 text-blue-500" />
            </div>
            <p className="text-2xl font-bold text-slate-900">
              {loading ? "..." : formatHM(weekly.this_week_seconds)}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              {weekly.this_week_entries} entries
            </p>
          </div>

          <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-500">Last Week</p>
              <CalendarDays className="w-4 h-4 text-slate-400" />
            </div>
            <p className="text-2xl font-bold text-slate-900">
              {loading ? "..." : formatHM(weekly.last_week_seconds)}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              {weekly.last_week_entries} entries
            </p>
          </div>

          <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-500">Week Change</p>
              {weekly.change_percent > 0 ? (
                <ArrowUpRight className="w-4 h-4 text-green-500" />
              ) : weekly.change_percent < 0 ? (
                <ArrowDownRight className="w-4 h-4 text-red-500" />
              ) : (
                <Minus className="w-4 h-4 text-slate-400" />
              )}
            </div>
            <p
              className={`text-2xl font-bold ${
                changeIsPositive ? "text-green-600" : "text-red-600"
              }`}
            >
              {changeIsPositive ? "+" : ""}
              {weekly.change_percent}%
            </p>
            <p className="text-xs text-slate-400 mt-1">vs last week</p>
          </div>

          <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-slate-500">Avg Activity</p>
              <Zap className="w-4 h-4 text-amber-500" />
            </div>
            <p className="text-2xl font-bold text-slate-900">
              {weekly.this_week_avg_activity}%
            </p>
            <p className="text-xs text-slate-400 mt-1">this week</p>
          </div>
        </div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Daily Hours Chart */}
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">
            Daily Hours (Last 7 Days)
          </h2>
          {chartData.length === 0 ? (
            <div className="flex items-center justify-center h-64 text-slate-400 text-sm">
              No data yet. Start tracking time to see your chart.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#64748b" }} />
                <YAxis
                  tick={{ fontSize: 12, fill: "#64748b" }}
                  label={{
                    value: "Hours",
                    angle: -90,
                    position: "insideLeft",
                    style: { fontSize: 12, fill: "#64748b" },
                  }}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: 8,
                    border: "1px solid #e2e8f0",
                    fontSize: 13,
                  }}
                  formatter={(value: number) => [`${value}h`, "Hours"]}
                />
                <Bar dataKey="hours" fill="#4f46e5" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Productivity Trend */}
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary-600" />
            Productivity Trend (14 Days)
          </h2>
          {trendData.length === 0 ? (
            <div className="flex items-center justify-center h-64 text-slate-400 text-sm">
              No activity data yet.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="colorActivity" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#4f46e5" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#64748b" }} />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fontSize: 12, fill: "#64748b" }}
                  label={{
                    value: "Activity %",
                    angle: -90,
                    position: "insideLeft",
                    style: { fontSize: 12, fill: "#64748b" },
                  }}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: 8,
                    border: "1px solid #e2e8f0",
                    fontSize: 13,
                  }}
                  formatter={(value: number) => [`${value}%`, "Activity"]}
                />
                <Area
                  type="monotone"
                  dataKey="activity"
                  stroke="#4f46e5"
                  strokeWidth={2}
                  fill="url(#colorActivity)"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* App Usage */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">
          App Usage (Today)
        </h2>
        {apps.length === 0 ? (
          <div className="text-center py-12">
            <Zap className="w-10 h-10 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 text-sm">
              App usage data will appear once the desktop agent starts reporting
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {apps.map((app, i) => {
              const maxSecs = apps[0]?.total_seconds || 1;
              const pct = Math.round((app.total_seconds / maxSecs) * 100);
              const categoryColors: Record<string, string> = {
                productive: "bg-green-500",
                unproductive: "bg-red-400",
                neutral: "bg-slate-400",
                uncategorized: "bg-blue-400",
              };
              return (
                <div key={i} className="flex items-center gap-4">
                  <div className="w-36 text-sm font-medium text-slate-900 truncate">
                    {app.app_name}
                  </div>
                  <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        categoryColors[app.category] || "bg-blue-400"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <div className="w-20 text-right text-sm text-slate-600">
                    {formatHM(app.total_seconds)}
                  </div>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      app.category === "productive"
                        ? "bg-green-50 text-green-700"
                        : app.category === "unproductive"
                        ? "bg-red-50 text-red-600"
                        : "bg-slate-100 text-slate-600"
                    }`}
                  >
                    {app.category}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}