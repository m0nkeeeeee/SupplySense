import { useEffect, useMemo, useState } from "react";
import Topbar from "../components/Topbar.jsx";
import Panel from "../components/Panel.jsx";
import Badge from "../components/Badge.jsx";
import { listShipments } from "../api/client.js";

const STATUS_OPTIONS = ["all", "planned", "in_transit", "delayed", "customs_hold", "delivered", "cancelled"];

export default function Shipments() {
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    (async () => {
      try {
        const data = await listShipments({ limit: 300 });
        setShipments(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const filtered = useMemo(
    () => (filter === "all" ? shipments : shipments.filter((s) => s.status === filter)),
    [shipments, filter]
  );

  return (
    <div className="flex flex-1 flex-col">
      <Topbar title="Shipments" subtitle={`${shipments.length} shipments tracked across all lanes`} />
      <div className="flex-1 overflow-y-auto p-6">
        <Panel
          eyebrow="Logistics"
          title="Shipment Tracking"
          action={
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="rounded-lg border border-ink-700 bg-ink-900 px-2 py-1.5 text-xs text-mist-100 focus:border-signal-teal/50 focus:outline-none"
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s.replace("_", " ")}
                </option>
              ))}
            </select>
          }
        >
          {loading ? (
            <p className="text-sm text-mist-400">Loading shipments...</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-ink-700 font-mono text-[10px] uppercase tracking-widest text-mist-400">
                    <th className="py-2 pr-4">Shipment</th>
                    <th className="py-2 pr-4">Route</th>
                    <th className="py-2 pr-4">Carrier</th>
                    <th className="py-2 pr-4">Mode</th>
                    <th className="py-2 pr-4">ETA</th>
                    <th className="py-2 pr-4">Delay</th>
                    <th className="py-2 pr-4">Risk Score</th>
                    <th className="py-2 pr-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-700/60">
                  {filtered.map((s) => (
                    <tr key={s.shipment_id} className="hover:bg-ink-700/20">
                      <td className="py-2.5 pr-4 font-mono text-mist-100">{s.shipment_id}</td>
                      <td className="py-2.5 pr-4 text-mist-300">
                        {s.origin} → {s.destination}
                      </td>
                      <td className="py-2.5 pr-4 text-mist-400">{s.carrier}</td>
                      <td className="py-2.5 pr-4 text-mist-400 uppercase">{s.mode}</td>
                      <td className="py-2.5 pr-4 font-mono text-mist-400">
                        {new Date(s.eta).toLocaleDateString()}
                      </td>
                      <td className="py-2.5 pr-4 font-mono text-mist-400">
                        {s.delay_days > 0 ? `+${s.delay_days}d` : "—"}
                      </td>
                      <td className="py-2.5 pr-4 font-mono text-mist-400">
                        {(s.risk_score * 100).toFixed(0)}%
                      </td>
                      <td className="py-2.5 pr-4">
                        <Badge tone={s.status}>{s.status.replace("_", " ")}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filtered.length === 0 && (
                <p className="py-8 text-center text-sm text-mist-400">No matching shipments.</p>
              )}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
