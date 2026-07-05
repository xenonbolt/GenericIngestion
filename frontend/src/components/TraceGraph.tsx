import { useMemo, useEffect } from "react";
import ReactFlow, {
  Handle,
  Position,
  Node,
  Edge,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
} from "reactflow";
import "reactflow/dist/style.css";
import { TraceNode } from "../types";
import { Cpu, CheckCircle, Clock, Database, Coins } from "lucide-react";

interface TraceGraphProps {
  nodesState: TraceNode[];
}

// All nodes that always exist in the graph skeleton (greyed out by default)
const ALL_NODES: { id: string; label: string }[] = [
  { id: "query_translator",      label: "Query Translator" },
  { id: "intent_analyzer",       label: "Intent Analyzer" },
  { id: "graph_librarian",       label: "Graph Librarian Router" },
  { id: "data_analysis",         label: "Pandas Data Agent" },
  { id: "retrieval_synthesizer", label: "Vector Retrieval" },
  { id: "relevance_evaluator",   label: "Relevance Evaluator" },
  { id: "generator_agent",       label: "Final Response Generator" },
];

// Static layout — never changes, so the graph never re-fits/glitches
const nodeLayout: Record<string, { x: number; y: number }> = {
  "query_translator":      { x: 300, y: 20 },
  "intent_analyzer":       { x: 300, y: 140 },
  "graph_librarian":       { x: 300, y: 260 },
  "data_analysis":         { x: 80,  y: 400 },
  "retrieval_synthesizer": { x: 520, y: 400 },
  "relevance_evaluator":   { x: 300, y: 540 },
  "generator_agent":       { x: 300, y: 680 },
};

const staticEdges = [
  { source: "query_translator",      target: "intent_analyzer" },
  { source: "intent_analyzer",       target: "graph_librarian" },
  { source: "intent_analyzer",       target: "generator_agent" },
  { source: "graph_librarian",       target: "data_analysis" },
  { source: "graph_librarian",       target: "retrieval_synthesizer" },
  { source: "data_analysis",         target: "retrieval_synthesizer" },
  { source: "data_analysis",         target: "relevance_evaluator" },
  { source: "retrieval_synthesizer", target: "relevance_evaluator" },
  { source: "relevance_evaluator",   target: "retrieval_synthesizer" },
  { source: "relevance_evaluator",   target: "generator_agent" },
];

// Custom Node Component
const TraceNodeComponent = ({ data }: { data: any }) => {
  const { label, status, action, tokens, latency, cost } = data;

  const statusStyles = useMemo(() => {
    switch (status) {
      case "active":
        return {
          bg: "bg-teal-50 dark:bg-teal-950/40",
          border: "border-teal-500 shadow-teal-500/30 shadow-lg animate-pulse border-2",
          text: "text-teal-900 dark:text-teal-200",
          badge: "bg-teal-500 text-white animate-bounce",
          labelOpacity: "opacity-100",
        };
      case "completed":
        return {
          bg: "bg-white dark:bg-zinc-900",
          border: "border-green-500 dark:border-green-600 shadow-green-500/20 shadow-md",
          text: "text-zinc-800 dark:text-zinc-200",
          badge: "bg-green-500 text-white",
          labelOpacity: "opacity-100",
        };
      default: // idle — greyed out skeleton
        return {
          bg: "bg-zinc-50/60 dark:bg-zinc-900/30",
          border: "border-zinc-200 dark:border-zinc-800/60",
          text: "text-zinc-400 dark:text-zinc-600",
          badge: "bg-zinc-200 dark:bg-zinc-800 text-zinc-400 dark:text-zinc-600",
          labelOpacity: "opacity-50",
        };
    }
  }, [status]);

  return (
    <div
      className={`relative p-3.5 rounded-xl border text-xs text-left w-56 transition-all duration-500 ${statusStyles.bg} ${statusStyles.border}`}
    >
      <Handle type="target" position={Position.Top} className="!bg-zinc-400 dark:!bg-zinc-600 !opacity-40" />

      {/* Header */}
      <div className="flex items-center justify-between mb-1.5">
        <span className={`font-semibold font-sans tracking-tight text-[12px] ${statusStyles.text} ${statusStyles.labelOpacity}`}>
          {label}
        </span>
        <span
          className={`px-1.5 py-0.5 text-[9px] font-bold rounded uppercase tracking-wider ${statusStyles.badge}`}
        >
          {status}
        </span>
      </div>

      {/* Action / Description */}
      {action && status !== "idle" && (
        <p className="text-[10.5px] text-gray-600 dark:text-zinc-400 leading-normal mb-2 font-medium">
          {action}
        </p>
      )}

      {/* Metrics Footer (only when active/completed) */}
      {status !== "idle" && (
        <div className="pt-2 border-t border-gray-100 dark:border-zinc-800/80 grid grid-cols-3 gap-1 font-mono text-[9px]">
          <div className="flex flex-col">
            <span className="text-gray-400 dark:text-zinc-500">Tokens</span>
            <span className="font-semibold text-gray-700 dark:text-zinc-300 flex items-center gap-0.5 mt-0.5">
              <Database className="h-2.5 w-2.5 text-zinc-400" />
              {tokens || 0}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-gray-400 dark:text-zinc-500">Latency</span>
            <span className="font-semibold text-gray-700 dark:text-zinc-300 flex items-center gap-0.5 mt-0.5">
              <Clock className="h-2.5 w-2.5 text-zinc-400" />
              {latency ? `${latency}ms` : "0ms"}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="text-gray-400 dark:text-zinc-500">Cost</span>
            <span className="font-semibold text-gray-700 dark:text-zinc-300 flex items-center gap-0.5 mt-0.5">
              <Coins className="h-2.5 w-2.5 text-zinc-400" />
              ${cost ? cost.toFixed(6) : "0.00"}
            </span>
          </div>
        </div>
      )}

      <Handle type="source" position={Position.Bottom} className="!bg-zinc-400 dark:!bg-zinc-600 !opacity-40" />
    </div>
  );
};

