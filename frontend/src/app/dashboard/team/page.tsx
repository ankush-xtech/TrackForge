"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import { Users, UserPlus, Mail, Badge, Eye, EyeOff } from "lucide-react";

interface TeamMember {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  status?: string;
  created_at?: string;
}

async function fetchTeamMembers() {
  const res = await apiClient.get("/users");
  return res.data?.users || res.data || [];
}

export default function TeamPage() {
  const { user } = useAuthStore();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("employee");
  const [inviteLoading, setInviteLoading] = useState(false);
  const [inviteError, setInviteError] = useState("");
  const [inviteSuccess, setInviteSuccess] = useState(false);

  const {
    data: teamMembers = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["team-members"],
    queryFn: fetchTeamMembers,
  });

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setInviteError("");
    setInviteSuccess(false);
    setInviteLoading(true);

    try {
      await apiClient.post("/users/invite", {
        email: inviteEmail,
        role: inviteRole,
      });
      setInviteSuccess(true);
      setInviteEmail("");
      setInviteRole("employee");
      setTimeout(() => {
        setIsModalOpen(false);
        refetch();
      }, 1500);
    } catch (err: any) {
      setInviteError(
        err.response?.data?.detail || "Failed to send invitation"
      );
    } finally {
      setInviteLoading(false);
    }
  };

  const isAdmin = user?.role === "admin" || user?.role === "manager";

  const getRoleColor = (role: string) => {
    switch (role?.toLowerCase()) {
      case "admin":
        return "bg-red-100 text-red-800";
      case "manager":
        return "bg-purple-100 text-purple-800";
      case "employee":
        return "bg-blue-100 text-blue-800";
      default:
        return "bg-slate-100 text-slate-800";
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status?.toLowerCase()) {
      case "active":
        return "text-green-600";
      case "inactive":
        return "text-slate-400";
      default:
        return "text-slate-500";
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
            Manage your team and their permissions
          </p>
        </div>
        {isAdmin && (
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors shadow-md"
          >
            <UserPlus className="w-5 h-5" />
            Invite Member
          </button>
        )}
      </div>

      {/* Invite Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-slate-900 mb-4">
              Invite Team Member
            </h2>

            {inviteSuccess && (
              <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                Invitation sent successfully!
              </div>
            )}

            {inviteError && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {inviteError}
              </div>
            )}

            <form onSubmit={handleInvite} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-slate-900 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  disabled={inviteLoading}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none disabled:bg-slate-100"
                  placeholder="user@company.com"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-900 mb-2">
                  Role
                </label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  disabled={inviteLoading}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none disabled:bg-slate-100"
                >
                  <option value="employee">Employee</option>
                  <option value="manager">Manager</option>
                  {user?.role === "admin" && (
                    <option value="admin">Admin</option>
                  )}
                </select>
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
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                      Sending...
                    </>
                  ) : (
                    "Send Invitation"
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
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
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
            {isAdmin && (
              <button
                onClick={() => setIsModalOpen(true)}
                className="mt-4 text-primary-600 font-medium hover:underline"
              >
                Invite your first team member
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
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {teamMembers.map((member: TeamMember) => (
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
                        className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${getRoleColor(
                          member.role
                        )}`}
                      >
                        <Badge className="w-3 h-3" />
                        {member.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-1">
                        {member.status === "active" ? (
                          <>
                            <Eye
                              className={`w-4 h-4 ${getStatusColor(
                                member.status
                              )}`}
                            />
                            <span className={`text-sm ${getStatusColor(member.status)}`}>
                              Active
                            </span>
                          </>
                        ) : (
                          <>
                            <EyeOff
                              className={`w-4 h-4 ${getStatusColor(
                                member.status || "inactive"
                              )}`}
                            />
                            <span className={`text-sm ${getStatusColor(member.status || "inactive")}`}>
                              Inactive
                            </span>
                          </>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600">
                      {member.created_at
                        ? new Date(member.created_at).toLocaleDateString()
                        : "-"}
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
