import { useEffect, useMemo, useState } from "react";
import { Search } from "lucide-react";
import Topbar from "../components/Topbar.jsx";
import Panel from "../components/Panel.jsx";
import Badge from "../components/Badge.jsx";
import { listInventory } from "../api/client.js";

export default function Inventory() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    (async () => {
      try {
        const data = await listInventory({ limit: 300 });
        setItems(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const filtered = useMemo(() => {
    return items.filter((i) => {
      const matchesQuery =
        !query ||
        i.sku.toLowerCase().includes(query.toLowerCase()) ||
        i.name.toLowerCase().includes(query.toLowerCase());
      const status = statusOf(i);
      const matchesFilter = filter === "all" || status === filter;
      return matchesQuery && matchesFilter;
    });
  }, [items, query, filter]);

  return (
    <div className="flex flex-1 flex-col">
      <Topbar title="Inventory" subtitle={`${items.length} SKUs tracked across all warehouses`} />
      <div className="flex-1 overflow-y-auto p-6">
        <Panel
          eyebrow="Stock Levels"
          title="All SKUs"
          action={
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-mist-400" />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search SKU or name..."
                  className="rounded-lg border border-ink-700 bg-ink-900 py-1.5 pl-8 pr-3 text-xs text-mist-100 placeholder:text-mist-400 focus:border-signal-teal/50 focus:outline-none"
                />
              </div>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="rounded-lg border border-ink-700 bg-ink-900 px-2 py-1.5 text-xs text-mist-100 focus:border-signal-teal/50 focus:outline-none"
              >
                <option value="all">All</option>
                <option value="critical">Critical</option>
                <option value="low">Below reorder</option>
                <option value="ok">Healthy</option>
              </select>
            </div>
          }
        >
          {loading ? (
            <p className="text-sm text-mist-400">Loading inventory...</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-ink-700 font-mono text-[10px] uppercase tracking-widest text-mist-400">
                    <th className="py-2 pr-4">SKU</th>
                    <th className="py-2 pr-4">Name</th>
                    <th className="py-2 pr-4">Warehouse</th>
                    <th className="py-2 pr-4">On Hand</th>
                    <th className="py-2 pr-4">Reorder Pt</th>
                    <th className="py-2 pr-4">Safety Stock</th>
                    <th className="py-2 pr-4">Lead Time</th>
                    <th className="py-2 pr-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ink-700/60">
                  {filtered.map((i) => (
                    <tr key={i.sku} className="hover:bg-ink-700/20">
                      <td className="py-2.5 pr-4 font-mono text-mist-100">{i.sku}</td>
                      <td className="py-2.5 pr-4 text-mist-300">{i.name}</td>
                      <td className="py-2.5 pr-4 text-mist-400">{i.warehouse_id}</td>
                      <td className="py-2.5 pr-4 font-mono text-mist-100">{i.quantity_on_hand}</td>
                      <td className="py-2.5 pr-4 font-mono text-mist-400">{i.reorder_point}</td>
                      <td className="py-2.5 pr-4 font-mono text-mist-400">{i.safety_stock}</td>
                      <td className="py-2.5 pr-4 text-mist-400">{i.lead_time_days}d</td>
                      <td className="py-2.5 pr-4">
                        <Badge tone={badgeTone(statusOf(i))}>{statusOf(i)}</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filtered.length === 0 && (
                <p className="py-8 text-center text-sm text-mist-400">No matching SKUs.</p>
              )}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}

function statusOf(item) {
  if (item.quantity_on_hand <= item.safety_stock) return "critical";
  if (item.quantity_on_hand <= item.reorder_point) return "low";
  return "ok";
}

function badgeTone(status) {
  if (status === "critical") return "critical";
  if (status === "low") return "medium";
  return "low";
}
