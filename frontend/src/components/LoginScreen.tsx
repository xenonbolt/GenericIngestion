import React, { useState } from "react";
import { User } from "../types";
import { Shield, Key, ArrowRight, Sparkles } from "lucide-react";

interface LoginScreenProps {
  onLoginSuccess: (user: User) => void;
}

export default function LoginScreen({ onLoginSuccess }: LoginScreenProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Please fill in all fields.");
      return;
    }

    setError(null);
    setSuccess(null);
    setLoading(true);

    const url = isLogin ? "/auth/login" : "/auth/signup";

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMsg = data.error || data.detail || "Authentication failed.";
        if (errorMsg.toLowerCase().includes("already exists")) {
          alert("Username already exists! Please choose another or log in.");
        }
        throw new Error(errorMsg);
      }

      if (isLogin) {
        // Logged in
        const loggedInUser: User = {
          username: data.username,
          role: data.role,
          sessionId: `session-${Date.now()}`,
        };
        localStorage.setItem("agentic_user", JSON.stringify(loggedInUser));
        onLoginSuccess(loggedInUser);
      } else {
        // Signed up
        setSuccess("Account created successfully! Switching to Login mode...");
        setIsLogin(true);
        setPassword("");
      }
    } catch (err: any) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-zinc-950 p-4 transition-colors duration-300">
      {/* Decorative ambient background glows */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-teal-500/10 dark:bg-teal-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-violet-500/10 dark:bg-violet-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-2xl shadow-xl overflow-hidden p-8 transition-colors duration-300">
        
        {/* Header Branding */}
        <div className="flex flex-col items-center mb-8 text-center">
          <div className="h-12 w-12 rounded-xl bg-gradient-to-tr from-teal-500 to-violet-600 flex items-center justify-center shadow-lg shadow-teal-500/20 text-white mb-4">
            <Shield className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold font-sans text-gray-900 dark:text-zinc-100 tracking-tight">
            Enterprise Agentic Intelligence
          </h1>
          <p className="text-sm text-gray-500 dark:text-zinc-400 mt-1">
            Access secure multi-agent alignment frameworks
          </p>
        </div>

        {/* Signup / Login toggle header */}
        <div className="flex p-1 bg-gray-100 dark:bg-zinc-800 rounded-lg mb-6">
          <button
            onClick={() => {
              setIsLogin(true);
              setError(null);
              setSuccess(null);
            }}
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
              isLogin
                ? "bg-white dark:bg-zinc-700 text-gray-900 dark:text-white shadow-sm"
                : "text-gray-500 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white"
            }`}
          >
            Login
          </button>
          <button
            onClick={() => {
              setIsLogin(false);
              setError(null);
              setSuccess(null);
            }}
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${
              !isLogin
                ? "bg-white dark:bg-zinc-700 text-gray-900 dark:text-white shadow-sm"
                : "text-gray-500 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white"
            }`}
          >
            Register
          </button>
        </div>

        {/* System Credentials Guidance for Easy Preview */}
        <div className="mb-6 p-3 bg-teal-50/50 dark:bg-teal-950/20 border border-teal-100 dark:border-teal-900/40 rounded-lg">
          <p className="text-xs text-teal-800 dark:text-teal-300 font-medium flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 shrink-0 text-teal-500" />
            Prototype Credentials:
          </p>
          <div className="mt-1 flex flex-col gap-0.5 text-[11px] text-gray-500 dark:text-zinc-400 font-mono">
            <div>• Admin: <span className="text-gray-900 dark:text-white font-medium">admin</span> / <span className="text-gray-900 dark:text-white font-medium">password</span></div>
            <div>• Basic User: <span className="text-gray-900 dark:text-white font-medium">basic</span> / <span className="text-gray-900 dark:text-white font-medium">password</span></div>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 rounded-lg text-xs font-medium">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900/50 text-green-600 dark:text-green-400 rounded-lg text-xs font-medium">
            {success}
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-600 dark:text-zinc-400 uppercase tracking-wider mb-1">
              Username
            </label>
            <div className="relative">
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your corporate ID"
                className="w-full px-3 py-2.5 bg-gray-50 dark:bg-zinc-800/50 border border-gray-300 dark:border-zinc-700 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-teal-500 text-sm transition-all"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-600 dark:text-zinc-400 uppercase tracking-wider mb-1">
              Password
            </label>
            <div className="relative">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="w-full px-3 py-2.5 bg-gray-50 dark:bg-zinc-800/50 border border-gray-300 dark:border-zinc-700 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-teal-500 text-sm transition-all"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-3 bg-gradient-to-r from-teal-500 to-violet-600 hover:from-teal-600 hover:to-violet-700 text-white font-medium rounded-lg text-sm shadow-md shadow-teal-500/10 focus:outline-none focus:ring-2 focus:ring-teal-500 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="inline-block animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
            ) : isLogin ? (
              <>
                Initialize Environment
                <ArrowRight className="h-4 w-4" />
              </>
            ) : (
              <>
                Create Corporate ID
                <Sparkles className="h-4 w-4" />
              </>
            )}
          </button>
        </form>

        <p className="text-center text-xs text-gray-400 dark:text-zinc-500 mt-6">
          Secure AES-256 TLS 1.3 encrypted authentication tunnel.
        </p>
      </div>
    </div>
  );
}
