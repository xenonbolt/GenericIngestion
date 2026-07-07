import React from "react";
import { User, Activity, AlertTriangle, ShieldAlert, CheckCircle2 } from "lucide-react";

interface CustomerDelightTableProps {
  customers: any[];
  onSelectCustomer: (customerId: string) => void;
  loading: boolean;
}

export default function CustomerDelightTable({ customers, onSelectCustomer, loading }: CustomerDelightTableProps) {
  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center h-full">
        <Activity className="h-8 w-8 text-teal-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-2xl shadow-sm overflow-hidden flex flex-col h-full">
      <div className="p-6 border-b border-gray-100 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-900/50 flex justify-between items-center shrink-0">
        <div>
          <h2 className="text-xl font-black text-gray-900 dark:text-white tracking-tight flex items-center gap-2">
            <User className="h-5 w-5 text-teal-500" />
            Customer Delight
          </h2>
          <p className="text-sm text-gray-500 dark:text-zinc-400 mt-1">
            Overview of all enterprise customers and their real-time AI risk assessment metrics.
          </p>
        </div>
      </div>

      <div className="overflow-x-auto flex-1">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 dark:bg-zinc-800/50 border-b border-gray-200 dark:border-zinc-800">
              <th className="p-4 text-xs font-semibold text-gray-500 dark:text-zinc-400 uppercase tracking-wider">Customer ID</th>
              <th className="p-4 text-xs font-semibold text-gray-500 dark:text-zinc-400 uppercase tracking-wider">Name</th>
              <th className="p-4 text-xs font-semibold text-gray-500 dark:text-zinc-400 uppercase tracking-wider">Overall Sentiment</th>
              <th className="p-4 text-xs font-semibold text-gray-500 dark:text-zinc-400 uppercase tracking-wider">Escalation Risk</th>
              <th className="p-4 text-xs font-semibold text-gray-500 dark:text-zinc-400 uppercase tracking-wider text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 dark:divide-zinc-800">
            {customers.map((c) => {
              const riskProfile = c.risk_profile || {};
              const sentiment = riskProfile.sentiment || "Unknown";
              const escalation = riskProfile.escalation_score || 0;

              let sentimentColor = "text-gray-500 bg-gray-100 dark:bg-zinc-800";
              if (sentiment.toLowerCase().includes("positive")) sentimentColor = "text-green-600 bg-green-50 dark:bg-green-500/10";
              else if (sentiment.toLowerCase().includes("negative")) sentimentColor = "text-orange-600 bg-orange-50 dark:bg-orange-500/10";
              else if (sentiment.toLowerCase().includes("frustrated")) sentimentColor = "text-red-600 bg-red-50 dark:bg-red-500/10";
              else if (sentiment.toLowerCase().includes("neutral")) sentimentColor = "text-blue-600 bg-blue-50 dark:bg-blue-500/10";

              let escalationColor = "text-green-500";
              let EscalationIcon = CheckCircle2;
              if (escalation > 70) {
                escalationColor = "text-red-500";
                EscalationIcon = AlertTriangle;
              } else if (escalation > 40) {
                escalationColor = "text-orange-500";
                EscalationIcon = ShieldAlert;
              }

              return (
                <tr 
                  key={c.customer_id} 
                  className="hover:bg-gray-50 dark:hover:bg-zinc-800/30 transition-colors group cursor-pointer"
                  onClick={() => onSelectCustomer(c.customer_id)}
                >
                  <td className="p-4 text-sm font-mono text-gray-600 dark:text-zinc-400">
                    {c.customer_id}
                  </td>
                  <td className="p-4">
                    <div className="font-semibold text-gray-900 dark:text-white">
                      {c.customer_name || c.customer_id}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-zinc-500 uppercase tracking-wide">
                      {c.account_type}
                    </div>
                  </td>
                  <td className="p-4">
                    <span className={`px-2.5 py-1 rounded-md text-xs font-bold tracking-wide ${sentimentColor}`}>
                      {sentiment}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className={`flex items-center gap-2 font-bold ${escalationColor}`}>
                      <EscalationIcon className="h-4 w-4" />
                      {escalation}%
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <button
                      className="px-3 py-1.5 bg-teal-50 hover:bg-teal-100 dark:bg-teal-900/30 dark:hover:bg-teal-900/50 text-teal-600 dark:text-teal-400 text-xs font-semibold rounded-lg transition-colors"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectCustomer(c.customer_id);
                      }}
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              );
            })}
            
            {customers.length === 0 && (
              <tr>
                <td colSpan={5} className="p-8 text-center text-gray-500 dark:text-zinc-400 text-sm">
                  No customers available. Please run the ingestion pipeline.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
