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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a dataset ZIP to ingest.");
      return;
    }

    setUploading(true);
    setError(null);
    setSuccessMsg(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/upload-customer-dataset", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Dataset ingestion failed.");
      }

      const data = await response.json();

      if (data.status === "success") {
        setSuccessMsg(`Success! Customer dataset "${file.name}" ingested and analyzed.`);
      } else {
        throw new Error(data.message || "Failed to ingest dataset");
      }

      onUploadSuccess();

      setTimeout(() => {
        setFile(null);
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
        
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-zinc-800">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-teal-50 dark:bg-teal-950 text-teal-600 dark:text-teal-400">
              <FileUp className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold font-sans text-gray-900 dark:text-white tracking-tight">
                Ingest Customer Dataset
              </h3>
              <p className="text-xs text-gray-500 dark:text-zinc-400">
                Securely upload the customer support dataset ZIP for sentiment analysis
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

          <div>
            <label className="block text-xs font-semibold text-gray-600 dark:text-zinc-400 uppercase tracking-wider mb-1.5">
              Select Dataset (.zip)
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
                accept=".zip"
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
                    Supports ZIP file of customer dataset
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="p-3 rounded-lg bg-gray-50 dark:bg-zinc-800/50 flex items-center justify-between text-xs border border-gray-200 dark:border-zinc-800/80">
            <span className="text-gray-500 dark:text-zinc-400 flex items-center gap-1">
              <HelpCircle className="h-3.5 w-3.5 text-gray-400" />
              Submitting as: <strong className="text-gray-700 dark:text-zinc-300 font-semibold">{user.username}</strong>
            </span>
          </div>

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
              {uploading ? "Ingesting Dataset..." : "Start Ingestion"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
