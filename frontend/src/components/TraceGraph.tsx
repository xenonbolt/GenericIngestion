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

// Custom Node Component to display rich enterprise-grade details
const TraceNodeComponent = ({ data }: { data: any }) => {
  const { label, status, action, tokens, latency, cost } = data;

  const statusStyles = useMemo(() => {
    switch (status) {
      case "active":
        return {
          bg: "bg-teal-50 dark:bg-teal-950/40",
          border: "border-teal-500 shadow-teal-500/20 animate-pulse border-2",
          text: "text-teal-900 dark:text-teal-200",
          badge: "bg-teal-500 text-white animate-bounce",
          icon: "text-teal-500",
        };
      case "completed":
        return {
          bg: "bg-white dark:bg-zinc-900",
          border: "border-green-500 dark:border-green-600 shadow-green-500/10",
          text: "text-zinc-800 dark:text-zinc-200",
          badge: "bg-green-500 text-white",
          icon: "text-green-500",
        };
      default:
        return {
          bg: "bg-gray-50/50 dark:bg-zinc-900/40",
          border: "border-gray-200 dark:border-zinc-800/80",
          text: "text-gray-400 dark:text-zinc-600",
          badge: "bg-gray-200 dark:bg-zinc-800 text-gray-400 dark:text-zinc-500",
          icon: "text-gray-300 dark:text-zinc-700",
        };
    }
  }, [status]);

  return (
    <div
      className={`relative p-3.5 rounded-xl border text-xs text-left w-64 shadow-md transition-all duration-300 ${statusStyles.bg} ${statusStyles.border}`}
    >
      <Handle type="target" position={Position.Top} className="!bg-zinc-400 dark:!bg-zinc-600" />

      {/* Header */}
      <div className="flex items-center justify-between mb-1.5">
        <span className={`font-semibold font-sans tracking-tight text-[13px] ${statusStyles.text}`}>
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

      {/* Metrics Footer (Only when active/completed) */}
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

      <Handle type="source" position={Position.Bottom} className="!bg-zinc-400 dark:!bg-zinc-600" />
    </div>
  );
};

// Map node types
const nodeTypes = {
  custom: TraceNodeComponent,
};

const nodeLayout: Record<string, { x: number; y: number }> = {
  "query_translator": { x: 250, y: 20 },
  "intent_analyzer": { x: 250, y: 150 },
  "task_decomposer": { x: 100, y: 300 },
  "data_analysis": { x: 400, y: 300 },
  "networkx_qa": { x: -50, y: 450 },
  "kuzu_qa": { x: 250, y: 450 },
  "graph_judge": { x: 100, y: 600 },
  "retrieval_synthesizer": { x: 100, y: 750 },
  "relevance_evaluator": { x: 100, y: 900 },
  "generator_agent": { x: 250, y: 1050 }
};

const staticEdges = [
  { source: "query_translator", target: "intent_analyzer" },
  { source: "intent_analyzer", target: "task_decomposer" },
  { source: "intent_analyzer", target: "data_analysis" },
  { source: "intent_analyzer", target: "networkx_qa" },
  { source: "intent_analyzer", target: "generator_agent" },
  { source: "task_decomposer", target: "retrieval_synthesizer" },
  { source: "retrieval_synthesizer", target: "relevance_evaluator" },
  { source: "relevance_evaluator", target: "retrieval_synthesizer" },
  { source: "relevance_evaluator", target: "generator_agent" },
  { source: "networkx_qa", target: "kuzu_qa" },
  { source: "kuzu_qa", target: "graph_judge" },
  { source: "graph_judge", target: "generator_agent" },
  { source: "data_analysis", target: "generator_agent" },
];

export default function TraceGraph({ nodesState }: TraceGraphProps) {
  // Convert standard TraceNode[] state to ReactFlow Node[]
  const flowNodes = useMemo<Node[]>(() => {
    return nodesState.map((node) => ({
      id: node.id,
      type: "custom",
      position: nodeLayout[node.id] || { x: 30, y: 0 },
      data: {
        label: node.label,
        status: node.status,
        action: node.action,
        tokens: node.tokens,
        latency: node.latency,
        cost: node.cost,
      },
      draggable: false,
    }));
  }, [nodesState]);

  // Create Edges
  const flowEdges = useMemo<Edge[]>(() => {
    const nodesMap = new Map(nodesState.map(n => [n.id, n]));
    
    return staticEdges.map((edge) => {
      const sourceNode = nodesMap.get(edge.source);
      const targetNode = nodesMap.get(edge.target);
      
      const isAnimated = sourceNode?.status === "completed" && targetNode?.status === "active";
      const isCompleted = sourceNode?.status === "completed" && targetNode?.status === "completed";
      
      return {
        id: `edge-${edge.source}-${edge.target}`,
        source: edge.source,
        target: edge.target,
        animated: isAnimated,
        style: {
          stroke: isCompleted ? "#22c55e" : isAnimated ? "#14b8a6" : "#cbd5e1",
          strokeWidth: isCompleted || isAnimated ? 2.5 : 1.5,
          opacity: isCompleted || isAnimated ? 1 : 0.35,
        },
      };
    });
  }, [nodesState]);

  return (
    <div className="w-full h-[620px] bg-gray-50 dark:bg-zinc-950/20 border border-gray-200 dark:border-zinc-800 rounded-xl overflow-hidden transition-all duration-300 relative">
      <div className="absolute top-3 left-4 z-10 bg-white/95 dark:bg-zinc-900/95 border border-gray-200/80 dark:border-zinc-800/80 px-3 py-1.5 rounded-lg shadow-sm">
        <h4 className="text-xs font-semibold text-gray-800 dark:text-zinc-200 flex items-center gap-1.5">
          <Cpu className="h-3.5 w-3.5 text-teal-500 animate-spin" style={{ animationDuration: "3s" }} />
          Orchestration Graph View
        </h4>
      </div>

      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        minZoom={0.5}
        maxZoom={1.5}
        className="text-zinc-900 dark:text-zinc-100"
      >
        <Background gap={16} size={1} color="#e4e4e7" className="dark:hidden" />
        <Background gap={16} size={1} color="#27272a" className="hidden dark:block" />
        <Controls showInteractive={false} className="dark:bg-zinc-900 dark:border-zinc-800 text-zinc-800 dark:text-zinc-200" />
      </ReactFlow>
    </div>
  );
}
