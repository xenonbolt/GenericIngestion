import { useState, useEffect, useRef } from "react";
import { User, Message, TraceNode, TraceEvent } from "./types";
import LoginScreen from "./components/LoginScreen";
import ChatPanel from "./components/ChatPanel";
import TraceGraph from "./components/TraceGraph";
import UploadModal from "./components/UploadModal";
import AdminDashboardModal from "./components/AdminDashboardModal";
import Sidebar from "./components/Sidebar";
import {
  ShieldAlert,
  Sparkles,
  Cpu,
  Coins,
  Clock,
  Activity,
  LogOut,
  Sun,
  Moon,
  Database,
  Workflow,
  RefreshCw,
  Play,
  UploadCloud,
  LayoutDashboard,
  Zap,
} from "lucide-react";

const initialNodes: TraceNode[] = [
  { id: "query_translator", label: "Query Translator", status: "idle" },
  { id: "intent_analyzer", label: "Intent Analyzer", status: "idle" },
  { id: "task_decomposer", label: "Task Decomposer", status: "idle" },
  { id: "data_analysis", label: "Pandas Data Agent", status: "idle" },
  { id: "networkx_qa", label: "NetworkX Programmatic QA", status: "idle" },
  { id: "kuzu_qa", label: "Kùzu Cypher Graph QA", status: "idle" },
  { id: "graph_judge", label: "Graph Evaluation Judge", status: "idle" },
  { id: "retrieval_synthesizer", label: "Vector Retrieval", status: "idle" },
  { id: "relevance_evaluator", label: "Relevance Evaluator", status: "idle" },
  { id: "generator_agent", label: "Final Response Generator", status: "idle" },
];

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [theme, setTheme] = useState<"light" | "dark">("dark"); // Default dark mode look
  
  // Modals
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isAdminOpen, setIsAdminOpen] = useState(false);

  // Chat state
  const [messages, setMessages] = useState<Message[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const loadSessionHistory = async (sessionId: string) => {
    if (!user) return;
    try {
      const response = await fetch(`/chat/history/${sessionId}`);
      if (response.ok) {
        const data = await response.json();
        const loadedMessages = data.messages.map((msg: any) => ({
          id: msg.id || `${msg.role}-${Math.random()}`,
          sender: msg.role === "user" ? "user" : "assistant",
          text: msg.content,
          timestamp: msg.timestamp || new Date().toISOString(),
        }));
        setMessages(loadedMessages);
        setUser({ ...user, sessionId });
        // Clear trace nodes
        setNodesState(initialNodes.map(n => ({ ...n, status: "idle" })));
        setAccumulatedMetrics({ tokens: 0, latency: 0, cost: 0 });
        setTraceStatus("idle");
        setActiveNodeDetails(null);
      }
    } catch (err) {
      console.error("Failed to load session history:", err);
    }
  };

  const handleNewChat = () => {
    if (!user) return;
    setUser({ ...user, sessionId: `session-${Date.now()}` });
    setMessages([]);
    setNodesState(initialNodes.map(n => ({ ...n, status: "idle" })));
    setAccumulatedMetrics({ tokens: 0, latency: 0, cost: 0 });
    setTraceStatus("idle");
    setActiveNodeDetails(null);
  };

  // Live trace state
  const [nodesState, setNodesState] = useState<TraceNode[]>(initialNodes);
  const [activeNodeDetails, setActiveNodeDetails] = useState<any>(null);
  const [accumulatedMetrics, setAccumulatedMetrics] = useState({
    tokens: 0,
    latency: 0,
    cost: 0,
  });
  const [traceStatus, setTraceStatus] = useState<"idle" | "running" | "completed">("idle");

  // WebSocket connection
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Custom WebSocket backend url state (for flexibility to hook up Python backend)
  const [customWsUrl, setCustomWsUrl] = useState("");
  const [useCustomWs, setUseCustomWs] = useState(false);

  // Read session on startup
  useEffect(() => {
    const savedUser = localStorage.getItem("agentic_user");
    if (savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        if (!parsedUser.sessionId) {
          parsedUser.sessionId = `session-${Date.now()}`;
          localStorage.setItem("agentic_user", JSON.stringify(parsedUser));
        }
        setUser(parsedUser);
      } catch (e) {
        localStorage.removeItem("agentic_user");
      }
    }

    // Load saved theme
    const savedTheme = localStorage.getItem("agentic_theme") as "light" | "dark";
    if (savedTheme) {
      setTheme(savedTheme);
    }
  }, []);

  // Sync theme to root class
  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    localStorage.setItem("agentic_theme", theme);
  }, [theme]);

  // Handle WebSocket Ingress
  useEffect(() => {
    if (!user) return;

    function connectWS() {
      // Clear any pending reconnect
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);

      try {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const fallbackUrl = `${protocol}//${window.location.host}/ws/agent-stream`;
        const targetUrl = useCustomWs && customWsUrl ? customWsUrl : fallbackUrl;

        console.log("Connecting WS to:", targetUrl);
        const ws = new WebSocket(targetUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log("WS Connected successfully!");
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data: TraceEvent = JSON.parse(event.data);
            
            if (data.type === "node_active" && data.nodeId) {
              setTraceStatus("running");
              setNodesState((prev) =>
                prev.map((n) =>
                  n.id === data.nodeId
                    ? {
                        ...n,
                        status: "active",
                        action: data.action,
                      }
                    : n
                )
              );
              setActiveNodeDetails({
                nodeId: data.nodeId,
                nodeName: data.nodeName,
                action: data.action,
              });

            } else if (data.type === "node_completed" && data.nodeId) {
              setNodesState((prev) =>
                prev.map((n) =>
                  n.id === data.nodeId ? { 
                    ...n, 
                    status: "completed",
                    tokens: data.metrics?.tokens,
                    latency: data.metrics?.latency,
                    cost: data.metrics?.cost
                  } : n
                )
              );
              
              if (data.metrics) {
                setActiveNodeDetails((prev) => prev?.nodeId === data.nodeId ? { ...prev, metrics: data.metrics } : prev);
                setAccumulatedMetrics((prev) => ({
                  tokens: prev.tokens + (data.metrics.tokens || 0),
                  latency: prev.latency + (data.metrics.latency || 0),
                  cost: prev.cost + (data.metrics.cost || 0),
                }));
              }
            } else if (data.type === "trace_completed") {
              setTraceStatus("completed");
              // Cap at exact total cost provided by backend if available
              if (data.totalCost) {
                setAccumulatedMetrics((prev) => ({
                  ...prev,
                  cost: data.totalCost || prev.cost,
                  tokens: data.totalTokens || prev.tokens,
                  latency: data.totalLatency || prev.latency,
                }));
              }
            }
          } catch (err) {
            console.error("Failed to parse WS incoming payload:", err);
          }
        };

        ws.onclose = () => {
          console.log("WS Closed. Scheduling reconnect...");
          setWsConnected(false);
          // Auto reconnect after 4 seconds
          reconnectTimeoutRef.current = setTimeout(connectWS, 4000);
        };

        ws.onerror = (err) => {
          console.error("WS Socket error:", err);
          setWsConnected(false);
        };
      } catch (err) {
        console.error("WS initialization failed:", err);
        setWsConnected(false);
      }
    }

    connectWS();

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
    };
  }, [user, useCustomWs, customWsUrl]);

  const handleLogout = () => {
    localStorage.removeItem("agentic_user");
    setUser(null);
    setMessages([]);
    setNodesState(initialNodes);
  };

  const handleSendMessage = async (text: string) => {
    if (!user || chatLoading) return;

    // Reset flowchart state
    setNodesState(initialNodes.map(n => ({ ...n, status: "idle" })));
    setAccumulatedMetrics({ tokens: 0, latency: 0, cost: 0 });
    setTraceStatus("running");
    setActiveNodeDetails(null);

    // Append user message
    const userMsgId = `user-${Date.now()}`;
    const userMsg: Message = {
      id: userMsgId,
      sender: "user",
      text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setChatLoading(true);

    // Trigger trace over WebSockets
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "trigger-trace" }));
    }

    // Call chat rest endpoint
    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: user.username,
          session_id: user.sessionId,
          message: text,
        }),
      });

      if (!response.ok) {
        throw new Error("Chat api request failed.");
      }

      const data = await response.json();

      // Append assistant message once response is returned
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-${Date.now()}`,
          sender: "assistant",
          text: data.reply,
          timestamp: new Date().toISOString(),
          traceResult: {
            tokens: 1850,
            latency: 2820,
            cost: 0.000555,
          },
        },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-err-${Date.now()}`,
          sender: "assistant",
          text: `**System Connection Halt:**\nFailed to orchestrate server model pipeline. Reason: ${err.message}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };



  if (!user) {
    return (
      <div className={theme === "dark" ? "dark" : ""}>
        <LoginScreen onLoginSuccess={setUser} />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 transition-colors duration-300 overflow-hidden">
      
      {/* Top Header Panel */}
      <header className="px-6 py-4 border-b border-gray-200 dark:border-zinc-800/80 bg-white/95 dark:bg-zinc-900/95 backdrop-blur-md sticky top-0 z-40 transition-colors duration-300">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
          
          {/* Left Branding */}
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-teal-500 to-violet-600 flex items-center justify-center text-white shadow-md shadow-teal-500/10">
              <Workflow className="h-5 w-5 animate-pulse" style={{ animationDuration: "2s" }} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-extrabold font-sans tracking-tight bg-gradient-to-r from-teal-600 to-violet-500 dark:from-teal-400 dark:to-violet-400 bg-clip-text text-transparent">
                  Enterprise Agentic Intelligence
                </h1>
                <span className="px-1.5 py-0.5 rounded bg-teal-50 dark:bg-teal-950/40 border border-teal-200/50 dark:border-teal-900/40 text-[9px] font-mono font-bold text-teal-600 dark:text-teal-400">
                  PLATFORM PROTOTYPE
                </span>
              </div>
              <p className="text-[11px] text-gray-400 dark:text-zinc-500">
                Authorized Tunnel: <span className="font-mono text-gray-500 dark:text-zinc-400">{user.sessionId}</span>
              </p>
            </div>
          </div>

          {/* Right Action Bar */}
          <div className="flex items-center gap-3">
            
            {/* Theme Toggle */}
            <button
              onClick={() => setTheme(theme === "light" ? "dark" : "light")}
              className="p-2 bg-gray-100 dark:bg-zinc-800 hover:bg-gray-200 dark:hover:bg-zinc-700 text-gray-600 dark:text-zinc-300 rounded-xl border border-gray-200 dark:border-zinc-700/80 transition-all cursor-pointer"
              title="Toggle Theme Mode"
            >
              {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
            </button>

            {/* Ingestion Trigger Button */}
            <button
              onClick={() => setIsUploadOpen(true)}
              className="px-4 py-2 bg-teal-500 hover:bg-teal-600 text-white text-xs font-semibold rounded-xl shadow-md shadow-teal-500/10 flex items-center gap-2 cursor-pointer transition-all"
            >
              <UploadCloud className="h-4 w-4" />
              Upload Knowledge
            </button>

            {/* Admin trigger button */}
            {user.role === "admin" && (
              <button
                onClick={() => setIsAdminOpen(true)}
                className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-violet-500/10 flex items-center gap-2 cursor-pointer transition-all"
              >
                <LayoutDashboard className="h-4 w-4" />
                Admin Dashboard
              </button>
            )}

            {/* User Session Details */}
            <div className="h-9 px-3.5 bg-gray-100 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700/80 rounded-xl flex items-center gap-2.5">
              <div className="h-5 w-5 rounded bg-teal-500/10 dark:bg-teal-500/20 text-teal-600 dark:text-teal-400 flex items-center justify-center font-bold text-xs">
                {user.username.charAt(0).toUpperCase()}
              </div>
              <div className="text-[11px]">
                <div className="font-semibold text-gray-800 dark:text-zinc-300 leading-tight">
                  {user.username}
                </div>
                <div className="text-[9px] text-gray-400 dark:text-zinc-500 uppercase font-mono tracking-wider font-bold">
                  {user.role}
                </div>
              </div>
            </div>

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/20 rounded-xl border border-transparent hover:border-red-100 dark:hover:border-red-900/30 transition-all cursor-pointer"
              title="Logout session"
            >
              <LogOut className="h-4.5 w-4.5" />
            </button>

          </div>
        </div>
      </header>

      {/* Main Content Layout Grid */}
      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          user={user}
          isOpen={isSidebarOpen}
          onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
          currentSessionId={user.sessionId}
          onSelectSession={loadSessionHistory}
          onNewChat={handleNewChat}
        />
        <main className="flex-1 overflow-y-auto w-full p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left Side: Conversational Panel */}
          <section className="col-span-1 lg:col-span-5 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold tracking-tight text-gray-700 dark:text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
              <Zap className="h-4 w-4 text-teal-500" />
              Agentic Chat Console
            </h3>
          </div>
          <ChatPanel
            messages={messages}
            onSendMessage={handleSendMessage}
            loading={chatLoading}
            user={user}
          />
        </section>

        {/* Right Side: Graph Trace Visualization */}
        <section className="col-span-1 lg:col-span-7 flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <h3 className="text-sm font-bold tracking-tight text-gray-700 dark:text-zinc-400 uppercase tracking-wider flex items-center gap-1.5">
              <Workflow className="h-4 w-4 text-violet-500" />
              Live Multi-Agent Trace
            </h3>

            {/* WebSocket controls and Status indicators */}
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5 text-[10.5px]">
                <span className={`h-2 w-2 rounded-full ${wsConnected ? "bg-green-500" : "bg-amber-500 animate-pulse"}`} />
                <span className="text-gray-500 dark:text-zinc-400 font-mono">
                  {wsConnected ? "WS connected" : "WS fallback (local sim)"}
                </span>
              </span>
              <button
                onClick={() => setUseCustomWs(!useCustomWs)}
                className={`text-[10px] py-1 px-2.5 rounded-lg border font-medium transition-all cursor-pointer ${
                  useCustomWs
                    ? "bg-teal-50 border-teal-200 text-teal-700 dark:bg-teal-950/20 dark:border-teal-900/60 dark:text-teal-400"
                    : "bg-gray-100 dark:bg-zinc-800 border-gray-200 dark:border-zinc-700 text-gray-500 dark:text-zinc-400"
                }`}
              >
                Custom WS
              </button>
            </div>
          </div>

          {/* Custom WS parameters entry */}
          {useCustomWs && (
            <div className="p-3 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl flex items-center gap-3 shadow-sm animate-fade-in text-xs">
              <span className="font-semibold text-gray-500 dark:text-zinc-400 shrink-0 font-mono">WS URL:</span>
              <input
                type="text"
                placeholder="ws://localhost:8000/ws/agent-stream"
                value={customWsUrl}
                onChange={(e) => setCustomWsUrl(e.target.value)}
                className="flex-1 bg-gray-50 dark:bg-zinc-800/80 px-2.5 py-1 rounded border border-gray-300 dark:border-zinc-700 text-gray-800 dark:text-zinc-100 font-mono focus:outline-none"
              />
              <button
                onClick={() => {
                  setCustomWsUrl("");
                  setUseCustomWs(false);
                }}
                className="text-gray-400 hover:text-zinc-600 dark:hover:text-zinc-300 font-semibold"
              >
                Reset
              </button>
            </div>
          )}

          {/* Core ReactFlow Graph canvas */}
          <TraceGraph nodesState={nodesState} />

          {/* Live Trace Telemetry Console underneath */}
          <div className="p-4 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-800 rounded-xl shadow-sm transition-all">
            <h4 className="text-xs font-bold text-gray-800 dark:text-zinc-200 mb-3 uppercase tracking-wider font-sans border-b border-gray-100 dark:border-zinc-800/80 pb-2 flex items-center justify-between">
              <span>Trace Realtime Metrics Console</span>
              <span className={`px-2 py-0.5 rounded text-[9px] font-mono tracking-wider font-bold ${
                traceStatus === "running"
                  ? "bg-amber-100 dark:bg-amber-950/50 text-amber-700 dark:text-amber-400 animate-pulse"
                  : traceStatus === "completed"
                  ? "bg-green-100 dark:bg-green-950/50 text-green-700 dark:text-green-400"
                  : "bg-gray-100 dark:bg-zinc-800 text-gray-500 dark:text-zinc-400"
              }`}>
                {traceStatus.toUpperCase()}
              </span>
            </h4>

            {activeNodeDetails ? (
              <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
                {/* Active node actions detail */}
                <div className="md:col-span-7 space-y-1">
                  <div className="text-[10px] text-teal-600 dark:text-teal-400 font-bold uppercase font-mono tracking-wider">
                    Executing Step: <span className="underline">{activeNodeDetails.nodeName}</span>
                  </div>
                  <p className="text-xs text-gray-700 dark:text-zinc-300 leading-relaxed font-medium">
                    {activeNodeDetails.action}
                  </p>
                </div>

                {/* Micro metrics tracking */}
                <div className="md:col-span-5 border-l border-gray-100 dark:border-zinc-800/80 pl-4 grid grid-cols-3 md:grid-cols-1 gap-2.5 font-mono text-[11px]">
                  <div className="flex md:items-center md:justify-between gap-1">
                    <span className="text-gray-400 dark:text-zinc-500 flex items-center gap-1"><Database className="h-3.5 w-3.5" /> Tokens:</span>
                    <strong className="text-gray-800 dark:text-zinc-200 font-bold">{accumulatedMetrics.tokens}t</strong>
                  </div>
                  <div className="flex md:items-center md:justify-between gap-1">
                    <span className="text-gray-400 dark:text-zinc-500 flex items-center gap-1"><Clock className="h-3.5 w-3.5" /> Latency:</span>
                    <strong className="text-gray-800 dark:text-zinc-200 font-bold">{accumulatedMetrics.latency}ms</strong>
                  </div>
                  <div className="flex md:items-center md:justify-between gap-1">
                    <span className="text-gray-400 dark:text-zinc-500 flex items-center gap-1"><Coins className="h-3.5 w-3.5" /> Total Cost:</span>
                    <strong className="text-teal-600 dark:text-teal-400 font-bold">${accumulatedMetrics.cost.toFixed(6)}</strong>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-6">
                <p className="text-xs text-gray-400 dark:text-zinc-500 font-mono">
                  Awaiting conversational query input to initialize trace sequence.
                </p>
              </div>
            )}
          </div>
        </section>

        </main>
      </div>

      {/* Ingestion and approvals modals */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        user={user}
        onUploadSuccess={() => {
          // Callback is run when user uploads file, can log or refresh
        }}
      />

      <AdminDashboardModal
        isOpen={isAdminOpen}
        onClose={() => setIsAdminOpen(false)}
        onActionTriggered={() => {
          // Callback is run when admin approves / rejects, can refresh lists
        }}
      />

    </div>
  );
}
