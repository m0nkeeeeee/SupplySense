const TONE_MAP = {
  critical: "bg-signal-rose/15 text-signal-rose ring-signal-rose/30",
  high: "bg-signal-rose/15 text-signal-rose ring-signal-rose/30",
  urgent: "bg-signal-rose/15 text-signal-rose ring-signal-rose/30",
  medium: "bg-signal-amber/15 text-signal-amber ring-signal-amber/30",
  low: "bg-signal-teal/15 text-signal-teal ring-signal-teal/30",
  delayed: "bg-signal-rose/15 text-signal-rose ring-signal-rose/30",
  customs_hold: "bg-signal-amber/15 text-signal-amber ring-signal-amber/30",
  in_transit: "bg-signal-teal/15 text-signal-teal ring-signal-teal/30",
  delivered: "bg-mist-400/15 text-mist-300 ring-mist-400/30",
  planned: "bg-ink-600/40 text-mist-300 ring-ink-500/40",
  cancelled: "bg-ink-600/40 text-mist-400 ring-ink-500/40",
};

export default function Badge({ tone = "low", children }) {
  const classes = TONE_MAP[tone] || TONE_MAP.low;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-mono font-medium uppercase tracking-wide ring-1 ${classes}`}
    >
      {children}
    </span>
  );
}
