export default function Panel({ title, eyebrow, action, children, className = "" }) {
  return (
    <section className={`rounded-xl border border-ink-700 bg-ink-800/60 shadow-panel ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between border-b border-ink-700 px-5 py-3.5">
          <div>
            {eyebrow && (
              <p className="font-mono text-[10px] tracking-widest text-mist-400 uppercase">{eyebrow}</p>
            )}
            {title && <h2 className="font-display text-sm font-semibold text-mist-100">{title}</h2>}
          </div>
          {action}
        </div>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}
