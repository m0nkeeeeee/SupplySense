import { useRef, useState } from "react";
import { Send, Sparkles, Loader2, Download } from "lucide-react";
import ReactMarkdown from "react-markdown";
import Topbar from "../components/Topbar.jsx";
import Panel from "../components/Panel.jsx";
import Badge from "../components/Badge.jsx";
import AgentPipeline from "../components/AgentPipeline.jsx";
import { sendChatMessage } from "../api/client.js";
import { generateConversationPdf } from "../utils/generatePdf.js";

const SUGGESTIONS = [
  "Show inventory shortages",
  "Track delayed shipments",
  "Predict supply chain risks",
  "Recommend supplier alternatives",
  "Generate executive report",
  "Search customs policy",
  "Warehouse stock summary",
  "Download PDF report",
];

export default function Copilot() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const scrollRef = useRef(null);

  const handleSend = async (text) => {
    const message = (text ?? input).trim();
    if (!message || loading) return;

    setMessages((prev) => [...prev, { role: "user", content: message }]);
    setInput("");
    setLoading(true);

    try {
      const result = await sendChatMessage(message, sessionId);
      setSessionId(result.session_id);
      setMessages((prev) => [...prev, { role: "assistant", ...result }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          answer:
            "I couldn't reach the agent backend. Confirm the API is running and your Bedrock / MongoDB credentials are configured.",
          plan: [],
          traces: [],
          recommendations: [],
          risk_events: [],
        },
      ]);
      console.error(err);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => {
        scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
      });
    }
  };

  return (
    <div className="flex flex-1 flex-col">
      <Topbar title="SupplySense Agent Network" subtitle="Ask a question — the Planner routes it across specialist agents" />
      <div className="px-6 pt-6">
  <div className="rounded-xl bg-gradient-to-r from-cyan-600 to-blue-700 p-6 mb-6">
    <h1 className="text-3xl font-bold text-white">
      SupplySense Agent Network
    </h1>

    <p className="mt-2 text-cyan-100">
      Powered by Amazon Bedrock • MongoDB Atlas • LangGraph • Voyage AI
    </p>
  </div>
</div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <div className="mx-auto max-w-2xl pt-10 text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-signal-teal/10 ring-1 ring-signal-teal/25">
              <Sparkles className="h-5 w-5 text-signal-teal" />
            </div>
            <h2 className="font-display text-xl font-semibold text-mist-100">
              What do you need visibility into?
            </h2>
            <p className="mt-2 text-sm text-mist-400">
              The Planner agent reads your question and dispatches Inventory, Shipment, Knowledge,
              Risk, and Recommendation agents as needed.
            </p>
            <div className="mt-6 grid grid-cols-1 gap-2 sm:grid-cols-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => handleSend(s)}
                  className="rounded-lg border border-ink-700 bg-ink-800/60 px-4 py-3 text-left text-sm text-mist-300 transition-colors hover:border-signal-teal/40 hover:text-mist-100"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-5">
            {messages.map((m, idx) =>
              m.role === "user" ? (
                <div key={idx} className="flex justify-end">
                  <div className="max-w-lg rounded-2xl rounded-br-sm bg-signal-teal/10 px-4 py-2.5 text-sm text-mist-100 ring-1 ring-signal-teal/25">
                    {m.content}
                  </div>
                </div>
              ) : (
                <div key={idx} className="space-y-3 animate-rise">
                  {m.plan?.length > 0 && (
                    <Panel className="!p-0" eyebrow="Agent Pipeline" title={null}>
                      <AgentPipeline plan={m.plan} traces={m.traces} />
                    </Panel>
                  )}

<div className="mb-2 flex items-center gap-2">

<span className="text-xl">⚙️</span>

<p className="font-semibold">
    Agent Network
</p>

</div>
                  <div className="rounded-2xl rounded-bl-sm border border-ink-700 bg-ink-800/60 px-5 py-4 shadow-panel">
                    <div className="prose prose-invert prose-sm max-w-none prose-headings:font-display prose-headings:text-mist-100 prose-p:text-mist-200 prose-strong:text-mist-100 prose-li:text-mist-200">
                      <ReactMarkdown>{m.answer}</ReactMarkdown>
                      <button

onClick={()=>navigator.clipboard.writeText(m.answer)}

className="mt-4 rounded-lg bg-signal-teal px-3 py-2 text-black text-sm"
>

Copy Answer

</button>
                    </div>
                  </div>

                  {m.traces?.length > 0 && (
                    <details className="rounded-lg border border-ink-700 bg-ink-900/40 px-4 py-2.5">
                      <summary className="cursor-pointer font-mono text-xs text-mist-400">
                        Agent trace ({m.traces.length} step{m.traces.length !== 1 ? "s" : ""})
                      </summary>
                      <ul className="mt-2 space-y-1.5">
                        {m.traces.map((t, i) => (
                          <li key={i} className="text-xs text-mist-400">
                            <span className="font-mono text-signal-teal">{t.agent}</span> — {t.output_summary}
                          </li>
                        ))}
                      </ul>
                    </details>
                  )}

                  {m.recommendations?.length > 0 && (
                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                      {m.recommendations.map((r) => (
                        <div
                          key={r.recommendation_id}
                          className="rounded-lg border border-ink-700 bg-ink-900/40 p-3"
                        >
                          <div className="flex items-center justify-between mb-1">
                            <p className="text-sm font-medium text-mist-100">{r.title}</p>
                            <Badge tone={r.priority}>{r.priority}</Badge>
                          </div>
                          <p className="text-xs text-mist-400">{r.rationale}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {m.risk_events?.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {m.risk_events.map((r) => (
                        <Badge key={r.risk_id} tone={r.severity}>
                          {r.title}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              )
            )}
            {loading && (
  <div className="rounded-xl border border-ink-700 bg-ink-800 p-4 animate-pulse">

    <p>🧠 Planner Agent analyzing request...</p>

    <p>📦 Inventory Agent checking stock...</p>

    <p>🚚 Shipment Agent tracking deliveries...</p>

    <p>⚠ Risk Agent evaluating risks...</p>

    <p>💡 Recommendation Agent generating insights...</p>

  </div>
)}
          </div>
        )}
      </div>
      <button
        onClick={() => generateConversationPdf(messages)}
        disabled={messages.length === 0}
        className="mx-6 mb-4 flex items-center gap-2 rounded-lg bg-signal-teal px-4 py-2 text-sm font-medium text-ink-950 transition-opacity hover:bg-signal-teal/90 disabled:opacity-40"
      >
        <Download className="h-4 w-4" />
        Download Report PDF
      </button>

      <div className="border-t border-ink-700 bg-ink-900/80 px-6 py-4 backdrop-blur-sm">
        <div className="mx-auto flex max-w-3xl items-center gap-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask about inventory, shipments, risk, or request a report..."
            className="flex-1 rounded-xl border border-ink-700 bg-ink-800 px-4 py-3 text-sm text-mist-100 placeholder:text-mist-400 focus:border-signal-teal/50 focus:outline-none"
          />
          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            className="flex h-11 w-11 items-center justify-center rounded-xl bg-signal-teal text-ink-950 transition-opacity disabled:opacity-40"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