const nodeTypes = { custom: TraceNodeComponent };

export default function TraceGraph({ nodesState }: TraceGraphProps) {
  // Build a live status map from the incoming prop
  const statusMap = useMemo(() => {
    const m = new Map<string, TraceNode>();
    nodesState.forEach(n => m.set(n.id, n));
    return m;
  }, [nodesState]);

  // Merge ALL_NODES skeleton with live status — no nodes ever disappear
  const flowNodes = useMemo<Node[]>(() => {
    return ALL_NODES.map((skeleton) => {
      const live = statusMap.get(skeleton.id);
      return {
        id: skeleton.id,
        type: "custom",
        position: nodeLayout[skeleton.id] || { x: 0, y: 0 },
        data: {
          label: skeleton.label,
          status: live?.status ?? "idle",
          action: live?.action,
          tokens: live?.tokens,
          latency: live?.latency,
          cost: live?.cost,
        },
        // Never let ReactFlow move nodes — prevents layout glitching
        draggable: false,
        selectable: false,
      };
    });
  }, [statusMap]);

  // Edges light up based on status
  const flowEdges = useMemo<Edge[]>(() => {
    return staticEdges.map((edge) => {
      const src = statusMap.get(edge.source);
      const tgt = statusMap.get(edge.target);

      const isAnimated = src?.status === "completed" && tgt?.status === "active";
      const isCompleted = src?.status === "completed" && tgt?.status === "completed";
      const isLive = isAnimated || isCompleted;

      // Suppress shortcut edge (intent -> generator) if the full pipeline was used
      let suppress = false;
      
      if (edge.source === "intent_analyzer" && edge.target === "generator_agent") {
        const librarian = statusMap.get("graph_librarian");
        if (librarian && librarian.status !== "idle") suppress = true;
      }
      
      // Suppress librarian -> vector if Pandas ran (because it routes through pandas first)
      if (edge.source === "graph_librarian" && edge.target === "retrieval_synthesizer") {
        const pandas = statusMap.get("data_analysis");
        if (pandas && pandas.status !== "idle") suppress = true;
      }
      
      // Suppress pandas -> relevance if Vector ran (because it routes through vector first)
      if (edge.source === "data_analysis" && edge.target === "relevance_evaluator") {
        const vector = statusMap.get("retrieval_synthesizer");
        if (vector && vector.status !== "idle") suppress = true;
      }

      return {
        id: `edge-${edge.source}-${edge.target}`,
        source: edge.source,
        target: edge.target,
        animated: !suppress && isAnimated,
        style: {
          stroke: suppress ? "#cbd5e1" : isCompleted ? "#22c55e" : isAnimated ? "#14b8a6" : "#cbd5e1",
          strokeWidth: isLive && !suppress ? 2.5 : 1,
          opacity: isLive && !suppress ? 1 : 0.2,
          transition: "stroke 0.4s ease, opacity 0.4s ease",
        },
      };
    });
  }, [statusMap]);

  // Use stable ReactFlow state — only update data, never re-initialize positions
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState(flowNodes);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState(flowEdges);

  useEffect(() => {
    setRfNodes(flowNodes);
  }, [flowNodes]);

  useEffect(() => {
    setRfEdges(flowEdges);
  }, [flowEdges]);

  return (
    <div className="w-full h-[640px] bg-gray-50 dark:bg-zinc-950/20 border border-gray-200 dark:border-zinc-800 rounded-xl overflow-hidden transition-all duration-300 relative">
      <div className="absolute top-3 left-4 z-10 bg-white/95 dark:bg-zinc-900/95 border border-gray-200/80 dark:border-zinc-800/80 px-3 py-1.5 rounded-lg shadow-sm">
        <h4 className="text-xs font-semibold text-gray-800 dark:text-zinc-200 flex items-center gap-1.5">
          <Cpu className="h-3.5 w-3.5 text-teal-500 animate-spin" style={{ animationDuration: "3s" }} />
          Orchestration Graph View
        </h4>
      </div>

      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.18 }}
        minZoom={0.4}
        maxZoom={1.5}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        className="text-zinc-900 dark:text-zinc-100"
      >
        <Background gap={16} size={1} color="#e4e4e7" className="dark:hidden" />
        <Background gap={16} size={1} color="#27272a" className="hidden dark:block" />
        <Controls showInteractive={false} className="dark:bg-zinc-900 dark:border-zinc-800 text-zinc-800 dark:text-zinc-200" />
      </ReactFlow>
    </div>
  );
}
