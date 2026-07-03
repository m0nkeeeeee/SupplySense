const AGENT_LABELS = {
  planner: "Planner",
  inventory: "Inventory",
  shipment: "Shipment",
  knowledge: "Knowledge",
  risk: "Risk",
  recommendation: "Recommendation",
  report: "Report",
};

export default function AgentPipeline({ plan = [], traces = [] }) {
  const executed = new Set(traces.map((t) => t.agent));
  const sequence = ["planner", ...plan];

  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-1">
      {sequence.map((agent, idx) => {
        const done = executed.has(agent);
        const isLast = idx === sequence.length - 1;
        return (
          <div key={`${agent}-${idx}`} className="flex items-center shrink-0">
            <div
              className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-mono font-medium ring-1 transition-all ${
                done
                  ? "bg-signal-teal/10 text-signal-teal ring-signal-teal/30"
                  : "bg-ink-700/50 text-mist-400 ring-ink-600"
              }`}
            >
              <span className={`h-1.5 w-1.5 rounded-full ${done ? "bg-signal-teal" : "bg-mist-400/50"}`} />
              {AGENT_LABELS[agent] || agent}
            </div>
            {!isLast && (
              <svg width="20" height="8" className="mx-0.5 shrink-0">
                <line
                  x1="0"
                  y1="4"
                  x2="20"
                  y2="4"
                  stroke={done ? "#2DD4BF" : "#27334A"}
                  strokeWidth="1.5"
                  strokeDasharray="3 3"
                  className={done ? "animate-flow" : ""}
                />
              </svg>
            )}
          </div>
        );
      })}
    </div>
  );
}
