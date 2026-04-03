"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { useAuthStore } from "@/stores/auth-store";
import {
  FolderOpen,
  Plus,
  Calendar,
  User,
  Clock,
  AlertCircle,
  CheckCircle,
} from "lucide-react";

interface Project {
  id: string;
  name: string;
  status: "active" | "completed" | "paused";
  client?: string;
  budget_hours?: number;
  spent_hours?: number;
  created_at?: string;
  manager_id?: string;
}

async function fetchProjects() {
  const res = await apiClient.get("/projects");
  return res.data;
}

export default function ProjectsPage() {
  const { user } = useAuthStore();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [projectForm, setProjectForm] = useState({
    name: "",
    client: "",
    budget_hours: "",
  });
  const [formError, setFormError] = useState("");
  const [createLoading, setCreateLoading] = useState(false);
  const [createSuccess, setCreateSuccess] = useState(false);

  const {
    data: projects = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["projects"],
    queryFn: fetchProjects,
  });

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    setCreateSuccess(false);
    setCreateLoading(true);

    try {
      await apiClient.post("/projects", {
        name: projectForm.name,
        client: projectForm.client || null,
        budget_hours: projectForm.budget_hours
          ? parseInt(projectForm.budget_hours)
          : null,
        status: "active",
      });
      setCreateSuccess(true);
      setProjectForm({ name: "", client: "", budget_hours: "" });
      setTimeout(() => {
        setIsModalOpen(false);
        refetch();
      }, 1500);
    } catch (err: any) {
      setFormError(
        err.response?.data?.detail || "Failed to create project"
      );
    } finally {
      setCreateLoading(false);
    }
  };

  const isManager = user?.role === "manager" || user?.role === "admin";

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case "active":
        return "bg-green-100 text-green-800";
      case "completed":
        return "bg-blue-100 text-blue-800";
      case "paused":
        return "bg-amber-100 text-amber-800";
      default:
        return "bg-slate-100 text-slate-800";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case "completed":
        return <CheckCircle className="w-4 h-4" />;
      case "paused":
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const getBudgetProgress = (spent: number, budget: number) => {
    if (!budget || budget === 0) return 0;
    return Math.round((spent / budget) * 100);
  };

  return (
    <div className="p-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <FolderOpen className="w-8 h-8 text-primary-600" />
            Projects
          </h1>
          <p className="text-slate-600 mt-2">
            Manage your projects and track progress
          </p>
        </div>
        {isManager && (
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors shadow-md"
          >
            <Plus className="w-5 h-5" />
            New Project
          </button>
        )}
      </div>

      {/* Create Project Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-slate-900 mb-4">
              Create New Project
            </h2>

            {createSuccess && (
              <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
                Project created successfully!
              </div>
            )}

            {formError && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-slate-900 mb-2">
                  Project Name
                </label>
                <input
                  type="text"
                  value={projectForm.name}
                  onChange={(e) =>
                    setProjectForm({ ...projectForm, name: e.target.value })
                  }
                  disabled={createLoading}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none disabled:bg-slate-100"
                  placeholder="Project name"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-900 mb-2">
                  Client (Optional)
                </label>
                <input
                  type="text"
                  value={projectForm.client}
                  onChange={(e) =>
                    setProjectForm({ ...projectForm, client: e.target.value })
                  }
                  disabled={createLoading}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none disabled:bg-slate-100"
                  placeholder="Client name"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-900 mb-2">
                  Budget Hours (Optional)
                </label>
                <input
                  type="number"
                  value={projectForm.budget_hours}
                  onChange={(e) =>
                    setProjectForm({
                      ...projectForm,
                      budget_hours: e.target.value,
                    })
                  }
                  disabled={createLoading}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none disabled:bg-slate-100"
                  placeholder="Total hours budgeted"
                  min="0"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  disabled={createLoading}
                  className="flex-1 px-4 py-2.5 bg-slate-100 text-slate-900 font-medium rounded-lg hover:bg-slate-200 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createLoading}
                  className="flex-1 px-4 py-2.5 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {createLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                      Creating...
                    </>
                  ) : (
                    "Create Project"
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Projects Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center p-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p className="text-slate-600">Loading projects...</p>
          </div>
        </div>
      ) : error ? (
        <div className="flex items-center justify-center p-12">
          <p className="text-red-600">Failed to load projects</p>
        </div>
      ) : projects.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-100 p-12 text-center">
          <FolderOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-600">No projects yet</p>
          {isManager && (
            <button
              onClick={() => setIsModalOpen(true)}
              className="mt-4 text-primary-600 font-medium hover:underline"
            >
              Create your first project
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project: Project) => {
            const progress = getBudgetProgress(
              project.spent_hours || 0,
              project.budget_hours || 0
            );
            const isOverBudget =
              project.budget_hours &&
              project.spent_hours &&
              project.spent_hours > project.budget_hours;

            return (
              <div
                key={project.id}
                className="bg-white rounded-xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow overflow-hidden group"
              >
                {/* Header */}
                <div className="p-6 border-b border-slate-100 bg-gradient-to-r from-primary-50 to-transparent">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-lg font-bold text-slate-900 group-hover:text-primary-600 transition-colors">
                      {project.name}
                    </h3>
                    <span
                      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(
                        project.status
                      )}`}
                    >
                      {getStatusIcon(project.status)}
                      {project.status}
                    </span>
                  </div>
                  {project.client && (
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                      <User className="w-4 h-4" />
                      {project.client}
                    </div>
                  )}
                </div>

                {/* Content */}
                <div className="p-6 space-y-4">
                  {/* Budget */}
                  {project.budget_hours && (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                          <Clock className="w-4 h-4" />
                          <span>Budget Hours</span>
                        </div>
                        <span
                          className={`text-sm font-semibold ${
                            isOverBudget
                              ? "text-red-600"
                              : "text-slate-900"
                          }`}
                        >
                          {project.spent_hours || 0}h /{" "}
                          {project.budget_hours}h
                        </span>
                      </div>
                      <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-full transition-all ${
                            progress <= 50
                              ? "bg-green-500"
                              : progress <= 90
                              ? "bg-amber-500"
                              : "bg-red-500"
                          }`}
                          style={{ width: `${Math.min(progress, 100)}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-slate-600 mt-1">
                        {progress}% used
                      </p>
                    </div>
                  )}

                  {/* Created Date */}
                  {project.created_at && (
                    <div className="flex items-center gap-2 text-sm text-slate-600 pt-2 border-t border-slate-100">
                      <Calendar className="w-4 h-4" />
                      <span>
                        Created{" "}
                        {new Date(project.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="px-6 py-3 bg-slate-50 border-t border-slate-100">
                  <a
                    href={`/dashboard/projects/${project.id}`}
                    className="text-sm font-medium text-primary-600 hover:text-primary-700 transition-colors"
                  >
                    View details →
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
