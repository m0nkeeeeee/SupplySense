import { useEffect, useState } from "react";
import { getHealth } from "../api/client";

export default function Topbar({ title, subtitle }) {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    let mounted = true;

    const poll = async () => {
      try {
        const data = await getHealth();
        if (mounted) setHealth(data);
      } catch {
        if (mounted) setHealth({ status: "offline" });
      }
    };

    poll();
    const interval = setInterval(poll, 30000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const statusColor =
    health?.status === "ok"
      ? "bg-green-500"
      : health?.status === "degraded"
      ? "bg-yellow-500"
      : "bg-red-500";

  return (
    <header className="flex items-center justify-between border-b border-gray-700 bg-gray-900 px-6 py-4">
      <div>
        <h1 className="text-xl font-bold text-white">{title}</h1>
        {subtitle && (
          <p className="text-sm text-gray-400 mt-1">{subtitle}</p>
        )}
      </div>

      <div className="flex items-center gap-2 rounded-full border border-gray-700 px-3 py-1">
        <span className={`h-2 w-2 rounded-full ${statusColor}`} />
        <span className="text-xs text-gray-300">
          {health ? health.status.toUpperCase() : "CONNECTING"}
        </span>
      </div>
    </header>
  );
}
