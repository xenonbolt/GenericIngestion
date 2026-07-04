import React, { useState, useRef, useEffect } from "react";
import { Message, User } from "../types";
import { Send, Bot, User as UserIcon, Sparkles, Terminal, ShieldAlert } from "lucide-react";

interface ChatPanelProps {
  messages: Message[];
  onSendMessage: (text: string) => void;
  loading: boolean;
  user: User;
}

export default function ChatPanel({ messages, onSendMessage, loading, user }: ChatPanelProps) {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive or loading state changes
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSendMessage(input.trim());
    setInput("");
  };

  const suggestions = [
    "Check multi-agent system status",
    "Explain how knowledge ingestion gets approved",
    "Trigger full strategic planning trace flow",
  ];

  return (
    <div className="flex flex-col h-[620px] bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl overflow-hidden transition-all duration-300 shadow-sm">
      
      {/* Header Panel */}
      <div className="px-4 py-3 border-b border-gray-100 dark:border-zinc-800/80 bg-gray-50/50 dark:bg-zinc-900/50 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-teal-500/15 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold">
            <Bot className="h-4 w-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-gray-800 dark:text-zinc-200">
              Orchestrator Chat Console
            </h4>
            <span className="text-[10px] text-teal-600 dark:text-teal-400 font-mono font-medium flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-teal-500 animate-pulse" />
              Agent Core Online (v3.5)
            </span>
          </div>
        </div>
        <div className="px-2 py-0.5 rounded bg-gray-100 dark:bg-zinc-800 text-[9px] font-mono text-gray-500 dark:text-zinc-400 uppercase tracking-wider">
          TLS Tunnel Active
        </div>
      </div>

      {/* Message List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          /* Empty Chat Welcome Card */
          <div className="flex flex-col h-full justify-center items-center text-center p-6 space-y-4 max-w-sm mx-auto">
            <div className="h-12 w-12 rounded-2xl bg-gradient-to-tr from-teal-500 to-violet-600 text-white flex items-center justify-center shadow-lg shadow-teal-500/10">
              <Bot className="h-6 w-6" />
            </div>
            <div>
              <h5 className="text-sm font-bold text-gray-800 dark:text-zinc-200">
                Enterprise AI Orchestrator
              </h5>
              <p className="text-xs text-gray-400 dark:text-zinc-500 mt-1 leading-normal">
                Ask questions or index databases. Every response is validated by a 3-stage alignment loop.
              </p>
            </div>

            {/* Suggestions */}
            <div className="w-full pt-2 flex flex-col gap-2">
              <span className="text-[10px] uppercase tracking-wider font-semibold text-gray-400 dark:text-zinc-500 text-left">
                Suggested Actions
              </span>
              {suggestions.map((s, idx) => (
                <button
                  key={idx}
                  onClick={() => onSendMessage(s)}
                  className="w-full text-left p-2.5 bg-gray-50 hover:bg-teal-50/40 dark:bg-zinc-800/40 dark:hover:bg-teal-950/20 text-[11px] text-gray-600 dark:text-zinc-300 font-medium rounded-lg border border-gray-100 dark:border-zinc-800/80 hover:border-teal-300 dark:hover:border-teal-900/60 transition-all cursor-pointer"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 max-w-[85%] ${
                msg.sender === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
              }`}
            >
              {/* Avatar */}
              <div
                className={`h-7 w-7 rounded-lg shrink-0 flex items-center justify-center text-xs font-bold ${
                  msg.sender === "user"
                    ? "bg-violet-500 text-white"
                    : "bg-teal-500/10 text-teal-600 dark:text-teal-400"
                }`}
              >
                {msg.sender === "user" ? (
                  <UserIcon className="h-4 w-4" />
                ) : (
                  <Bot className="h-4 w-4" />
                )}
              </div>

              {/* Balloon */}
              <div className="flex flex-col gap-1">
                <div
                  className={`px-3.5 py-2.5 rounded-2xl text-xs leading-relaxed ${
                    msg.sender === "user"
                      ? "bg-violet-600 text-white rounded-tr-none"
                      : "bg-gray-100 dark:bg-zinc-800 text-gray-800 dark:text-zinc-200 rounded-tl-none border border-gray-200/50 dark:border-zinc-800/50"
                  }`}
                >
                  {/* Process simple markdown formatting for bold and list bullets */}
                  <div className="space-y-1 select-text">
                    {msg.text.split("\n").map((line, lIdx) => {
                      if (line.trim().startsWith("- ")) {
                        return (
                          <li key={lIdx} className="ml-2 list-disc">
                            {line.substring(2)}
                          </li>
                        );
                      }
                      // Handle double asterisks for bold
                      const parts = line.split("**");
                      return (
                        <p key={lIdx}>
                          {parts.map((p, pIdx) =>
                            pIdx % 2 === 1 ? (
                              <strong key={pIdx} className="font-semibold text-gray-900 dark:text-white">
                                {p}
                              </strong>
                            ) : (
                              p
                            )
                          )}
                        </p>
                      );
                    })}
                  </div>
                </div>

                {/* Timestamp and Trace info */}
                <div
                  className={`flex items-center gap-2 text-[10px] text-gray-400 dark:text-zinc-500 px-1 ${
                    msg.sender === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <span>{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  {msg.sender === "assistant" && msg.traceResult && (
                    <span className="font-mono text-[9px] text-teal-600 dark:text-teal-400 flex items-center gap-1 bg-teal-50 dark:bg-teal-950/40 px-1.5 py-0.5 rounded">
                      <Terminal className="h-2.5 w-2.5" />
                      Trace: {msg.traceResult.tokens}t • {msg.traceResult.latency}ms
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}

        {/* Typing Indicator */}
        {loading && (
          <div className="flex gap-3 max-w-[85%] mr-auto">
            <div className="h-7 w-7 rounded-lg shrink-0 flex items-center justify-center bg-teal-500/10 text-teal-600 dark:text-teal-400 text-xs">
              <Bot className="h-4 w-4" />
            </div>
            <div className="flex flex-col gap-1">
              <div className="px-4 py-3 bg-gray-50 dark:bg-zinc-800 text-gray-500 dark:text-zinc-400 rounded-2xl rounded-tl-none border border-gray-200/50 dark:border-zinc-800/50 text-xs">
                <div className="flex items-center gap-2">
                  <span className="flex gap-1 items-center">
                    <span className="h-1.5 w-1.5 bg-teal-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
                    <span className="h-1.5 w-1.5 bg-teal-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
                    <span className="h-1.5 w-1.5 bg-teal-500 rounded-full animate-bounce" />
                  </span>
                  <span className="font-mono text-[10px] text-zinc-400">Agent orchestrating LangGraph path...</span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={scrollRef} />
      </div>

      {/* Input panel footer */}
      <form
        onSubmit={handleSubmit}
        className="p-3 border-t border-gray-100 dark:border-zinc-800 bg-white dark:bg-zinc-900 shrink-0 flex gap-2 items-center"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask orchestrator or issue system commands..."
          disabled={loading}
          className="flex-1 px-4 py-2.5 bg-gray-50 dark:bg-zinc-800/60 border border-gray-300 dark:border-zinc-700/80 rounded-xl text-xs text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-teal-500 text-sm disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="p-2.5 bg-gradient-to-tr from-teal-500 to-violet-600 hover:from-teal-600 hover:to-violet-700 text-white rounded-xl shadow-md shadow-teal-500/10 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed transition-all shrink-0"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
