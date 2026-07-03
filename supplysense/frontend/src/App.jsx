import { Routes, Route } from "react-router-dom";

import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";

import Dashboard from "./pages/Dashboard";
import Copilot from "./pages/Copilot";
import Inventory from "./pages/Inventory";
import Shipments from "./pages/Shipments";
import Risks from "./pages/Risks";
import Reports from "./pages/Reports";

export default function App() {
  return (
    <div className="flex h-screen bg-slate-950 text-white overflow-hidden">

      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">

        {/* Top Navigation */}
        <Topbar />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-slate-900 p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/copilot" element={<Copilot />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/shipments" element={<Shipments />} />
            <Route path="/risks" element={<Risks />} />
            <Route path="/reports" element={<Reports />} />
          </Routes>
        </main>

      </div>

    </div>
  );
}
