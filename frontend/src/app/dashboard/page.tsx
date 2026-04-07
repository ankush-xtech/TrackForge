"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth-store";
import { apiClient } from "@/lib/api-client";
import { isAtLeast, canInvite, ROLE_LABELS, type RoleKey } from "@/lib/roles";
import {
  BarChart3,
  Users,
  Clock,
  TrendingUp,
  Zap,
  Activity,
  Play,
  UserPlus,
} from "lucide-react";

interface DashboardStats {
  totalProjects: number;
  teamMembers: number;
  todaySeconds: number;
  isTracking: boolean;
  weekSeconds: number;
  entriestoday: number;
}

function formatHM(totalSeconds: number): string {
  const h = Math.floor(totalSeconds / 3600);
  const m = Math.floor((totalSeconds % 3600) / 60);
  if (h === 0 && m === 0) return "0h 0m";
  if (h === 0) return `${m}m`;
  return `${h}h ${m}m`;
}

export default function DashboardPage() {
  const { user } = useAuthStore();
  const [stats, setStats] = useState<DashboardStats>({
    totalProjects: 0,
    teamMembers: 0,
    todaySeconds: 0,
    isTracking: false,
    weekSeconds: 0,
    entriestoday: 0,
  });
  const [recentEntries, setRecentEntries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const userRole = user?.role || "employee";
  const roleLabel = ROLE_LABELS[userRole as RoleKey] || userRole;

  useEffect(() => {
    const loadDashboard = async () => {
      setLoading(true);
      try {
        // Build parallel requests based on role
        const requests: Promise<any>[] = [
          apiClient.get("/tracking/summary"),
          apiClient.get("/tracking/time-entries?per_page=5"),
        ];

        // Only admin+ fetches projects and users
        if (isAtLeast(userRole, "org_admin")) {
          requests.push(apiClient.get("/projects"));
          requests.push(apiClient.get("/users"));
        } else if (isAtLeast(userRole, "manager")) {
          // Managers can see users (filtered by backend)
          requests.push(apiClient.get("/projects"));
          requests.push(apiClient.get("/users"));
        }

        const results = await Promise.allSettled(requests);

        const summary =
          results[0].status === "fulfilled" ? results[0].value.data : {};
        const entries =
          results[1].status === "fulfilled" ? results[1].value.data || [] : [];
        const projects =
          results.length > 2 && results[2].status === "fulfilled"
            ? results[2].value.data?.projects || results[2].value.data || []
            : [];
        const users =
          results.length > 3 && results[3].status === "fulfilled"
            ? results[3].value.data?.users || results[3].value.data || []
            : [];

        setStats({
          totalProjects: Array.isArray(projects) ? projects.length : 0,
          teamMembers: Array.isArray(users) ? users.length : 0,
          todaySeconds: summary.today_seconds || 0,
          isTracking: summary.is_tracking || false,
          weekSeconds: summary.week_seconds || 0,
          entriestoday: summary.entries_today || 0,
        });
        setRecentEntries(entries.slice(0, 5));
      } catch {
        // fail silently
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, [userRole]);

  // ── Build stat cards based on role ──
  const statCards: { label: string; value: string; icon: any; color: string; borderColor: string }[] = [
    {
      label: "Hours Today",
      value: formatHM(stats.todaySeconds),
      icon: Clock,
      color: "bg-purple-50 text-purple-600",
      borderColor: "border-purple-200",
    },
    {
      label: "This Week",
      value: formatHM(stats.weekSeconds),
      icon: TrendingUp,
      color: "bg-amber-50 text-amber-600",
      borderColor: "border-amber-200",
    },
  ];

  // Manager+ sees team count
  if (isAtLeast(userRole, "manager")) {
    statCards.push({
      label: "Team Members",
      value: String(stats.teamMembers),
      icon: Users,
      color: "bg-green-50 text-green-600",
      borderColor: "border-green-200",
    });
  }

  // Admin+ sees project count
  if (isAtLeast(userRole, "org_admin")) {
    statCards.push({
      label: "Total Projects",
      value: String(stats.totalProjects),
      icon: BarChart3,
      color: "bg-blue-50 text-blue-600",
      borderColor: "border-blue-200",
    });
  }

  // ── Build quick actions based on role ──
  const quickActions: { label: string; icon: any; href: string }[] = [
    { label: "Start Tracking", icon: Play, href: "/dashboard/time-tracking" },
  ];

  if (isAtLeast(userRole, "org_admin")) {
    quickActions.push({ label: "Create Project", icon: Zap, href: "/dashboard/projects" });
  }

  if (canInvite(userRole)) {
    quickActions.push({ label: "Invite Team Member", icon: UserPlus, href: "/dashboard/team" });
  }

  return (
    <div className="p-8 max-w-7xl">
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">
          Welcome back, {user?.first_name}
        </h1>
        <p className="text-slate-600 mt-2">
          {userRole === "employee"
            ? "Here's your activity overview"
            : userRole === "manager"
            ? "Here's your team's overview"
            : "Here's what's happening across your organization"}
        </p>
        {stats.isTracking && (
          <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 bg-green-50 border border-green-200 rounded-full">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm text-green-700 font-medium">
              Timer is running
            </span>
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className={`grid grid-cols-1 md:grid-cols-2 ${statCards.length >= 4 ? "lg:grid-cols-4" : statCards.length === 3 ? "lg:grid-cols-3" : "lg:grid-cols-2"} gap-6 mb-8`}>
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.label}
              className={`bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow ${stat.borderColor} border`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
              <p className="text-sm text-slate-600 font-medium mb-1">
                {stat.label}
              </p>
              <p className="text-3xl font-bold text-slate-900">
                {loading ? (
                  <span className="inline-block w-16 h-8 bg-slate-100 rounded animate-pulse" />
                ) : (
                  stat.value
                )}
              </p>
            </div>
          );
        })}
      </div>

      {/* Quick Actions and Recent Entries */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Quick Actions */}
        <div className="lg:col-span-1 bg-white p-6 rounded-xl border border-slate-100 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">
            Quick Actions
          </h2>
          <div className="space-y-3">
            {quickActions.map((action) => {
              const Icon = action.icon;
              return (
                <Link
                  key={action.label}
                  href={action.href}
                  className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 hover:bg-primary-50 text-slate-700 hover:text-primary-700 transition-colors group"
                >
                  <Icon className="w-5 h-5 group-hover:scale-110 transition-transform" />
                  <span className="text-sm font-medium">{action.label}</span>
                </Link>
              );
            })}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-100 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">
            Recent Time Entries
          </h2>
          {recentEntries.length === 0 ? (
            <div className="text-center py-8">
              <Activity className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500 text-sm">
                Activity data will appear here once you start tracking
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {recentEntries.map((entry: any) => (
                <div
                  key={entry.id}
                  className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        entry.end_time ? "bg-slate-400" : "bg-green-500 animate-pulse"
                      }`}
                    />
                    <div>
                      <p className="text-sm font-medium text-slate-900">
                        {entry.description || "No description"}
                      </p>
                      <p className="text-xs text-slate-500">
                        {new Date(entry.start_time).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                        })}{" "}
                        at{" "}
                        {new Date(entry.start_time).toLocaleTimeString("en-US", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                  </div>
                  <span className="text-sm font-mono font-medium text-slate-700">
                    {entry.end_time
                      ? formatHM(entry.duration_seconds)
                      : "Running"}
                  </span>
                </div>
              ))}
              <Link
                href="/dashboard/time-tracking"
                className="block text-center text-sm text-primary-600 font-medium hover:underline pt-2"
              >
                View all entries
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Getting Started — only for admin role */}
      {isAtLeast(userRole, "org_admin") && (
        <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">
            Organization Overview
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center py-6">
              <div
                className={`w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center ${
                  stats.teamMembers > 1
                    ? "bg-green-100 text-green-600"
                    : "bg-slate-100 text-slate-400"
                }`}
              >
                <Users className="w-6 h-6" />
              </div>
              <p className="text-sm font-medium text-slate-900 mb-1">
                {stats.teamMembers > 1
                  ? `${stats.teamMembers} members`
                  : "Invite your team"}
              </p>
              <Link
                href="/dashboard/team"
                className="text-primary-600 text-xs font-medium hover:underline"
              >
                Manage team
              </Link>
            </div>
            <div className="text-center py-6">
              <div
                className={`w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center ${
                  stats.totalProjects > 0
                    ? "bg-green-100 text-green-600"
                    : "bg-slate-100 text-slate-400"
                }`}
              >
                <TrendingUp className="w-6 h-6" />
              </div>
              <p className="text-sm font-medium text-slate-900 mb-1">
                {stats.totalProjects > 0
                  ? `${stats.totalProjects} projects`
                  : "Create a project"}
              </p>
              <Link
                href="/dashboard/projects"
                className="text-primary-600 text-xs font-medium hover:underline"
              >
                Manage projects
              </Link>
            </div>
            <div className="text-center py-6">
              <div
                className={`w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center ${
                  stats.todaySeconds > 0
                    ? "bg-green-100 text-green-600"
                    : "bg-slate-100 text-slate-400"
                }`}
              >
                <Clock className="w-6 h-6" />
              </div>
              <p className="text-sm font-medium text-slate-900 mb-1">
                {stats.todaySeconds > 0
                  ? `${formatHM(stats.todaySeconds)} tracked today`
                  : "Start tracking time"}
              </p>
              <Link
                href="/dashboard/time-tracking"
                className="text-primary-600 text-xs font-medium hover:underline"
              >
                Time tracking
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
