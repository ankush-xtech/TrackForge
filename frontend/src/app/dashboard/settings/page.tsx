"use client";

import { useAuthStore } from "@/stores/auth-store";
import {
  Settings,
  User,
  Bell,
  Lock,
  LogOut,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";

export default function SettingsPage() {
  const { user, logout } = useAuthStore();
  const [activeTab, setActiveTab] = useState("profile");
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  const settingsTabs = [
    { id: "profile", label: "Profile", icon: User },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "security", label: "Security", icon: Lock },
  ];

  return (
    <div className="p-8 max-w-6xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
          <Settings className="w-8 h-8 text-primary-600" />
          Settings
        </h1>
        <p className="text-slate-600 mt-2">
          Manage your account and preferences
        </p>
      </div>

      {/* Tabs */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden sticky top-8">
            <nav className="flex flex-col">
              {settingsTabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center justify-between px-4 py-4 border-l-4 text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? "bg-primary-50 border-l-primary-600 text-primary-700"
                        : "border-l-transparent text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="w-5 h-5" />
                      {tab.label}
                    </div>
                    {activeTab === tab.id && (
                      <ChevronRight className="w-4 h-4" />
                    )}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          {/* Profile Tab */}
          {activeTab === "profile" && (
            <div className="space-y-6">
              <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
                <h2 className="text-lg font-semibold text-slate-900 mb-6">
                  Profile Information
                </h2>

                <div className="space-y-6">
                  {/* Avatar */}
                  <div className="flex items-center gap-6">
                    <div className="w-16 h-16 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-2xl font-bold text-white flex-shrink-0">
                      {user?.first_name?.[0]}
                      {user?.last_name?.[0]}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-900 mb-2">
                        Profile Picture
                      </p>
                      <button className="px-4 py-2 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors">
                        Upload Photo
                      </button>
                    </div>
                  </div>

                  <div className="border-t border-slate-200 pt-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-semibold text-slate-900 mb-2">
                          First Name
                        </label>
                        <input
                          type="text"
                          value={user?.first_name || ""}
                          disabled
                          className="w-full px-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 text-slate-600"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-slate-900 mb-2">
                          Last Name
                        </label>
                        <input
                          type="text"
                          value={user?.last_name || ""}
                          disabled
                          className="w-full px-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 text-slate-600"
                        />
                      </div>
                      <div className="md:col-span-2">
                        <label className="block text-sm font-semibold text-slate-900 mb-2">
                          Email
                        </label>
                        <input
                          type="email"
                          value={user?.email || ""}
                          disabled
                          className="w-full px-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 text-slate-600"
                        />
                      </div>
                      <div className="md:col-span-2">
                        <label className="block text-sm font-semibold text-slate-900 mb-2">
                          Role
                        </label>
                        <div className="px-4 py-2.5 border border-slate-300 rounded-lg bg-slate-50 text-slate-600 capitalize font-medium">
                          {user?.role || "Unknown"}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="border-t border-slate-200 pt-6">
                    <button className="px-6 py-2.5 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors">
                      Save Changes
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === "notifications" && (
            <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-6">
                Notification Preferences
              </h2>

              <div className="space-y-4">
                <label className="flex items-center gap-3 p-4 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="w-5 h-5 text-primary-600 rounded"
                  />
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">
                      Email notifications
                    </p>
                    <p className="text-sm text-slate-600">
                      Receive updates via email
                    </p>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-4 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="w-5 h-5 text-primary-600 rounded"
                  />
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">
                      Project updates
                    </p>
                    <p className="text-sm text-slate-600">
                      Get notified about project changes
                    </p>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-4 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors">
                  <input
                    type="checkbox"
                    className="w-5 h-5 text-primary-600 rounded"
                  />
                  <div className="flex-1">
                    <p className="font-medium text-slate-900">
                      Team notifications
                    </p>
                    <p className="text-sm text-slate-600">
                      Notify me about team activity
                    </p>
                  </div>
                </label>
              </div>
            </div>
          )}

          {/* Security Tab */}
          {activeTab === "security" && (
            <div className="space-y-6">
              <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6">
                <h2 className="text-lg font-semibold text-slate-900 mb-6">
                  Security Settings
                </h2>

                <div className="space-y-6">
                  <div>
                    <h3 className="font-medium text-slate-900 mb-3">
                      Change Password
                    </h3>
                    <button className="px-6 py-2.5 border border-slate-300 text-slate-700 font-medium rounded-lg hover:bg-slate-50 transition-colors">
                      Update Password
                    </button>
                  </div>

                  <div className="border-t border-slate-200 pt-6">
                    <h3 className="font-medium text-slate-900 mb-3">
                      Two-Factor Authentication
                    </h3>
                    <p className="text-sm text-slate-600 mb-4">
                      Add an extra layer of security to your account
                    </p>
                    <button className="px-6 py-2.5 border border-slate-300 text-slate-700 font-medium rounded-lg hover:bg-slate-50 transition-colors">
                      Enable 2FA
                    </button>
                  </div>

                  <div className="border-t border-slate-200 pt-6">
                    <h3 className="font-medium text-slate-900 mb-3">
                      Sign Out
                    </h3>
                    <p className="text-sm text-slate-600 mb-4">
                      Sign out from all devices
                    </p>
                    <button
                      onClick={() => setShowLogoutConfirm(true)}
                      className="px-6 py-2.5 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2"
                    >
                      <LogOut className="w-4 h-4" />
                      Sign Out
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Logout Confirm Modal */}
      {showLogoutConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-sm w-full p-6">
            <h2 className="text-xl font-bold text-slate-900 mb-2">
              Sign out?
            </h2>
            <p className="text-slate-600 mb-6">
              Are you sure you want to sign out? You'll need to sign in again to access your account.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowLogoutConfirm(false)}
                className="flex-1 px-4 py-2.5 bg-slate-100 text-slate-900 font-medium rounded-lg hover:bg-slate-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={logout}
                className="flex-1 px-4 py-2.5 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
