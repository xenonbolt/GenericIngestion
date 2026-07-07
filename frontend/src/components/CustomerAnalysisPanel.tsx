import React, { useState } from "react";
import { User, Activity, AlertTriangle, MessageSquare, ArrowLeft } from "lucide-react";

interface AnalysisData {
  summary: string;
  sentiment: string;
  escalation_score: number;
  root_cause_analysis: string;
  complaint_themes?: string[];
  next_best_action?: string[];
  timeline?: string;
  customer_id?: string;
  customer_name?: string;
}

interface CustomerAnalysisPanelProps {
  data: AnalysisData | null;
  loading: boolean;
  onBack?: () => void;
}

export default function CustomerAnalysisPanel({ data, loading, onBack }: CustomerAnalysisPanelProps) {
  const [escalating, setEscalating] = useState(false);
  const [escalationTicket, setEscalationTicket] = useState<string | null>(null);
  const [escalationError, setEscalationError] = useState<string | null>(null);

  const handleEscalationRequest = async () => {
    if (!data) return;
    setEscalating(true);
    setEscalationError(null);
    try {
      const response = await fetch('/api/escalations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: data.customer_id || "",
          customer_name: data.customer_name || data.customer_id || "Unknown Customer",
          summary: data.summary,
          root_cause_analysis: data.root_cause_analysis || "",
          next_best_actions: data.next_best_action || []
        })
      });
      const result = await response.json();
      if (response.ok && result.ticket_number) {
        setEscalationTicket(result.ticket_number);
      } else {
        setEscalationError("Failed to create escalation request.");
      }
    } catch (e) {
      console.error(e);
      setEscalationError("Error connecting to server.");
    } finally {
      setEscalating(false);
    }
  };
  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-2xl shadow-sm p-8 text-center animate-pulse">
        <div className="h-16 w-16 bg-teal-100 dark:bg-teal-900/50 rounded-full mb-4 flex items-center justify-center">
          <Activity className="h-8 w-8 text-teal-500 animate-spin" />
        </div>
        <h3 className="text-lg font-bold text-gray-800 dark:text-zinc-200 mb-2">
          Analyzing Customer History
        </h3>
        <p className="text-sm text-gray-500 dark:text-zinc-400">
          Aggregating ticket sentiment, SLA breaches, and generating predictive risk scores...
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-2xl shadow-sm p-8 text-center">
        <div className="h-16 w-16 bg-gray-100 dark:bg-zinc-800 rounded-full mb-4 flex items-center justify-center">
          <User className="h-8 w-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-bold text-gray-800 dark:text-zinc-200 mb-2">
          Select a Customer
        </h3>
        <p className="text-sm text-gray-500 dark:text-zinc-400">
          Choose a customer from the directory to generate a real-time sentiment and escalation analysis.
        </p>
      </div>
    );
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case "positive": return "text-green-500 bg-green-50 dark:bg-green-500/10 border-green-200 dark:border-green-500/20";
      case "neutral": return "text-blue-500 bg-blue-50 dark:bg-blue-500/10 border-blue-200 dark:border-blue-500/20";
      case "negative": return "text-orange-500 bg-orange-50 dark:bg-orange-500/10 border-orange-200 dark:border-orange-500/20";
      case "frustrated": return "text-red-500 bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/20";
      default: return "text-gray-500 bg-gray-50 dark:bg-zinc-800 border-gray-200 dark:border-zinc-700";
    }
  };

  const scoreColor = data.escalation_score > 70 ? "text-red-500" : data.escalation_score > 40 ? "text-orange-500" : "text-green-500";
  const scoreBg = data.escalation_score > 70 ? "bg-red-500" : data.escalation_score > 40 ? "bg-orange-500" : "bg-green-500";

  const formatMarkdown = (text: string) => {
    return text.split('\n').map((line, i) => {
      let formattedLine = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      formattedLine = formattedLine.replace(/^\*\s*(.*)/, '• $1');
      return (
        <span key={i} className="block" dangerouslySetInnerHTML={{ __html: formattedLine }} />
      );
    });
  };

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-2xl shadow-sm overflow-hidden h-full">
      <div className="p-6 border-b border-gray-100 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-900/50 flex justify-between items-center shrink-0">
        <div>
          <h2 className="text-xl font-black text-gray-900 dark:text-white tracking-tight flex items-center gap-2">
            <Activity className="h-5 w-5 text-teal-500" />
            Executive Risk Assessment
          </h2>
          <p className="text-sm text-gray-500 dark:text-zinc-400 mt-1">
            AI-generated synthesis of historical tickets and interaction transcripts.
          </p>
        </div>
        {onBack && (
          <button 
            onClick={onBack}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold text-gray-600 dark:text-zinc-300 bg-white dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-lg hover:bg-gray-50 dark:hover:bg-zinc-700 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to List
          </button>
        )}
      </div>

      <div className="p-6 space-y-6 overflow-y-auto">
        
        {/* Top Metrics Row */}
        <div className="grid grid-cols-2 gap-4">
          <div className={`p-4 rounded-xl border flex flex-col justify-center items-center text-center ${getSentimentColor(data.sentiment)}`}>
            <span className="text-xs font-bold uppercase tracking-wider mb-1 opacity-80">Overall Sentiment</span>
            <span className="text-2xl font-black">{data.sentiment}</span>
          </div>

          <div className="p-4 rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex flex-col justify-center items-center text-center relative overflow-hidden">
            <span className="text-xs font-bold uppercase tracking-wider text-gray-500 dark:text-zinc-400 mb-1">Escalation Risk</span>
            <div className="flex items-end gap-1">
              <span className={`text-3xl font-black tracking-tighter ${scoreColor}`}>{data.escalation_score}</span>
              <span className="text-lg font-bold text-gray-400 pb-1">%</span>
            </div>
            
            {/* Progress Bar */}
            <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-gray-100 dark:bg-zinc-800">
              <div className={`h-full ${scoreBg}`} style={{ width: `${data.escalation_score}%` }} />
            </div>
          </div>
        </div>

        {/* Summary Card */}
        <div className="p-5 rounded-xl border border-gray-200 dark:border-zinc-800 bg-gray-50 dark:bg-zinc-800/30">
          <h3 className="text-sm font-bold text-gray-800 dark:text-zinc-200 flex items-center gap-2 mb-3">
            <MessageSquare className="h-4 w-4 text-violet-500" />
            Executive Summary
          </h3>
          <p className="text-sm text-gray-600 dark:text-zinc-300 leading-relaxed">
            {data.summary}
          </p>
        </div>

        {/* Root Cause Analysis Card */}
        {data.escalation_score > 30 && data.root_cause_analysis && (
          <div className="p-5 rounded-xl border border-red-100 dark:border-red-900/30 bg-red-50/50 dark:bg-red-950/10">
            <h3 className="text-sm font-bold text-red-800 dark:text-red-400 flex items-center gap-2 mb-3">
              <AlertTriangle className="h-4 w-4" />
              Root Cause Analysis
            </h3>
            <p className="text-sm text-red-700/80 dark:text-red-300/80 leading-relaxed">
              {data.root_cause_analysis}
            </p>
          </div>
        )}

        {/* Customer Journey Timeline */}
        {data.timeline && (
          <div className="p-5 rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
            <h3 className="text-sm font-bold text-gray-800 dark:text-zinc-200 mb-3 flex items-center gap-2">
              <Activity className="h-4 w-4 text-violet-500" />
              Customer Journey Timeline
            </h3>
            <div className="text-sm text-gray-600 dark:text-zinc-300 leading-relaxed font-mono space-y-1">
              {formatMarkdown(data.timeline)}
            </div>
            {data.escalation_score > 50 && (
              <div className="mt-4 pt-4 border-t border-gray-100 dark:border-zinc-800 space-y-3">
                {!escalationTicket ? (
                  <div className="flex justify-end">
                    <button
                      onClick={handleEscalationRequest}
                      disabled={escalating}
                      className={`px-4 py-2 ${escalating ? 'bg-red-400 cursor-not-allowed' : 'bg-red-600 hover:bg-red-700 cursor-pointer'} text-white text-xs font-semibold rounded-lg shadow-md shadow-red-500/20 flex items-center gap-2 transition-all`}
                    >
                      <AlertTriangle className={`h-4 w-4 ${escalating ? 'animate-pulse' : ''}`} />
                      {escalating ? 'Requesting...' : 'Request Escalation Manager'}
                    </button>
                  </div>
                ) : (
                  <div className="p-3 rounded-lg bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900/40 text-xs text-green-700 dark:text-green-400 flex items-start gap-2">
                    <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-green-500" />
                    <div>
                      <span className="font-semibold">Escalation Request Created for Risk Manager</span><br />
                      Ticket: <span className="font-mono font-bold">{escalationTicket}</span> is now <span className="font-semibold">Open</span> and assigned to the Risk Manager queue.
                    </div>
                  </div>
                )}
                {escalationError && (
                  <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/40 text-xs text-red-700 dark:text-red-400">
                    {escalationError}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
