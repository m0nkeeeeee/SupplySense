import { useEffect, useState } from "react";
import { Download, FileText } from "lucide-react";
import Topbar from "../components/Topbar.jsx";
import Panel from "../components/Panel.jsx";
import { listReports, downloadReport } from "../api/client.js";

export default function Reports() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const data = await listReports(50);
        setReports(data);
        if (data.length > 0) setActive(data[0]);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="flex flex-1 flex-col">
      <Topbar title="Reports" subtitle="Compiled by the Report Agent on request" />
      <div className="flex-1 overflow-y-auto p-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <Panel eyebrow="Generated Reports" title="History" className="lg:col-span-1">
            {loading ? (
              <p className="text-sm text-mist-400">Loading reports...</p>
            ) : reports.length === 0 ? (
              <p className="text-sm text-mist-400">
                No reports yet. Ask SupplySense Agent Network: "Give me a full status report."
              </p>
            ) : (
              <ul className="space-y-1.5">
                {reports.map((r) => (
                  <li key={r.report_id}>
                    <button
                      onClick={() => setActive(r)}
                      className={`w-full rounded-lg px-3 py-2.5 text-left text-sm transition-colors ${
                        active?.report_id === r.report_id
                          ? "bg-signal-teal/10 text-signal-teal ring-1 ring-signal-teal/25"
                          : "text-mist-300 hover:bg-ink-700/40"
                      }`}
                    >
                      <p className="font-medium truncate">{r.title}</p>
                      <p className="text-xs text-mist-400">{new Date(r.created_at).toLocaleString()}</p>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </Panel>

          <Panel
            eyebrow="Report"
            title={active ? active.title : "Select a report"}
            className="lg:col-span-2"
            action={
              active && (
                <button
  onClick={() => downloadReport(active.report_id)}
  className="flex items-center gap-1.5 rounded-lg border border-ink-700 bg-ink-900 px-3 py-1.5 text-xs text-mist-200 hover:border-signal-teal/40 hover:text-signal-teal"
>
  <Download className="h-3.5 w-3.5" />
  Export PDF
</button>
              )
            }
          >
            {!active ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <FileText className="h-8 w-8 text-mist-400 mb-2" />
                <p className="text-sm text-mist-400">No report selected.</p>
              </div>
            ) : (
              <div className="space-y-5">
                <p className="text-sm text-mist-300">{active.summary}</p>
                {active.sections?.map((s, idx) => (
                  <div key={idx}>
                    <h3 className="font-display text-sm font-semibold text-mist-100 mb-1.5">{s.heading}</h3>
                    <p className="text-sm text-mist-400 whitespace-pre-line">{s.body}</p>
                  </div>
                ))}
              </div>
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
