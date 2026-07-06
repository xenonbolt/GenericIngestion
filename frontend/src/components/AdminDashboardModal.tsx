import { useState, useEffect } from "react";
import { 
  X, Check, Ban, ScrollText, ThumbsUp, Trash2, ShieldCheck, 
  Search, Activity, Database, RefreshCw, Server, AlertCircle, Settings
} from "lucide-react";
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
  const [activeTab, setActiveTab] = useState<"pending" | "users" | "audit" | "glpi">("pending");
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [users, setUsers] = useState<{username: string, role: string}[]>([]);
  
  // GLPI integration states
  const [glpiStatus, setGlpiStatus] = useState<any>(null);
  const [glpiUrl, setGlpiUrl] = useState("http://localhost:8080/glpi");
  const [glpiAppToken, setGlpiAppToken] = useState("hackathon-app-token-2026");
  const [glpiUserToken, setGlpiUserToken] = useState("hackathon-user-token-2026");
  const [useMock, setUseMock] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncSuccessMessage, setSyncSuccessMessage] = useState<string | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      if (activeTab === "glpi") {
        const response = await fetch("/admin/glpi/status");
        if (!response.ok) throw new Error("Failed to fetch GLPI status.");
        const data = await response.json();
        setGlpiStatus(data);
        return;
      }
      
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
    // Clear notifications on tab switch
    setSyncSuccessMessage(null);
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

  const handleGlpiSync = async () => {
    setSyncing(true);
    setError(null);
    setSyncSuccessMessage(null);
    try {
      const response = await fetch("/admin/glpi/sync", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          glpi_url: glpiUrl,
          app_token: glpiAppToken,
          user_token: glpiUserToken,
          use_mock: useMock
        })
      });
      
      if (!response.ok) {
        throw new Error("GLPI Integration sync process failed.");
      }
      
      const data = await response.json();
      setGlpiStatus(data);
      setSyncSuccessMessage(`Sync Complete! Map registered ${data.computers_synced} Computers, ${data.software_synced} Software, and ${data.tickets_synced} tickets into Knowledge Graphs and ChromaDB.`);
      onActionTriggered();
    } catch (err: any) {
      setError(err.message || "Failed to execute GLPI synchronization.");
    } finally {
      setSyncing(false);
    }
  };

  // Filter logs based on search
  const filteredLogs = auditLogs.filter((log) => {
    const q = searchQuery.toLowerCase();
    const uId = log.userId || (log as any).user_id || "";
    const action = log.action || "";
    const details = log.details || "";
    return (
      uId.toLowerCase().includes(q) ||
      action.toLowerCase().includes(q) ||
      details.toLowerCase().includes(q)
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
                Oversee knowledge index approvals, GLPI integrations, and security audit logs
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
              onClick={() => setActiveTab("glpi")}
              className={`py-3.5 text-sm font-semibold border-b-2 transition-all cursor-pointer ${
                activeTab === "glpi"
                  ? "border-teal-500 text-teal-600 dark:text-teal-400"
                  : "border-transparent text-gray-500 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white"
              }`}
            >
              GLPI ITAM Integration
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
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 text-red-600 dark:text-red-400 rounded-lg text-xs font-medium flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}
          
          {syncSuccessMessage && (
            <div className="mb-4 p-3 bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900/50 text-green-600 dark:text-green-400 rounded-lg text-xs font-medium flex items-center gap-2">
              <Check className="h-4 w-4 shrink-0" />
              <span>{syncSuccessMessage}</span>
            </div>
          )}

          {loading && !syncing ? (
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
          ) : activeTab === "glpi" ? (
            /* GLPI ITAM Integration Panel */
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start font-sans">
              
              {/* Left Config Panel */}
              <div className="md:col-span-6 bg-gray-50 dark:bg-zinc-800/30 border border-gray-100 dark:border-zinc-800/80 p-5 rounded-xl space-y-4">
                <div className="flex items-center gap-2 text-sm font-bold text-gray-800 dark:text-zinc-200 mb-1 uppercase tracking-wider">
                  <Settings className="h-4 w-4 text-teal-500" />
                  <span>Sync Configurations</span>
                </div>
                
                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold text-gray-400 dark:text-zinc-500 uppercase">GLPI REST API Endpoint</label>
                  <input
                    type="text"
                    disabled={useMock}
                    value={glpiUrl}
                    onChange={(e) => setGlpiUrl(e.target.value)}
                    className="w-full bg-white dark:bg-zinc-900 border border-gray-300 dark:border-zinc-700 rounded-lg px-3 py-2 text-xs text-gray-900 dark:text-white outline-none focus:ring-1 focus:ring-teal-500 disabled:opacity-50 disabled:bg-gray-100 dark:disabled:bg-zinc-950"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold text-gray-400 dark:text-zinc-500 uppercase">Application App-Token</label>
                  <input
                    type="text"
                    disabled={useMock}
                    value={glpiAppToken}
                    onChange={(e) => setGlpiAppToken(e.target.value)}
                    className="w-full bg-white dark:bg-zinc-900 border border-gray-300 dark:border-zinc-700 rounded-lg px-3 py-2 text-xs text-gray-900 dark:text-white outline-none focus:ring-1 focus:ring-teal-500 disabled:opacity-50 disabled:bg-gray-100 dark:disabled:bg-zinc-950 font-mono"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-[11px] font-bold text-gray-400 dark:text-zinc-500 uppercase">User Security Token</label>
                  <input
                    type="password"
                    disabled={useMock}
                    value={glpiUserToken}
                    onChange={(e) => setGlpiUserToken(e.target.value)}
                    className="w-full bg-white dark:bg-zinc-900 border border-gray-300 dark:border-zinc-700 rounded-lg px-3 py-2 text-xs text-gray-900 dark:text-white outline-none focus:ring-1 focus:ring-teal-500 disabled:opacity-50 disabled:bg-gray-100 dark:disabled:bg-zinc-950 font-mono"
                  />
                </div>

                {/* Sandbox Toggle */}
                <div className="py-2 flex items-center justify-between border-t border-gray-200 dark:border-zinc-800/80 mt-2">
                  <div>
                    <span className="text-xs font-semibold text-gray-800 dark:text-zinc-200">Local Sandbox Simulator</span>
                    <p className="text-[10px] text-gray-400 dark:text-zinc-500">Injects custom ITAM schema for live evaluation</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={useMock}
                    onChange={(e) => setUseMock(e.target.checked)}
                    className="h-4.5 w-4.5 text-teal-600 rounded bg-gray-100 border-gray-300 focus:ring-teal-500 accent-teal-500 cursor-pointer"
                  />
                </div>

                <button
                  onClick={handleGlpiSync}
                  disabled={syncing}
                  className="w-full py-2.5 bg-teal-500 hover:bg-teal-600 disabled:bg-teal-500/50 text-white text-xs font-bold rounded-lg shadow-md shadow-teal-500/10 flex items-center justify-center gap-2 cursor-pointer transition-all uppercase tracking-wider"
                >
                  <RefreshCw className={`h-4 w-4 ${syncing ? "animate-spin" : ""}`} />
                  {syncing ? "Synchronizing Asset Map..." : "Synchronize GLPI Map"}
                </button>
              </div>

              {/* Right Telemetry Panel */}
              <div className="md:col-span-6 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 p-5 rounded-xl space-y-4 shadow-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm font-bold text-gray-800 dark:text-zinc-200 uppercase tracking-wider">
                    <Database className="h-4 w-4 text-violet-500" />
                    <span>Sync Status & Telemetry</span>
                  </div>
                  {glpiStatus && glpiStatus.status === "success" ? (
                    <span className="flex items-center gap-1 text-[10px] font-bold text-green-500 bg-green-50 dark:bg-green-950/40 px-2 py-0.5 rounded border border-green-200/50 dark:border-green-900/30">
                      <Activity className="h-3 w-3 animate-pulse" /> SYNCHRONIZED
                    </span>
                  ) : (
                    <span className="text-[10px] font-bold text-gray-400 bg-gray-50 dark:bg-zinc-800 px-2 py-0.5 rounded">
                      NOT SYNCED
                    </span>
                  )}
                </div>

                {glpiStatus && glpiStatus.status === "success" ? (
                  <div className="space-y-4">
                    
                    {/* Metrics Grid */}
                    <div className="grid grid-cols-2 gap-3.5">
                      
                      <div className="p-3 bg-gray-50 dark:bg-zinc-800/30 border border-gray-100 dark:border-zinc-800/60 rounded-lg">
                        <span className="text-[10px] font-bold text-gray-400 dark:text-zinc-500 uppercase tracking-wider">Computers Synced</span>
                        <div className="text-xl font-black text-gray-900 dark:text-white mt-0.5">{glpiStatus.computers_synced}</div>
                      </div>

                      <div className="p-3 bg-gray-50 dark:bg-zinc-800/30 border border-gray-100 dark:border-zinc-800/60 rounded-lg">
                        <span className="text-[10px] font-bold text-gray-400 dark:text-zinc-500 uppercase tracking-wider">Software Registered</span>
                        <div className="text-xl font-black text-gray-900 dark:text-white mt-0.5">{glpiStatus.software_synced}</div>
                      </div>

                      <div className="p-3 bg-gray-50 dark:bg-zinc-800/30 border border-gray-100 dark:border-zinc-800/60 rounded-lg">
                        <span className="text-[10px] font-bold text-gray-400 dark:text-zinc-500 uppercase tracking-wider">Service Tickets Map</span>
                        <div className="text-xl font-black text-gray-900 dark:text-white mt-0.5">{glpiStatus.tickets_synced}</div>
                      </div>

                      <div className="p-3 bg-gray-50 dark:bg-zinc-800/30 border border-gray-100 dark:border-zinc-800/60 rounded-lg">
                        <span className="text-[10px] font-bold text-gray-400 dark:text-zinc-500 uppercase tracking-wider">Graph Relations</span>
                        <div className="text-xl font-black text-teal-500 mt-0.5">{glpiStatus.relations_synced}</div>
                      </div>

                    </div>

                    <div className="border-t border-gray-100 dark:border-zinc-800/80 pt-3 space-y-2 text-xs">
                      <div className="flex justify-between">
                        <span className="text-gray-400 dark:text-zinc-500">Sync Mode:</span>
                        <strong className="text-gray-700 dark:text-zinc-300 font-semibold uppercase font-mono tracking-wider">
                          {glpiStatus.use_mock ? "Mock Sandbox" : "Remote GLPI Instance"}
                        </strong>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400 dark:text-zinc-500">Last Sync Time:</span>
                        <strong className="text-gray-700 dark:text-zinc-300 font-mono">
                          {new Date(glpiStatus.last_synced_at).toLocaleString()}
                        </strong>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 space-y-2">
                    <Server className="h-10 w-10 text-gray-300 dark:text-zinc-700 mx-auto" />
                    <h5 className="text-xs font-bold text-gray-500 dark:text-zinc-400 uppercase tracking-wider">No Sync Logs Found</h5>
                    <p className="text-[11px] text-gray-400 dark:text-zinc-500 max-w-[240px] mx-auto leading-relaxed">
                      Configure your settings on the left and trigger the sync map to load GLPI nodes into the database.
                    </p>
                  </div>
                )}
              </div>

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
                  {filteredLogs.map((log) => {
                    const uId = log.userId || (log as any).user_id || "system";
                    return (
                      <div key={log.id} className="p-3 bg-zinc-50/30 dark:bg-zinc-900/30 hover:bg-zinc-50 dark:hover:bg-zinc-800/20 transition-all flex flex-col md:flex-row md:items-center gap-3">
                        <div className="w-36 text-gray-400 dark:text-zinc-500 shrink-0">
                          {new Date(log.timestamp).toLocaleString()}
                        </div>
                        <div className="w-24 shrink-0 font-bold">
                          <span className={`px-1.5 py-0.5 rounded text-[9px] uppercase tracking-wide ${
                            uId === "admin" || uId === "system"
                              ? "bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-400"
                              : "bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400"
                          }`}>
                            {uId}
                          </span>
                        </div>
                        <div className="w-32 shrink-0 font-bold text-gray-800 dark:text-zinc-200">
                          {log.action}
                        </div>
                        <div className="flex-1 text-gray-600 dark:text-zinc-400">
                          {log.details}
                        </div>
                      </div>
                    );
                  })}
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
