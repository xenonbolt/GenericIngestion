export interface User {
  username: string;
  role: "admin" | "basic";
  sessionId: string;
}

export interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  tracePending?: boolean;
  traceResult?: {
    tokens: number;
    latency: number;
    cost: number;
  };
}

export interface ApprovalItem {
  id: string;
  filename: string;
  submitter: string;
  timestamp: string;
  category: string;
  tags: string;
  summary: string;
  status: "pending" | "approved" | "rejected";
}

export interface AuditLog {
  id: string;
  timestamp: string;
  userId: string;
  action: string;
  details: string;
}

export interface TraceEvent {
  type: "connected" | "node_active" | "node_completed" | "trace_completed";
  nodeId?: string;
  nodeName?: string;
  action?: string;
  metrics?: {
    tokens: number;
    latency: number;
    cost: number;
  };
  totalTokens?: number;
  totalLatency?: number;
  totalCost?: number;
  timestamp?: string;
}

export interface TraceNode {
  id: string;
  label: string;
  status: "idle" | "active" | "completed";
  action?: string;
  tokens?: number;
  latency?: number;
  cost?: number;
}

export interface ChatSession {
  session_id: string;
  title: string;
  started_at: string | null;
  last_active: string | null;
  message_count: number;
}
