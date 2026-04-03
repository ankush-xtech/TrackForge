"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";

interface FormData {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  organization_name: string;
}

interface FormErrors {
  [key: string]: string;
}

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading, error, clearError, isAuthenticated } =
    useAuthStore();
  const [form, setForm] = useState<FormData>({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    organization_name: "",
  });
  const [formErrors, setFormErrors] = useState<FormErrors>({});

  // If already authenticated, redirect to dashboard
  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, router]);

  const update = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    // Clear field error when user starts typing
    if (formErrors[field]) {
      setFormErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const validate = (): boolean => {
    const errors: FormErrors = {};

    if (!form.first_name.trim()) {
      errors.first_name = "First name is required";
    }
    if (!form.last_name.trim()) {
      errors.last_name = "Last name is required";
    }
    if (!form.organization_name.trim()) {
      errors.organization_name = "Organization name is required";
    }
    if (!form.email.trim()) {
      errors.email = "Email is required";
    } else if (!form.email.includes("@")) {
      errors.email = "Please enter a valid email";
    }
    if (!form.password) {
      errors.password = "Password is required";
    } else if (form.password.length < 8) {
      errors.password = "Password must be at least 8 characters";
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();

    if (!validate()) {
      return;
    }

    try {
      await register(form);
      router.push("/dashboard");
    } catch (err) {
      // Error is already in store
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-indigo-50 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-primary-700 mb-2">WebWork</h1>
          <p className="text-slate-600 text-lg">Create your workspace</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white p-8 rounded-xl shadow-lg border border-slate-100"
        >
          {error && (
            <div className="mb-5 p-4 text-sm text-red-700 bg-red-50 rounded-lg border border-red-200 flex items-start gap-2">
              <span className="text-lg leading-none mt-0.5">!</span>
              <div>
                <p className="font-medium">Registration Error</p>
                <p>{error}</p>
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="block text-sm font-semibold text-slate-900 mb-2">
                First Name
              </label>
              <input
                type="text"
                value={form.first_name}
                onChange={(e) => update("first_name", e.target.value)}
                disabled={isLoading}
                className={`w-full px-4 py-2.5 border rounded-lg outline-none transition disabled:bg-slate-100 disabled:cursor-not-allowed ${
                  formErrors.first_name
                    ? "border-red-300 focus:ring-red-500 focus:border-red-500"
                    : "border-slate-300 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                }`}
                placeholder="John"
                required
              />
              {formErrors.first_name && (
                <p className="text-xs text-red-600 mt-1">{formErrors.first_name}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-900 mb-2">
                Last Name
              </label>
              <input
                type="text"
                value={form.last_name}
                onChange={(e) => update("last_name", e.target.value)}
                disabled={isLoading}
                className={`w-full px-4 py-2.5 border rounded-lg outline-none transition disabled:bg-slate-100 disabled:cursor-not-allowed ${
                  formErrors.last_name
                    ? "border-red-300 focus:ring-red-500 focus:border-red-500"
                    : "border-slate-300 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                }`}
                placeholder="Doe"
                required
              />
              {formErrors.last_name && (
                <p className="text-xs text-red-600 mt-1">{formErrors.last_name}</p>
              )}
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-semibold text-slate-900 mb-2">
              Organization Name
            </label>
            <input
              type="text"
              value={form.organization_name}
              onChange={(e) => update("organization_name", e.target.value)}
              disabled={isLoading}
              className={`w-full px-4 py-2.5 border rounded-lg outline-none transition disabled:bg-slate-100 disabled:cursor-not-allowed ${
                formErrors.organization_name
                  ? "border-red-300 focus:ring-red-500 focus:border-red-500"
                  : "border-slate-300 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              }`}
              placeholder="Your Company"
              required
            />
            {formErrors.organization_name && (
              <p className="text-xs text-red-600 mt-1">
                {formErrors.organization_name}
              </p>
            )}
          </div>

          <div className="mb-4">
            <label className="block text-sm font-semibold text-slate-900 mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => update("email", e.target.value)}
              disabled={isLoading}
              className={`w-full px-4 py-2.5 border rounded-lg outline-none transition disabled:bg-slate-100 disabled:cursor-not-allowed ${
                formErrors.email
                  ? "border-red-300 focus:ring-red-500 focus:border-red-500"
                  : "border-slate-300 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              }`}
              placeholder="you@company.com"
              required
            />
            {formErrors.email && (
              <p className="text-xs text-red-600 mt-1">{formErrors.email}</p>
            )}
          </div>

          <div className="mb-6">
            <label className="block text-sm font-semibold text-slate-900 mb-2">
              Password
            </label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => update("password", e.target.value)}
              disabled={isLoading}
              className={`w-full px-4 py-2.5 border rounded-lg outline-none transition disabled:bg-slate-100 disabled:cursor-not-allowed ${
                formErrors.password
                  ? "border-red-300 focus:ring-red-500 focus:border-red-500"
                  : "border-slate-300 focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              }`}
              placeholder="Minimum 8 characters"
              minLength={8}
              required
            />
            {formErrors.password && (
              <p className="text-xs text-red-600 mt-1">{formErrors.password}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 disabled:bg-primary-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                Creating workspace...
              </>
            ) : (
              "Create Workspace"
            )}
          </button>

          <div className="mt-6 pt-6 border-t border-slate-200">
            <p className="text-center text-sm text-slate-600">
              Already have an account?{" "}
              <Link
                href="/auth/login"
                className="text-primary-600 font-semibold hover:text-primary-700 transition-colors"
              >
                Sign in
              </Link>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
