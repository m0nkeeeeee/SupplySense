import { useEffect, useState } from "react";
import Topbar from "../components/Topbar.jsx";
import Panel from "../components/Panel.jsx";
import Badge from "../components/Badge.jsx";
import { listRisks } from "../api/client.js";

const CATEGORY_LABELS = {
  geopolitical: "Geopolitical",
  weather: "Weather",
  supplier: "Supplier",
  logistics: "Logistics",
  demand: "Demand",
};

export default function Risks() {
  const [risks, setRisks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const data = await listRisks(100);
        setRisks(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const grouped = risks.reduce((acc, r) => {
    acc[r.category] = acc[r.category] || [];
    acc[r.category].push(r);
    return acc;
  }, {});

  return (
    <div className="flex flex-1 flex-col">
      <Topbar title="Risk Radar" subtitle={`${risks.length} risk events logged by the Risk Agent`} />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {loading ? (
          <p className="text-sm text-mist-400">Loading risk events...</p>
        ) : risks.length === 0 ? (
          <Panel>
            <p className="text-sm text-mist-400">
              No risk events logged yet. Ask the Agent Network about supply chain risk to trigger the Risk Agent.
            </p>
          </Panel>
        ) : (
          Object.entries(grouped).map(([category, items]) => (
            <Panel key={category} eyebrow="Category" title={CATEGORY_LABELS[category] || category}>
              <ul className="space-y-3">
                {items.map((r) => (
                  <li
                    key={r.risk_id}
                    className="rounded-lg border border-ink-700 bg-ink-900/40 p-4 animate-rise"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <p className="text-sm font-medium text-mist-100">{r.title}</p>
                      <Badge tone={r.severity}>{r.severity}</Badge>
                    </div>
                    <p className="text-sm text-mist-400">{r.description}</p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {r.affected_skus?.map((sku) => (
                        <span key={sku} className="font-mono text-[10px] text-mist-400 bg-ink-800 rounded px-1.5 py-0.5">
                          {sku}
                        </span>
                      ))}
                      {r.affected_shipments?.map((id) => (
                        <span key={id} className="font-mono text-[10px] text-mist-400 bg-ink-800 rounded px-1.5 py-0.5">
                          {id}
                        </span>
                      ))}
                    </div>
                  </li>
                ))}
              </ul>
            </Panel>
          ))
        )}
      </div>
    </div>
  );
}
