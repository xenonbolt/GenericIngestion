import { useState, useEffect } from "react";
import { User } from "./types";
import LoginScreen from "./components/LoginScreen";
import CustomerAnalysisPanel from "./components/CustomerAnalysisPanel";
import CustomerDelightTable from "./components/CustomerDelightTable";
import UploadModal from "./components/UploadModal";
import AdminDashboardModal from "./components/AdminDashboardModal";
import RiskManagerDashboard from "./components/RiskManagerDashboard";
import Sidebar from "./components/Sidebar";
import {
  Workflow,
  LogOut,
  Sun,
  Moon,
  UploadCloud,
  LayoutDashboard,
} from "lucide-react";

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [theme, setTheme] = useState<"light" | "dark">("dark");

  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isAdminOpen, setIsAdminOpen] = useState(false);

  const [customers, setCustomers] = useState<any[]>([]);
  const [customersLoading, setCustomersLoading] = useState(false);

  const [analysisData, setAnalysisData] = useState<any>(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

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

    const savedTheme = localStorage.getItem("agentic_theme") as "light" | "dark";
    if (savedTheme) setTheme(savedTheme);
  }, []);

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === "dark") root.classList.add("dark");
    else root.classList.remove("dark");
    localStorage.setItem("agentic_theme", theme);
  }, [theme]);

  // Fetch customers
  useEffect(() => {
    if (user) {
      fetchCustomers();
    }
  }, [user]);

  const fetchCustomers = async () => {
    setCustomersLoading(true);
    try {
      const response = await fetch(`/api/customers`);
      if (response.ok) {
        const data = await response.json();
        setCustomers(data.customers || []);
      }
    } catch (err) {
      console.error("Failed to fetch customers:", err);
    } finally {
      setCustomersLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("agentic_user");
    setUser(null);
    setAnalysisData(null);
  };

  const handleSendMessage = async (text: string) => {
    if (!user || chatLoading) return;
    setAnalysisData(null);
    setChatLoading(true);

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

      if (!response.ok) throw new Error("Analysis api request failed.");

      const data = await response.json();
      try {
        const parsedData = JSON.parse(data.reply);
        setAnalysisData(parsedData);
      } catch (parseError) {
        console.error("Failed to parse analysis data JSON:", data.reply);
      }
    } catch (err: any) {
      console.error("System Connection Halt:", err);
    } finally {
      setChatLoading(false);
    }
  };

  const handleResetView = () => {
    setAnalysisData(null);
    fetchCustomers(); // Refresh table data just in case
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
      <header className="px-6 py-4 border-b border-gray-200 dark:border-zinc-800/80 bg-white/95 dark:bg-zinc-900/95 backdrop-blur-md sticky top-0 z-40 transition-colors duration-300">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4">
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

          <div className="flex items-center gap-3">
            <button
              onClick={() => setTheme(theme === "light" ? "dark" : "light")}
              className="p-2 bg-gray-100 dark:bg-zinc-800 hover:bg-gray-200 dark:hover:bg-zinc-700 text-gray-600 dark:text-zinc-300 rounded-xl border border-gray-200 dark:border-zinc-700/80 transition-all cursor-pointer"
              title="Toggle Theme Mode"
            >
              {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
            </button>

            <button
              onClick={() => setIsUploadOpen(true)}
              className="px-4 py-2 bg-teal-500 hover:bg-teal-600 text-white text-xs font-semibold rounded-xl shadow-md shadow-teal-500/10 flex items-center gap-2 cursor-pointer transition-all"
            >
              <UploadCloud className="h-4 w-4" />
              Upload Knowledge
            </button>

            {user.role === "admin" && (
              <button
                onClick={() => setIsAdminOpen(true)}
                className="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white text-xs font-semibold rounded-xl shadow-md shadow-violet-500/10 flex items-center gap-2 cursor-pointer transition-all"
              >
                <LayoutDashboard className="h-4 w-4" />
                Admin Dashboard
              </button>
            )}

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

      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          user={user}
          isOpen={isSidebarOpen}
          onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
          customers={customers}
          onSelectCustomer={(customerId) => handleSendMessage(`ANALYZE_CUSTOMER: ${customerId}`)}
          onResetView={handleResetView}
        />
        <main className="flex-1 overflow-y-auto w-full p-6 grid grid-cols-1 gap-6 items-start">
          {user.role === "risk-manager" ? (
            <RiskManagerDashboard />
          ) : analysisData || chatLoading ? (
             <CustomerAnalysisPanel data={analysisData} loading={chatLoading} onBack={handleResetView} />
          ) : (
             <CustomerDelightTable customers={customers} loading={customersLoading} onSelectCustomer={(customerId) => handleSendMessage(`ANALYZE_CUSTOMER: ${customerId}`)} />
          )}
        </main>
      </div>

      <UploadModal isOpen={isUploadOpen} onClose={() => setIsUploadOpen(false)} user={user} onUploadSuccess={() => {}} />
      <AdminDashboardModal isOpen={isAdminOpen} onClose={() => setIsAdminOpen(false)} onActionTriggered={() => {}} />
    </div>
  );
}
