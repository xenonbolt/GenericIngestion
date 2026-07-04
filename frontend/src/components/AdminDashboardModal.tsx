import { useState, useEffect } from "react";
import { X, Check, Ban, ScrollText, ThumbsUp, Trash2, ShieldCheck, Search, Activity } from "lucide-react";
import { ApprovalItem, AuditLog } from "../types";

interface AdminDashboardModalProps {
  isOpen: boolean;
  onClose: () => void;
  onActionTriggered: () => void;
}

export default function AdminDashboardModal({
  isOpen,
  onClose,
  onActionTriggered,
}: AdminDashboardModalProps) {
  const [activeTab, setActiveTab] = useState<"pending" | "users" | "audit">("pending");
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [users, setUsers] = useState<{username: string, role: string}[]>([]);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const endpoint = activeTab === "pending" ? "/admin/approvals" : activeTab === "users" ? "/admin/users" : "/admin/audit-logs";
      const response = await fetch(endpoint);
      if (!response.ok) {
        throw new Error(`Failed to fetch data for ${activeTab}`);
      }
      const data = await response.json();
      if (activeTab === "pending") {
        setApprovals(data);
      } else if (activeTab === "users") {
        setUsers(data);
      } else {
        setAuditLogs(data);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchData();
    }
  }, [isOpen, activeTab]);

  if (!isOpen) return null;

  const handleApprove = async (id: string, name: string) => {
    try {
      const res = await fetch(`/admin/approvals/${id}/approve`, { method: "POST" });
      if (!res.ok) throw new Error("Approval action failed.");
      setApprovals((prev) => prev.filter((item) => item.id !== id));
      onActionTriggered();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleReject = async (id: string, name: string) => {
    try {
      const res = await fetch(`/admin/approvals/${id}/reject`, { method: "POST" });
      if (!res.ok) throw new Error("Rejection action failed.");
      setApprovals((prev) => prev.filter((item) => item.id !== id));
      onActionTriggered();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleRoleChange = async (username: string, newRole: string) => {
    try {
      const res = await fetch(`/admin/users/${username}/role`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: newRole })
      });
      if (!res.ok) throw new Error("Failed to update role");
      fetchData();
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Filter logs based on search
  const filteredLogs = auditLogs.filter((log) => {
    const q = searchQuery.toLowerCase();
    return (
      log.userId.toLowerCase().includes(q) ||
      log.action.toLowerCase().includes(q) ||
      log.details.toLowerCase().includes(q)
    );
  });

  return (
    <div className="fixed inset-0 bg-zinc-950/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="relative w-full max-w-4xl bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-2xl shadow-2xl overflow-hidden max-h-[85vh] flex flex-col transition-colors duration-300">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-900/50">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-violet-50 dark:bg-violet-950/40 text-violet-600 dark:text-violet-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold font-sans text-gray-900 dark:text-white tracking-tight">
                Enterprise Admin Operations Control
              </h3>
              <p className="text-xs text-gray-500 dark:text-zinc-400">
                Oversee knowledge index approvals and system wide security audits
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

        {/* Tab Selection */}
        <div className="flex items-center justify-between px-6 border-b border-gray-100 dark:border-zinc-800 bg-white dark:bg-zinc-900">
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab("pending")}
              className={`py-3.5 text-sm font-semibold border-b-2 transition-all cursor-pointer ${
                activeTab === "pending"
                  ? "border-teal-500 text-teal-600 dark:text-teal-400"
                  : "border-transparent text-gray-500 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white"
              }`}
            >
              Pending Approvals ({approvals.length})
            </button>
            <button
              onClick={() => setActiveTab("users")}
              className={`py-3.5 text-sm font-semibold border-b-2 transition-all cursor-pointer ${
                activeTab === "users"
                  ? "border-teal-500 text-teal-600 dark:text-teal-400"
                  : "border-transparent text-gray-500 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white"
              }`}
            >
              User Management
            </button>
            <button
              onClick={() => setActiveTab("audit")}
              className={`py-3.5 text-sm font-semibold border-b-2 transition-all cursor-pointer ${
                activeTab === "audit"
                  ? "border-teal-500 text-teal-600 dark:text-teal-400"
                  : "border-transparent text-gray-500 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white"
              }`}
            >
              System Audit Logs
            </button>
          </div>

          {activeTab === "audit" && (
            <div className="relative w-64 max-w-xs py-2">
              <input
                type="text"
                placeholder="Search audit trail..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1 bg-gray-50 dark:bg-zinc-800 border border-gray-300 dark:border-zinc-700 rounded-lg text-xs text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
              />
              <Search className="absolute left-2.5 top-3.5 h-3.5 w-3.5 text-gray-400 dark:text-zinc-500" />
            </div>
          )}
        </div>

        {/* Body content */}
        <div className="p-6 overflow-y-auto flex-1 bg-white dark:bg-zinc-900 transition-colors duration-300">
          {error && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 rounded-lg text-xs font-medium">
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3">
              <span className="inline-block animate-spin h-8 w-8 border-3 border-teal-500 border-t-transparent rounded-full" />
              <p className="text-xs text-gray-400 dark:text-zinc-500 font-mono">
                Querying corporate ledger and files...
              </p>
            </div>
          ) : activeTab === "pending" ? (
            /* Pending Approvals View */
            approvals.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="p-4 rounded-full bg-teal-50 dark:bg-teal-950/40 text-teal-500 mb-4 animate-pulse">
                  <ThumbsUp className="h-8 w-8" />
                </div>
                <h4 className="text-sm font-semibold text-gray-800 dark:text-zinc-200">
                  All Clear! No Pending Approvals
                </h4>
                <p className="text-xs text-gray-400 dark:text-zinc-500 mt-1 max-w-sm">
                  All enterprise knowledge ingestion requests have been successfully indexed.
                </p>
              </div>
            ) : (
              <div className="border border-gray-100 dark:border-zinc-800/80 rounded-xl overflow-hidden shadow-sm">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-gray-50 dark:bg-zinc-800 text-gray-600 dark:text-zinc-400 border-b border-gray-100 dark:border-zinc-800/80 font-semibold tracking-wider uppercase text-[10px]">
                      <th className="px-4 py-3">Filename / Submitter</th>
                      <th className="px-4 py-3">Category</th>
                      <th className="px-4 py-3">Summary Abstract</th>
                      <th className="px-4 py-3">Timestamp</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-zinc-800/80 font-sans text-gray-700 dark:text-zinc-300">
                    {approvals.map((doc) => (
                      <tr key={doc.id} className="hover:bg-gray-50/50 dark:hover:bg-zinc-800/30 transition-colors">
                        <td className="px-4 py-4.5">
                          <div className="font-semibold text-gray-900 dark:text-zinc-100 break-all max-w-[150px]">
                            {doc.filename}
                          </div>
                          <div className="text-[10px] text-gray-400 mt-0.5">
                            Submitter: <strong className="font-medium">{doc.submitter}</strong>
                          </div>
                        </td>
                        <td className="px-4 py-4.5">
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-teal-50 dark:bg-teal-950/50 text-teal-700 dark:text-teal-400 border border-teal-100 dark:border-teal-900/30">
                            {doc.category}
                          </span>
                        </td>
                        <td className="px-4 py-4.5 text-gray-500 dark:text-zinc-400 max-w-[260px] line-clamp-3">
                          {doc.summary}
                        </td>
                        <td className="px-4 py-4.5 text-gray-400 font-mono text-[11px]">
                          {new Date(doc.timestamp).toLocaleString()}
                        </td>
                        <td className="px-4 py-4.5 text-right whitespace-nowrap">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => handleApprove(doc.id, doc.filename)}
                              className="p-1.5 rounded-lg bg-green-50 hover:bg-green-100 text-green-600 dark:bg-green-950/40 dark:hover:bg-green-900/50 dark:text-green-400 border border-green-200 dark:border-green-900/40 cursor-pointer transition-all"
                              title="Approve & Index"
                            >
                              <Check className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleReject(doc.id, doc.filename)}
                              className="p-1.5 rounded-lg bg-red-50 hover:bg-red-100 text-red-600 dark:bg-red-950/40 dark:hover:bg-red-900/50 dark:text-red-400 border border-red-200 dark:border-red-900/40 cursor-pointer transition-all"
                              title="Reject Upload"
                            >
                              <Ban className="h-4 w-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          ) : activeTab === "users" ? (
            /* Users View */
            <div className="border border-gray-100 dark:border-zinc-800/80 rounded-xl overflow-hidden shadow-sm p-4">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-gray-50 dark:bg-zinc-800 text-gray-600 dark:text-zinc-400 border-b border-gray-100 dark:border-zinc-800/80 font-semibold tracking-wider uppercase text-[10px]">
                    <th className="px-4 py-3">Username</th>
                    <th className="px-4 py-3">Role</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-zinc-800/80 font-sans text-gray-700 dark:text-zinc-300">
                  {users.map((u) => (
                    <tr key={u.username} className="hover:bg-gray-50/50 dark:hover:bg-zinc-800/30 transition-colors">
                      <td className="px-4 py-4.5 font-semibold text-gray-900 dark:text-zinc-100">{u.username}</td>
                      <td className="px-4 py-4.5">
                        <select 
                          value={u.role} 
                          onChange={(e) => handleRoleChange(u.username, e.target.value)}
                          className="bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 text-gray-800 dark:text-zinc-200 rounded px-2 py-1 outline-none focus:ring-1 focus:ring-teal-500"
                        >
                          <option value="basic">Basic</option>
                          <option value="admin">Admin</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            /* System Audit Logs View */
            filteredLogs.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <ScrollText className="h-8 w-8 text-gray-400 mb-2" />
                <h4 className="text-sm font-semibold text-gray-800 dark:text-zinc-200">
                  No Logs Match Filter
                </h4>
                <p className="text-xs text-gray-400 dark:text-zinc-500 mt-1">
                  Try clearing or adjusting your search phrase.
                </p>
              </div>
            ) : (
              <div className="border border-gray-100 dark:border-zinc-800/80 rounded-xl overflow-hidden shadow-sm">
                <div className="bg-gray-50 dark:bg-zinc-800/80 px-4 py-2 text-[10px] font-bold uppercase tracking-wider text-gray-500 dark:text-zinc-400 border-b border-gray-100 dark:border-zinc-800/80 flex items-center justify-between">
                  <span>Audit Event Log Stream</span>
                  <span className="flex items-center gap-1 font-mono text-[9px] text-teal-600 dark:text-teal-400">
                    <Activity className="h-3 w-3 animate-pulse" />
                    LIVE TELEMETRY ACTIVE
                  </span>
                </div>
                <div className="divide-y divide-gray-100 dark:divide-zinc-800/80 font-mono text-[11px] max-h-[480px] overflow-y-auto">
                  {filteredLogs.map((log) => (
                    <div key={log.id} className="p-3 bg-zinc-50/30 dark:bg-zinc-900/30 hover:bg-zinc-50 dark:hover:bg-zinc-800/20 transition-all flex flex-col md:flex-row md:items-center gap-3">
                      <div className="w-36 text-gray-400 dark:text-zinc-500 shrink-0">
                        {new Date(log.timestamp).toLocaleString()}
                      </div>
                      <div className="w-24 shrink-0 font-bold">
                        <span className={`px-1.5 py-0.5 rounded text-[9px] uppercase tracking-wide ${
                          log.userId === "admin" || log.userId === "system"
                            ? "bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-400"
                            : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400"
                        }`}>
                          {log.userId}
                        </span>
                      </div>
                      <div className="w-32 shrink-0 font-bold text-gray-800 dark:text-zinc-200">
                        {log.action}
                      </div>
                      <div className="flex-1 text-gray-600 dark:text-zinc-400">
                        {log.details}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 dark:bg-zinc-900 border-t border-gray-100 dark:border-zinc-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-zinc-800 hover:bg-zinc-700 text-white font-medium rounded-lg text-sm transition-all cursor-pointer"
          >
            Close Operational Panel
          </button>
        </div>

      </div>
    </div>
  );
}
