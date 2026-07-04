import React, { useState, useRef } from "react";
import { X, FileUp, Sparkles, AlertCircle, HelpCircle } from "lucide-react";
import { User } from "../types";

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: User;
  onUploadSuccess: () => void;
}

export default function UploadModal({ isOpen, onClose, user, onUploadSuccess }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [category, setCategory] = useState("");
  const [tags, setTags] = useState("");
  const [summary, setSummary] = useState("");
  
  const [analyzing, setAnalyzing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  // Drag and Drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
    }
  };

  // Magic AI Auto-Fill metadata
  const handleMagicAutoFill = async () => {
    if (!file) {
      setError("Please select or drop a file first before using magic auto-fill.");
      return;
    }
    setAnalyzing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/analyze-metadata", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to analyze file metadata.");
      }

      const data = await response.json();
      setCategory(data.category);
      setTags(data.tags);
      setSummary(data.summary);
    } catch (err: any) {
      setError("AI analysis failed. Please fill in metadata fields manually.");
    } finally {
      setAnalyzing(false);
    }
  };

  // Handle Form Submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file to ingest.");
      return;
    }
    if (!category.trim() || !tags.trim() || !summary.trim()) {
      setError("Please fill in or auto-fill all metadata fields.");
      return;
    }

    setUploading(true);
    setError(null);
    setSuccessMsg(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("category", category);
    formData.append("tags", tags);
    formData.append("summary", summary);
    formData.append("user_id", user.username);
    formData.append("role", user.role);

    try {
      const response = await fetch("/upload", {
        method: "POST",
        body: formData, // Multi-part body
      });

      if (!response.ok) {
        throw new Error("Inflow ingestion pipeline failed.");
      }

      const data = await response.json();

      if (user.role === "admin") {
        setSuccessMsg(`Success! Document "${file.name}" was approved and indexed instantly!`);
      } else {
        setSuccessMsg("Inflow submission received. Upload submitted for Admin approval.");
      }

      // Trigger callback to refresh admin lists if applicable
      onUploadSuccess();

      // Reset fields after brief delay
      setTimeout(() => {
        setFile(null);
        setCategory("");
        setTags("");
        setSummary("");
        setSuccessMsg(null);
        onClose();
      }, 2500);

    } catch (err: any) {
      setError(err.message || "Something went wrong during ingestion.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-zinc-950/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="relative w-full max-w-xl bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col transition-colors duration-300">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-zinc-800">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-600 dark:text-teal-400">
              <FileUp className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold font-sans text-gray-900 dark:text-white tracking-tight">
                Ingest Enterprise Knowledge Base
              </h3>
              <p className="text-xs text-gray-500 dark:text-zinc-400">
                Securely stream documentation assets into vector indices
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 dark:text-zinc-500 hover:text-gray-600 dark:hover:text-zinc-300 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-all cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6 overflow-y-auto space-y-4 flex-1">
          {error && (
            <div className="p-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 rounded-lg text-xs font-medium flex items-start gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 text-red-500 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-3 bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900/50 text-green-700 dark:text-green-400 rounded-lg text-xs font-medium flex items-start gap-2">
              <Sparkles className="h-4 w-4 shrink-0 text-green-500 mt-0.5 animate-pulse" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* File Picker drag and drop target */}
          <div>
            <label className="block text-xs font-semibold text-gray-600 dark:text-zinc-400 uppercase tracking-wider mb-1.5">
              Select Document
            </label>
            <div
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer ${
                file
                  ? "border-teal-500 bg-teal-50/20 dark:bg-teal-950/10"
                  : "border-gray-300 dark:border-zinc-700 hover:border-teal-500 bg-gray-50 dark:bg-zinc-800/40"
              }`}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                className="hidden"
                accept=".pdf,.doc,.docx,.xlsx,.xls,.csv,.txt,.json"
              />
              <FileUp className={`mx-auto h-8 w-8 mb-2 ${file ? "text-teal-500" : "text-gray-400"}`} />
              {file ? (
                <div>
                  <span className="text-sm font-semibold text-teal-600 dark:text-teal-400 break-all">
                    {file.name}
                  </span>
                  <p className="text-xs text-gray-400 mt-1">
                    {(file.size / 1024).toFixed(1)} KB • Click or drag to replace
                  </p>
                </div>
              ) : (
                <div>
                  <span className="text-sm text-gray-600 dark:text-zinc-300 font-medium">
                    Drag and drop file here, or <span className="text-teal-500 font-semibold underline">browse</span>
                  </span>
                  <p className="text-xs text-gray-400 mt-1">
                    Supports PDF, DOCX, XLSX, CSV, JSON, TXT (Max 25MB)
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Meta header with AI assistance */}
          <div className="flex items-center justify-between pt-2">
            <label className="block text-xs font-semibold text-gray-600 dark:text-zinc-400 uppercase tracking-wider">
              Knowledge Base Metadata
            </label>
            <button
              type="button"
              onClick={handleMagicAutoFill}
              disabled={analyzing || !file}
              className="text-xs py-1.5 px-3 bg-gradient-to-r from-teal-500 to-violet-600 hover:from-teal-600 hover:to-violet-700 text-white font-medium rounded-lg shadow-sm transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Sparkles className={`h-3 w-3 ${analyzing ? "animate-spin" : ""}`} />
              {analyzing ? "AI Analyzing..." : "Magic Auto-Fill"}
            </button>
          </div>

          {/* Fields */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 dark:text-zinc-400 mb-1">
                Category
              </label>
              <input
                type="text"
                placeholder="e.g. Finance"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-zinc-800 border border-gray-300 dark:border-zinc-700 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-teal-500 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 dark:text-zinc-400 mb-1">
                Tags (comma separated)
              </label>
              <input
                type="text"
                placeholder="e.g. q3, report, ledger"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="w-full px-3 py-2 bg-gray-50 dark:bg-zinc-800 border border-gray-300 dark:border-zinc-700 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-teal-500 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-zinc-400 mb-1">
              Executive Summary
            </label>
            <textarea
              rows={3}
              placeholder="Provide a comprehensive summary of this corporate data asset..."
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              className="w-full px-3 py-2 bg-gray-50 dark:bg-zinc-800 border border-gray-300 dark:border-zinc-700 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-teal-500 text-sm resize-none"
            />
          </div>

          {/* Role submission badge */}
          <div className="p-3 rounded-lg bg-gray-50 dark:bg-zinc-800/50 flex items-center justify-between text-xs border border-gray-200 dark:border-zinc-800/80">
            <span className="text-gray-500 dark:text-zinc-400 flex items-center gap-1">
              <HelpCircle className="h-3.5 w-3.5 text-gray-400" />
              Submitting as: <strong className="text-gray-700 dark:text-zinc-300 font-semibold">{user.username}</strong>
            </span>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
              user.role === "admin"
                ? "bg-purple-100 dark:bg-purple-950/50 text-purple-700 dark:text-purple-400"
                : "bg-blue-100 dark:bg-blue-950/50 text-blue-700 dark:text-blue-400"
            }`}>
              {user.role} Privilege
            </span>
          </div>

          {/* Footer Buttons */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-100 dark:border-zinc-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 dark:bg-zinc-800 hover:bg-gray-200 dark:hover:bg-zinc-700 text-gray-700 dark:text-zinc-300 font-medium rounded-lg text-sm transition-all cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={uploading}
              className="px-5 py-2 bg-teal-500 hover:bg-teal-600 text-white font-medium rounded-lg text-sm shadow-sm transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {uploading && (
                <span className="inline-block animate-spin h-3.5 w-3.5 border-2 border-white border-t-transparent rounded-full" />
              )}
              {uploading ? "Ingesting..." : "Initialize Ingestion"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
