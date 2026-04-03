"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";
import {
  LayoutDashboard,
  Users,
  FolderOpen,
  Clock,
  Settings,
  LogOut,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/team", label: "Team", icon: Users },
  { href: "/dashboard/projects", label: "Projects", icon: FolderOpen },
  { href: "/dashboard/time-tracking", label: "Time Tracking", icon: Clock },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { logout, user } = useAuthStore();

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shadow-sm">
      {/* Logo */}
      <div className="px-6 py-6 border-b border-slate-100">
        <h1 className="text-2xl font-bold text-primary-700">WebWork</h1>
        <p className="text-xs text-slate-500 mt-1">Tracking Platform</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-6 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            pathname === item.href || pathname.startsWith(item.href + "/");

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-primary-50 text-primary-700 border border-primary-200"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      <div className="px-4 py-5 border-t border-slate-100 bg-slate-50">
        <div className="mb-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-sm font-bold text-white flex-shrink-0">
              {user?.first_name?.[0]}
              {user?.last_name?.[0]}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-900">
                {user?.first_name} {user?.last_name}
              </p>
              <p className="text-xs text-slate-500 truncate">{user?.email}</p>
              {user?.role && (
                <p className="text-xs font-medium text-primary-600 mt-0.5 capitalize">
                  {user.role}
                </p>
              )}
            </div>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-slate-700 hover:text-red-700 hover:bg-red-50 rounded-lg transition-all duration-200 border border-transparent hover:border-red-200"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
