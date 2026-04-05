export function AegisCoreLogo() {
  return (
    <div className="flex items-center gap-3">
      <div className="grid h-11 w-11 place-items-center rounded-2xl border border-aegis-border bg-gradient-to-br from-aegis-orange to-aegis-orange-hover shadow-panel">
        <span className="text-sm font-black tracking-[0.24em] text-aegis-text">
          AC
        </span>
      </div>
      <div>
        <p className="text-xs uppercase tracking-[0.4em] text-aegis-muted">
          Security Operations
        </p>
        <h1 className="text-2xl font-semibold tracking-tight text-aegis-text">
          AegisCore
        </h1>
      </div>
    </div>
  );
}

