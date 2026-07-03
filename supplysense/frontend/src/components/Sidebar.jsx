import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  MessagesSquare,
  PackageSearch,
  Ship,
  ShieldAlert,
  FileText,
  Bot,
  Cpu,
} from "lucide-react";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/copilot", label: "Agent Network", icon: MessagesSquare },
  { to: "/inventory", label: "Inventory", icon: PackageSearch },
  { to: "/shipments", label: "Shipments", icon: Ship },
  { to: "/risks", label: "Risk Radar", icon: ShieldAlert },
  { to: "/reports", label: "Reports", icon: FileText },
];

export default function Sidebar() {
  return (
    <aside className="hidden md:flex md:w-72 flex-col bg-slate-950 border-r border-slate-800">

      {/* Logo */}
      <div className="px-6 py-6 border-b border-slate-800">
        <div className="flex items-center gap-4">

          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-600">
            <Bot className="h-7 w-7 text-white" />
          </div>

          <div>
            <h1 className="text-lg font-bold text-white">
              SupplySense
            </h1>

            <p className="text-sm text-slate-400">
              Agent Network
            </p>
          </div>

        </div>
      </div>

      {/* AI Status */}
      <div className="mx-4 mt-5 rounded-xl bg-slate-900 p-4">

        <div className="flex items-center gap-2">

          <Cpu size={18} className="text-green-400" />

          <span className="font-semibold text-white">
            AI Status
          </span>

        </div>

        <p className="mt-2 text-sm text-slate-400">
          Planner • Inventory • Risk • Knowledge • Recommendation
        </p>

        <div className="mt-3 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs text-green-400">
            All Agents Active
          </span>
        </div>

      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">

        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-4 py-3 transition ${
                isActive
                  ? "bg-cyan-600 text-white shadow-lg"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              }`
            }
          >
            <Icon size={20} />
            <span>{label}</span>
          </NavLink>
        ))}

      </nav>

      {/* Footer */}
      <div className="border-t border-slate-800 p-5">

        <div className="rounded-xl bg-slate-900 p-4">

          <h3 className="text-sm font-semibold text-white">
            Tech Stack
          </h3>

          <ul className="mt-3 space-y-1 text-xs text-slate-400">
            <li>✓ MongoDB Atlas</li>
            <li>✓ Amazon Bedrock</li>
            <li>✓ LangGraph</li>
            <li>✓ Voyage AI</li>
            <li>✓ FastAPI</li>
            <li>✓ React + Vite</li>
          </ul>

        </div>

        <p className="mt-4 text-center text-xs text-slate-500">
          MongoDB & Accenture Agentic AI Hackathon 2026
        </p>

      </div>

    </aside>
  );
}
