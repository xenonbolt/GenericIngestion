import React, { useEffect, useState } from "react";
import { MessageSquare, Plus, ChevronLeft, ChevronRight, Loader2, Clock, Trash2 } from "lucide-react";
import { ChatSession, User } from "../types";

interface SidebarProps {
  user: User;
  isOpen: boolean;
  onToggle: () => void;
  currentSessionId: string;
  onSelectSession: (sessionId: string) => void;
  onNewChat: () => void;
}

export default function Sidebar({
  user,
  isOpen,
  onToggle,
  currentSessionId,
  onSelectSession,
  onNewChat,
}: SidebarProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user && isOpen) {
      fetchSessions();
    }
  }, [user, isOpen, currentSessionId]); // Re-fetch if session changes so counts update

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/chat/sessions/${user.username}`);
      if (response.ok) {
        const data = await response.json();
        setSessions(data.sessions || []);
      }
    } catch (err) {
      console.error("Failed to fetch sessions:", err);
    } finally {
      setLoading(false);
    }
  };

  const deleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation();
    try {
      await fetch(`/chat/history/${sessionId}`, { method: 'DELETE' });
      if (sessionId === currentSessionId) {
        onNewChat();
      } else {
        fetchSessions();
      }
    } catch (err) {
      console.error("Failed to delete session:", err);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "Unknown";
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, { month: "short", day: "numeric", hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div
      className={`relative flex flex-col bg-white dark:bg-zinc-900 border-r border-gray-200 dark:border-zinc-800 transition-all duration-300 ease-in-out ${
        isOpen ? "w-72" : "w-0"
      } h-full`}
    >
      {/* Toggle Button */}
      <button
        onClick={onToggle}
        className={`absolute top-4 -right-10 z-20 p-2 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-r-xl shadow-sm text-gray-500 hover:text-teal-600 transition-colors cursor-pointer ${
          !isOpen && "opacity-100"
        }`}
      >
        {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
      </button>

      <div className={`flex flex-col h-full overflow-hidden ${isOpen ? "opacity-100" : "opacity-0 invisible"} transition-opacity duration-300 delay-100`}>
        
        {/* Header */}
        <div className="p-4 border-b border-gray-100 dark:border-zinc-800 flex items-center justify-between shrink-0">
          <h2 className="text-sm font-semibold text-gray-800 dark:text-zinc-200 flex items-center gap-2">
            <Clock size={16} className="text-teal-500" />
            Chat History
          </h2>
        </div>

        {/* New Chat Button */}
        <div className="p-4 shrink-0">
          <button
            onClick={onNewChat}
            className="w-full py-2.5 px-4 bg-teal-50 dark:bg-teal-950/30 text-teal-700 dark:text-teal-400 hover:bg-teal-100 dark:hover:bg-teal-900/40 font-medium rounded-xl text-sm transition-all flex items-center justify-center gap-2 border border-teal-200 dark:border-teal-900/50 cursor-pointer"
          >
            <Plus size={16} />
            New Thread
          </button>
        </div>

        {/* Session List */}
        <div className="flex-1 overflow-y-auto px-3 pb-4 space-y-1 custom-scrollbar">
          {loading && sessions.length === 0 ? (
            <div className="flex justify-center items-center py-8">
              <Loader2 className="animate-spin text-teal-500" size={24} />
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-8 text-xs text-gray-400">
              No chat history found.
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.session_id}
                onClick={() => onSelectSession(session.session_id)}
                className={`group relative w-full text-left p-3 rounded-xl transition-all flex flex-col gap-1 cursor-pointer ${
                  currentSessionId === session.session_id
                    ? "bg-teal-500/10 border-teal-500/30 border text-teal-700 dark:text-teal-300"
                    : "bg-transparent border border-transparent hover:bg-gray-100 dark:hover:bg-zinc-800/60 text-gray-700 dark:text-zinc-300"
                }`}
              >
                <div className="flex items-start gap-2">
                  <MessageSquare size={14} className={`shrink-0 mt-0.5 ${currentSessionId === session.session_id ? 'text-teal-500' : 'text-gray-400'}`} />
                  <span className="text-sm font-medium leading-tight line-clamp-2 pr-6">
                    {session.title || "New Conversation"}
                  </span>
                </div>
                <div className="flex justify-between items-center pl-6 pr-1 mt-1">
                  <span className="text-[10px] text-gray-400 font-medium uppercase tracking-wider">
                    {formatDate(session.last_active)}
                  </span>
                  <span className="text-[10px] bg-gray-200 dark:bg-zinc-700 text-gray-600 dark:text-zinc-300 px-1.5 py-0.5 rounded-full">
                    {session.message_count}
                  </span>
                </div>
                <button
                  onClick={(e) => deleteSession(e, session.session_id)}
                  className="absolute right-3 top-3 p-1.5 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity bg-white/80 dark:bg-zinc-800/80 rounded-md backdrop-blur-sm"
                  title="Delete chat"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
