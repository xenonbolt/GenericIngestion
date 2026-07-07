import React from "react";
import { User, Activity, AlertTriangle, MessageSquare, Flame } from "lucide-react";

interface AnalysisData {
  summary: string;
  sentiment: string;
  escalation_score: number;
  root_cause_analysis: string;
  complaint_themes?: string[];
  next_best_action?: string[];
}

interface CustomerAnalysisPanelProps {
  data: AnalysisData | null;
  loading: boolean;
}

export default function CustomerAnalysisPanel({ data, loading }: CustomerAnalysisPanelProps) {
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

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-2xl shadow-sm overflow-hidden h-full">
      <div className="p-6 border-b border-gray-100 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-900/50">
        <h2 className="text-xl font-black text-gray-900 dark:text-white tracking-tight flex items-center gap-2">
          <Activity className="h-5 w-5 text-teal-500" />
          Executive Risk Assessment
        </h2>
        <p className="text-sm text-gray-500 dark:text-zinc-400 mt-1">
          AI-generated synthesis of historical tickets and interaction transcripts.
        </p>
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

        {/* Complaint Themes & Next Best Action */}
        {(data.complaint_themes?.length || data.next_best_action?.length) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.complaint_themes && data.complaint_themes.length > 0 && (
              <div className="p-5 rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
                <h3 className="text-sm font-bold text-gray-800 dark:text-zinc-200 mb-3">Complaint Themes</h3>
                <div className="flex flex-wrap gap-2">
                  {data.complaint_themes.map((theme, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-md text-xs font-medium bg-gray-100 dark:bg-zinc-800 text-gray-700 dark:text-zinc-300">
                      {theme}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {data.next_best_action && data.next_best_action.length > 0 && (
              <div className="p-5 rounded-xl border border-teal-200 dark:border-teal-900/30 bg-teal-50/50 dark:bg-teal-900/10">
                <h3 className="text-sm font-bold text-teal-800 dark:text-teal-400 mb-3">Next Best Actions</h3>
                <ul className="space-y-2">
                  {data.next_best_action.map((action, i) => (
                    <li key={i} className="text-sm text-teal-700/90 dark:text-teal-300/80 flex items-start gap-2">
                      <span className="text-teal-500 mt-0.5">•</span>
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
