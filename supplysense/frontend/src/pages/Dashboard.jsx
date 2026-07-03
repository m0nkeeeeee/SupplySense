import { useEffect, useState } from "react";
import { PackageX, ShieldAlert, Ship, TrendingDown } from "lucide-react";
import Topbar from "../components/Topbar.jsx";
import Panel from "../components/Panel.jsx";
import Badge from "../components/Badge.jsx";
import { listInventory, listShipments, listRisks, listRecommendations } from "../api/client.js";

function StatCard({ label, value, icon: Icon, tone }) {
  const toneClasses = {
    teal: "text-signal-teal bg-signal-teal/10 ring-signal-teal/25",
    amber: "text-signal-amber bg-signal-amber/10 ring-signal-amber/25",
    rose: "text-signal-rose bg-signal-rose/10 ring-signal-rose/25",
  };
  return (
    <div className="rounded-xl border border-ink-700 bg-ink-800/60 p-5 shadow-panel animate-rise">
      <div className="flex items-center justify-between">
        <p className="font-mono text-[10px] uppercase tracking-widest text-mist-400">{label}</p>
        <div className={`rounded-md p-1.5 ring-1 ${toneClasses[tone]}`}>
          <Icon className="h-3.5 w-3.5" />
        </div>
      </div>
      <p className="mt-3 font-display text-3xl font-semibold text-mist-100">{value}</p>
    </div>
  );
}

export default function Dashboard() {
  const [inventory, setInventory] = useState([]);
  const [shipments, setShipments] = useState([]);
  const [risks, setRisks] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [inv, shp, rsk, rec] = await Promise.all([
          listInventory({ limit: 200 }),
          listShipments({ limit: 200 }),
          listRisks(10),
          listRecommendations(10),
        ]);
        setInventory(inv);
        setShipments(shp);
        setRisks(rsk);
        setRecommendations(rec);
      } catch (err) {
        console.error("Failed to load dashboard data", err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const critical = inventory.filter((i) => i.quantity_on_hand <= i.safety_stock);
  const delayed = shipments.filter((s) => s.status === "delayed" || s.status === "customs_hold");
  const highRisk = risks.filter((r) => r.severity === "high" || r.severity === "critical");

  return (
    <div className="flex flex-1 flex-col">
      <Topbar
        title="Control Tower"
        subtitle="Live cross-functional view of inventory, shipments, and risk"
      />
      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-grid bg-grid">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="SKUs Tracked" value={loading ? "—" : inventory.length} icon={PackageX} tone="teal" />
          <StatCard
            label="Critical Stock"
            value={loading ? "—" : critical.length}
            icon={TrendingDown}
            tone="rose"
          />
          <StatCard label="Shipments Delayed" value={loading ? "—" : delayed.length} icon={Ship} tone="amber" />
          <StatCard
            label="High Severity Risks"
            value={loading ? "—" : highRisk.length}
            icon={ShieldAlert}
            tone="rose"
          />
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Panel eyebrow="Inventory" title="SKUs at or below safety stock">
            {critical.length === 0 ? (
              <p className="text-sm text-mist-400">No critical stock shortages detected.</p>
            ) : (
              <ul className="divide-y divide-ink-700">
                {critical.slice(0, 8).map((item) => (
                  <li key={item.sku} className="flex items-center justify-between py-2.5 text-sm">
                    <div>
                      <p className="font-mono text-mist-100">{item.sku}</p>
                      <p className="text-mist-400 text-xs">{item.name}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-mono text-signal-rose">{item.quantity_on_hand} on hand</p>
                      <p className="text-xs text-mist-400">safety stock {item.safety_stock}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Panel>

          <Panel eyebrow="Logistics" title="Delayed or held shipments">
            {delayed.length === 0 ? (
              <p className="text-sm text-mist-400">No delayed shipments right now.</p>
            ) : (
              <ul className="divide-y divide-ink-700">
                {delayed.slice(0, 8).map((s) => (
                  <li key={s.shipment_id} className="flex items-center justify-between py-2.5 text-sm">
                    <div>
                      <p className="font-mono text-mist-100">{s.shipment_id}</p>
                      <p className="text-mist-400 text-xs">
                        {s.origin} → {s.destination}
                      </p>
                    </div>
                    <Badge tone={s.status}>{s.status.replace("_", " ")}</Badge>
                  </li>
                ))}
              </ul>
            )}
          </Panel>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Panel eyebrow="Risk Radar" title="Recently identified risks">
            {risks.length === 0 ? (
              <p className="text-sm text-mist-400">No risk events logged yet.</p>
            ) : (
              <ul className="space-y-3">
                {risks.slice(0, 5).map((r) => (
                  <li key={r.risk_id} className="rounded-lg border border-ink-700 bg-ink-900/40 p-3">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm font-medium text-mist-100">{r.title}</p>
                      <Badge tone={r.severity}>{r.severity}</Badge>
                    </div>
                    <p className="text-xs text-mist-400">{r.description}</p>
                  </li>
                ))}
              </ul>
            )}
          </Panel>

          <Panel eyebrow="Agent Insights" title="Latest recommendations">
            {recommendations.length === 0 ? (
              <p className="text-sm text-mist-400">
                Ask the Agent Network a question to generate recommendations.
              </p>
            ) : (
              <ul className="space-y-3">
                {recommendations.slice(0, 5).map((r) => (
                  <li key={r.recommendation_id} className="rounded-lg border border-ink-700 bg-ink-900/40 p-3">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm font-medium text-mist-100">{r.title}</p>
                      <Badge tone={r.priority}>{r.priority}</Badge>
                    </div>
                    <p className="text-xs text-mist-400">{r.rationale}</p>
                  </li>
                ))}
              </ul>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
