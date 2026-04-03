"use client";

import { useAuthStore } from "@/stores/auth-store";
import {
  BarChart3,
  Users,
  Clock,
  TrendingUp,
  Zap,
  Activity,
} from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuthStore();

  const stats = [
    {
      label: "Total Projects",
      value: "0",
      icon: BarChart3,
      color: "bg-blue-50 text-blue-600",
      borderColor: "border-blue-200",
    },
    {
      label: "Team Members",
      value: "0",
      icon: Users,
      color: "bg-green-50 text-green-600",
      borderColor: "border-green-200",
    },
    {
      label: "Hours Today",
      value: "0h 0m",
      icon: Clock,
      color: "bg-purple-50 text-purple-600",
      borderColor: "border-purple-200",
    },
    {
      label: "Active Now",
      value: "0",
      icon: TrendingUp,
      color: "bg-amber-50 text-amber-600",
      borderColor: "border-amber-200",
    },
  ];

  const quickActions = [
    { label: "Create Project", icon: Zap, href: "/dashboard/projects" },
    { label: "Invite Team Member", icon: Users, href: "/dashboard/team" },
    { label: "View Reports", icon: Activity, href: "/dashboard/settings" },
  ];

  return (
    <div className="p-8 max-w-7xl">
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">
          Welcome back, {user?.first_name}
        </h1>
        <p className="text-slate-600 mt-2">
          Here's what's happening with your team today
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.label}
              className={`bg-white p-6 rounded-xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow ${stat.borderColor} border`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
              <p className="text-sm text-slate-600 font-medium mb-1">
                {stat.label}
              </p>
              <p className="text-3xl font-bold text-slate-900">{stat.value}</p>
            </div>
          );
        })}
      </div>

      {/* Quick Actions and Recent Activity */}
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
                <a
                  key={action.label}
                  href={action.href}
                  className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 hover:bg-primary-50 text-slate-700 hover:text-primary-700 transition-colors group"
                >
                  <Icon className="w-5 h-5 group-hover:scale-110 transition-transform" />
                  <span className="text-sm font-medium">{action.label}</span>
                </a>
              );
            })}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-100 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">
            Recent Activity
          </h2>
          <div className="space-y-4">
            <div className="text-center py-8">
              <Activity className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500 text-sm">
                Activity data will appear here once employees start tracking
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Team Status */}
      <div className="bg-white p-6 rounded-xl border border-slate-100 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">
          Team Status
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center py-8">
            <Users className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 text-sm">No team members yet</p>
            <a
              href="/dashboard/team"
              className="text-primary-600 text-sm font-medium hover:underline mt-2 inline-block"
            >
              Invite your team
            </a>
          </div>
          <div className="text-center py-8">
            <TrendingUp className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 text-sm">No projects created yet</p>
            <a
              href="/dashboard/projects"
              className="text-primary-600 text-sm font-medium hover:underline mt-2 inline-block"
            >
              Create your first project
            </a>
          </div>
          <div className="text-center py-8">
            <Clock className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500 text-sm">No time tracked today</p>
            <a
              href="/dashboard/time-tracking"
              className="text-primary-600 text-sm font-medium hover:underline mt-2 inline-block"
            >
              Start tracking
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
