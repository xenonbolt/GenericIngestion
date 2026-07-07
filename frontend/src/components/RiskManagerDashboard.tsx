import React, { useState, useEffect } from "react";
import { AlertTriangle, CheckCircle, ChevronDown, ChevronUp, RefreshCw } from "lucide-react";

interface NextBestAction {
  action: string;
  actionable_work_items: string;
}

interface EscalationTicket {
  ticket_number: string;
  customer_id: string;
  customer_name: string;
  summary: string;
  root_cause_analysis: string;
  next_best_actions: NextBestAction[];
  customer_feedback: string;
  status: "Open" | "Resolved";
  created_date: string;
  resolved_date?: string;
}

export default function RiskManagerDashboard() {
  const [tickets, setTickets] = useState<EscalationTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedTicket, setExpandedTicket] = useState<string | null>(null);
  const [workItems, setWorkItems] = useState<Record<string, Record<number, string>>>({});
  const [feedbacks, setFeedbacks] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState<string | null>(null);
  const [resolveMsg, setResolveMsg] = useState<Record<string, string>>({});

  const fetchTickets = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/escalations");
      const data = await res.json();
      if (data.status === "success") {
        setTickets(data.tickets || []);
      }
    } catch (e) {
      console.error("Failed to load tickets", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTickets(); }, []);

  const handleWorkItemChange = (ticketNum: string, idx: number, value: string) => {
    setWorkItems(prev => ({
      ...prev,
      [ticketNum]: { ...(prev[ticketNum] || {}), [idx]: value }
    }));
  };

  const handleResolve = async (ticket: EscalationTicket) => {
    const ticketWorkItems = workItems[ticket.ticket_number] || {};
    const updatedActions = ticket.next_best_actions.map((a, idx) => ({
      action: a.action,
      actionable_work_items: ticketWorkItems[idx] || a.actionable_work_items || ""
    }));
    const feedback = feedbacks[ticket.ticket_number] || "";

    // Validate mandatory fields
    const missingAction = updatedActions.find(a => !a.actionable_work_items.trim());
    if (missingAction) {
      setResolveMsg(p => ({ ...p, [ticket.ticket_number]: `Please add work items for: "${missingAction.action}"` }));
      return;
    }
    if (!feedback.trim()) {
      setResolveMsg(p => ({ ...p, [ticket.ticket_number]: "Customer feedback is required." }));
      return;
    }

    setSubmitting(ticket.ticket_number);
    setResolveMsg(p => ({ ...p, [ticket.ticket_number]: "" }));
    try {
      const res = await fetch(`/api/escalations/${ticket.ticket_number}/resolve`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ next_best_actions: updatedActions, customer_feedback: feedback })
      });
      const data = await res.json();
      if (res.ok) {
        setResolveMsg(p => ({ ...p, [ticket.ticket_number]: "✓ Ticket resolved! Customer risk profile is being updated..." }));
        fetchTickets();
      } else {
        setResolveMsg(p => ({ ...p, [ticket.ticket_number]: data.detail || "Failed to resolve." }));
      }
    } catch (e) {
      setResolveMsg(p => ({ ...p, [ticket.ticket_number]: "Connection error." }));
    } finally {
      setSubmitting(null);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-2xl shadow-sm overflow-hidden h-full">
      {/* Header */}
      <div className="p-6 border-b border-gray-100 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-900/50 flex justify-between items-center shrink-0">
        <div>
          <h2 className="text-xl font-black text-gray-900 dark:text-white tracking-tight flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-red-500" />
            Risk Manager — Escalation Queue
          </h2>
          <p className="text-sm text-gray-500 dark:text-zinc-400 mt-1">
            Review, work on, and resolve open escalation tickets.
          </p>
        </div>
        <button
          onClick={fetchTickets}
          className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold text-gray-600 dark:text-zinc-300 bg-white dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-lg hover:bg-gray-50 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      </div>

      <div className="p-6 overflow-y-auto space-y-4 flex-1">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <RefreshCw className="h-8 w-8 text-teal-500 animate-spin" />
            <p className="text-xs text-gray-400 dark:text-zinc-500">Loading escalation tickets...</p>
          </div>
        ) : tickets.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <CheckCircle className="h-12 w-12 text-green-400 mb-3" />
            <h3 className="text-sm font-semibold text-gray-800 dark:text-zinc-200">No Open Escalations</h3>
            <p className="text-xs text-gray-400 dark:text-zinc-500 mt-1">All tickets have been resolved.</p>
          </div>
        ) : (
          tickets.map(ticket => {
            const isExpanded = expandedTicket === ticket.ticket_number;
            const isResolved = ticket.status === "Resolved";
            return (
              <div
                key={ticket.ticket_number}
                className={`rounded-xl border ${isResolved ? 'border-green-200 dark:border-green-900/40 bg-green-50/30 dark:bg-green-950/10' : 'border-red-200 dark:border-red-900/40 bg-red-50/30 dark:bg-red-950/10'} overflow-hidden transition-all`}
              >
                {/* Ticket Header */}
                <button
                  className="w-full flex items-center justify-between p-4 text-left cursor-pointer hover:bg-black/5 transition-colors"
                  onClick={() => setExpandedTicket(isExpanded ? null : ticket.ticket_number)}
                >
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${isResolved ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400' : 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400'}`}>
                      {ticket.status}
                    </span>
                    <div>
                      <span className="font-mono text-xs font-bold text-gray-700 dark:text-zinc-300">{ticket.ticket_number}</span>
                      <span className="ml-2 text-sm font-semibold text-gray-900 dark:text-white">{ticket.customer_name}</span>
                      <span className="ml-1 text-xs text-gray-400 dark:text-zinc-500">({ticket.customer_id})</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-400 dark:text-zinc-500">
                    <span>{new Date(ticket.created_date).toLocaleDateString()}</span>
                    {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </div>
                </button>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="px-4 pb-4 space-y-4 border-t border-gray-100 dark:border-zinc-800 pt-4">
                    {/* Summary */}
                    <div>
                      <h4 className="text-xs font-bold text-gray-600 dark:text-zinc-400 uppercase tracking-wider mb-1">Executive Summary</h4>
                      <p className="text-sm text-gray-700 dark:text-zinc-300">{ticket.summary}</p>
                    </div>

                    {/* Root Cause */}
                    <div className="p-3 rounded-lg bg-orange-50 dark:bg-orange-950/20 border border-orange-100 dark:border-orange-900/30">
                      <h4 className="text-xs font-bold text-orange-700 dark:text-orange-400 uppercase tracking-wider mb-1">Root Cause Analysis</h4>
                      <p className="text-sm text-orange-800 dark:text-orange-300">{ticket.root_cause_analysis}</p>
                    </div>

                    {/* Next Best Actions */}
                    <div>
                      <h4 className="text-xs font-bold text-gray-600 dark:text-zinc-400 uppercase tracking-wider mb-2">Next Best Actions — Add Work Items</h4>
                      <div className="space-y-2">
                        {ticket.next_best_actions.map((a, idx) => (
                          <div key={idx} className="flex gap-3 items-start p-3 rounded-lg bg-white dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700">
                            <div className="flex-1">
                              <div className="text-xs font-semibold text-gray-700 dark:text-zinc-200 mb-1">• {a.action}</div>
                              {isResolved ? (
                                <p className="text-xs text-green-700 dark:text-green-400 italic">{a.actionable_work_items || "—"}</p>
                              ) : (
                                <textarea
                                  rows={2}
                                  placeholder="Describe the work done for this action (required)..."
                                  value={workItems[ticket.ticket_number]?.[idx] ?? a.actionable_work_items}
                                  onChange={e => handleWorkItemChange(ticket.ticket_number, idx, e.target.value)}
                                  className="w-full text-xs bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-lg px-3 py-2 text-gray-700 dark:text-zinc-200 outline-none focus:ring-1 focus:ring-teal-500 resize-none"
                                />
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Customer Feedback */}
                    <div>
                      <h4 className="text-xs font-bold text-gray-600 dark:text-zinc-400 uppercase tracking-wider mb-2">Customer Feedback (required)</h4>
                      {isResolved ? (
                        <p className="text-sm text-gray-700 dark:text-zinc-300 italic p-3 rounded-lg bg-white dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700">{ticket.customer_feedback}</p>
                      ) : (
                        <textarea
                          rows={3}
                          placeholder="Enter the customer's feedback after resolution (required)..."
                          value={feedbacks[ticket.ticket_number] ?? ""}
                          onChange={e => setFeedbacks(p => ({ ...p, [ticket.ticket_number]: e.target.value }))}
                          className="w-full text-sm bg-white dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-lg px-3 py-2 text-gray-700 dark:text-zinc-200 outline-none focus:ring-1 focus:ring-teal-500 resize-none"
                        />
                      )}
                    </div>

                    {/* Status / Resolve Button */}
                    {!isResolved && (
                      <div className="flex flex-col items-end gap-2">
                        {resolveMsg[ticket.ticket_number] && (
                          <p className={`text-xs ${resolveMsg[ticket.ticket_number].startsWith('✓') ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                            {resolveMsg[ticket.ticket_number]}
                          </p>
                        )}
                        <button
                          onClick={() => handleResolve(ticket)}
                          disabled={submitting === ticket.ticket_number}
                          className={`px-5 py-2 ${submitting === ticket.ticket_number ? 'bg-teal-400 cursor-not-allowed' : 'bg-teal-600 hover:bg-teal-700 cursor-pointer'} text-white text-xs font-semibold rounded-lg shadow-md shadow-teal-500/20 flex items-center gap-2 transition-all`}
                        >
                          <CheckCircle className="h-4 w-4" />
                          {submitting === ticket.ticket_number ? "Resolving..." : "Resolve Ticket"}
                        </button>
                      </div>
                    )}

                    {isResolved && (
                      <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900/30 text-xs text-green-700 dark:text-green-400">
                        <CheckCircle className="h-4 w-4" />
                        <span>Resolved on {ticket.resolved_date ? new Date(ticket.resolved_date).toLocaleString() : "—"}. Customer journey has been updated.</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
