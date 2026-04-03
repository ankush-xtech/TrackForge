"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading, error, clearError, isAuthenticated } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState("");

  // If already authenticated, redirect to dashboard
  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    clearError();

    if (!email || !password) {
      setFormError("Please fill in all fields");
      return;
    }

    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      // Error is already in store
    }
  };

  const displayError = error || formError;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-indigo-50 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-primary-700 mb-2">WebWork</h1>
          <p className="text-slate-600 text-lg">Sign in to your account</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white p-8 rounded-xl shadow-lg border border-slate-100"
        >
          {displayError && (
            <div className="mb-5 p-4 text-sm text-red-700 bg-red-50 rounded-lg border border-red-200 flex items-start gap-2">
              <span className="text-lg leading-none mt-0.5">!</span>
              <div>
                <p className="font-medium">Error</p>
                <p>{displayError}</p>
              </div>
            </div>
          )}

          <div className="mb-5">
            <label className="block text-sm font-semibold text-slate-900 mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
              className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition disabled:bg-slate-100 disabled:cursor-not-allowed"
              placeholder="you@company.com"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-semibold text-slate-900 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition disabled:bg-slate-100 disabled:cursor-not-allowed"
              placeholder="Enter your password"
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 disabled:bg-primary-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                Signing in...
              </>
            ) : (
              "Sign In"
            )}
          </button>

          <div className="mt-6 pt-6 border-t border-slate-200">
            <p className="text-center text-sm text-slate-600">
              Don't have an account?{" "}
              <Link
                href="/auth/register"
                className="text-primary-600 font-semibold hover:text-primary-700 transition-colors"
              >
                Create one
              </Link>
            </p>
          </div>
        </form>

        <p className="text-center text-xs text-slate-500 mt-6">
          Demo account: admin@trackforge.com / password123
        </p>
      </div>
    </div>
  );
}
