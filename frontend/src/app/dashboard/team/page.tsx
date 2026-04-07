"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import {
  canInvite,
  invitableRoles,
  ROLE_LABELS,
  ROLE_COLORS,
  isAbove,
  type RoleKey,
} from "@/lib/roles";
import { Users, UserPlus, Mail, Shield, Trash2 } from "lucide-react";

interface TeamMember {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  created_at?: string;
}

async function fetchTeamMembers() {
  const res = await apiClient.get("/users");
  return res.data?.users || res.data || [];
}

export default function TeamPage() {
  const { user } = useAuthStore();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    role: "employee",
  });
  const [inviteLoading, setInviteLoading] = useState(false);
  const [inviteError, setInviteError] = useState("");
  const [inviteSuccess, setInviteSuccess] = useState(false);

  const userRole = user?.role || "employee";
  const allowedRoles = invitableRoles(userRole);
  const canInviteUsers = canInvite(userRole);

  const {
    data: teamMembers = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["team-members"],
    queryFn: fetchTeamMembers,
  });

  const resetForm = () => {
    setFormData({ email: "", password: "", first_name: "", last_name: "", role: "employee" });
    setInviteError("");
    setInviteSuccess(false);
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviteError("");
    setInviteSuccess(false);
    setInviteLoading(true);

    try {
      await apiClient.post("/users", {
        email: formData.email,
        password: formData.password,
        first_name: formData.first_name,
        last_name: formData.last_name,
        role: formData.role,
      });
      setInviteSuccess(true);
      resetForm();
      setTimeout(() => {
        setIsModalOpen(false);
        setInviteSuccess(false);
        refetch();
      }, 1500);
    } catch (err: any) {
      setInviteError(
        err.response?.data?.detail || "Failed to create user"
      );
    } finally {
      setInviteLoading(false);
    }
  };

  const handleDeactivate = async (memberId: string) => {
    if (!window.confirm("Are you sure you want to deactivate this user?")) return;
    try {
      await apiClient.delete(`/users/${memberId}`);
      refetch();
    } catch (err: any) {
      alert(err.response?.data?.detail || "Failed to deactivate user");
    }
  };

  return (
    <div className="p-8 max-w-6xl">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <Users className="w-8 h-8 text-primary-600" />
            Team Members
          </h1>
          <p className="text-slate-600 mt-2">
            {canInviteUsers
              ? "Manage your team and invite new members"
              : "View your team members"}
          </p>
        </div>
        {canInviteUsers && (
          <button
            onClick={() => { resetForm(); setIsModalOpen(true); }}
            className="flex items-center gap-2 px-4 py-2.5 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors shadow-md"
          >
            <UserPlus className="w-5 h-5" />
            Add Member
          </button>
        )}
      </div>

      {/* Invite Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-slate-900 mb-4">
              Add Team Member
            </h2>

            {inviteSuccess && (
              <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                User created successfully!
              </div>
            )}

            {inviteError && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {inviteError}
              </div>
            )}

            <form onSubmit={handleInvite} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-semibold text-slate-900 mb-1.5">
                    First Name
                  </label>
                  <input
                    type="text"
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    disabled={inviteLoading}
                    className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none disabled:bg-slate-100 text-sm"
                    placeholder="John"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-slate-900 mb-1.5">
                    Last Name
                  </label>
                  <input
                    type="text"
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    disabled={inviteLoading}
                    className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none disabled:bg-slate-100 text-sm"
                    placeholder="Doe"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-900 mb-1.5">
                  Email Address
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  disabled={inviteLoading}
                  className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none disabled:bg-slate-100 text-sm"
                  placeholder="user@company.com"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-900 mb-1.5">
                  Temporary Password
                </label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  disabled={inviteLoading}
                  className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none disabled:bg-slate-100 text-sm"
                  placeholder="Min 8 characters"
                  minLength={8}
                  required
                />
                <p className="text-xs text-slate-500 mt-1">
                  The user can change this after their first login.
                </p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-900 mb-1.5">
                  Role
                </label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  disabled={inviteLoading}
                  className="w-full px-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none disabled:bg-slate-100 text-sm"
                >
                  {allowedRoles.map((role) => (
                    <option key={role} value={role}>
                      {ROLE_LABELS[role] || role}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-slate-500 mt-1">
                  {userRole === "org_admin"
                    ? "As Admin, you can add Managers and Employees."
                    : "As Manager, you can add Employees."}
                </p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  disabled={inviteLoading}
                  className="flex-1 px-4 py-2.5 bg-slate-100 text-slate-900 font-medium rounded-lg hover:bg-slate-200 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={inviteLoading}
                  className="flex-1 px-4 py-2.5 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {inviteLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                      Creating...
                    </>
                  ) : (
                    "Create User"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Team Members Table */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4" />
            <p className="text-slate-600">Loading team members...</p>
          </div>
        ) : error ? (
          <div className="p-12 text-center">
            <p className="text-red-600">Failed to load team members</p>
          </div>
        ) : teamMembers.length === 0 ? (
          <div className="p-12 text-center">
            <Users className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-600">No team members yet</p>
            {canInviteUsers && (
              <button
                onClick={() => { resetForm(); setIsModalOpen(true); }}
                className="mt-4 text-primary-600 font-medium hover:underline"
              >
                Add your first team member
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-slate-900">
                    Joined
                  </th>
                  {canInviteUsers && (
                    <th className="px-6 py-3 text-right text-sm font-semibold text-slate-900">
                      Actions
                    </th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {teamMembers.map((member: TeamMember) => {
                  const roleLabel = ROLE_LABELS[member.role as RoleKey] || member.role;
                  const roleColor = ROLE_COLORS[member.role as RoleKey] || "bg-slate-100 text-slate-700";
                  const isSelf = member.id === user?.id;
                  const canDelete = !isSelf && isAbove(userRole, member.role);

                  return (
                    <tr
                      key={member.id}
                      className="hover:bg-slate-50 transition-colors"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-primary-400 to-primary-600 rounded-full flex items-center justify-center text-sm font-bold text-white flex-shrink-0">
                            {member.first_name?.[0]}
                            {member.last_name?.[0]}
                          </div>
                          <div>
                            <p className="font-medium text-slate-900">
                              {member.first_name} {member.last_name}
                              {isSelf && (
                                <span className="ml-2 text-xs text-primary-600 font-normal">(you)</span>
                              )}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2 text-slate-600 text-sm">
                          <Mail className="w-4 h-4 text-slate-400" />
                          {member.email}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${roleColor}`}
                        >
                          <Shield className="w-3 h-3" />
                          {roleLabel}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              member.is_active ? "bg-green-500" : "bg-slate-400"
                            }`}
                          />
                          <span
                            className={`text-sm ${
                              member.is_active ? "text-green-700" : "text-slate-500"
                            }`}
                          >
                            {member.is_active ? "Active" : "Deactivated"}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-600">
                        {member.created_at
                          ? new Date(member.created_at).toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                              year: "numeric",
                            })
                          : "-"}
                      </td>
                      {canInviteUsers && (
                        <td className="px-6 py-4 text-right">
                          {canDelete && member.is_active && (
                            <button
                              onClick={() => handleDeactivate(member.id)}
                              className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                              title="Deactivate user"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
