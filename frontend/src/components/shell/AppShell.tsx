import type { ReactNode } from "react";
import { useRefresh } from "../../api/hooks";

/** A football used as a motif (header bullet / accents). */
export function Ball({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" className={className} aria-hidden fill="none">
      <circle cx="24" cy="24" r="22" fill="#f6f8f4" stroke="#0e2f17" strokeWidth="2" />
      <path
        d="M24 9l6 4.5-2.3 7H20.3L18 13.5 24 9zm0 0v6m-9 7l2.3 7-6 4.5M33 16l-2.3 7 6 4.5M15 33l9 6 9-6"
        stroke="#0e2f17" strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round"
      />
      <path d="M24 22.5l4 3-1.5 4.7h-5L20 25.5l4-3z" fill="#0e2f17" />
    </svg>
  );
}

/** Mowed-grass pitch with faint chalk lines — the app's football backdrop. */
export function PitchBackdrop() {
  return (
    <div aria-hidden className="fixed inset-0 -z-10 overflow-hidden">
      <div className="absolute inset-0 mowed" />
      {/* faint chalk pitch markings, sliced to fill */}
      <svg
        className="absolute inset-0 h-full w-full opacity-[0.12]"
        viewBox="0 0 100 64"
        preserveAspectRatio="xMidYMid slice"
        fill="none"
        stroke="#f6f8f4"
        strokeWidth="0.28"
      >
        <rect x="1" y="1" width="98" height="62" />
        <line x1="50" y1="1" x2="50" y2="63" />
        <circle cx="50" cy="32" r="9" />
        <circle cx="50" cy="32" r="0.7" fill="#f6f8f4" />
        {/* left box */}
        <rect x="1" y="16" width="14" height="32" />
        <rect x="1" y="25" width="5" height="14" />
        {/* right box */}
        <rect x="85" y="16" width="14" height="32" />
        <rect x="94" y="25" width="5" height="14" />
      </svg>
      {/* vignette so centre content reads */}
      <div className="absolute inset-0 bg-[radial-gradient(120%_90%_at_50%_30%,rgba(0,0,0,0)_55%,rgba(0,0,0,0.45))]" />
    </div>
  );
}

function SyncButton() {
  const refresh = useRefresh();
  return (
    <button
      onClick={() => refresh.mutate()}
      disabled={refresh.isPending}
      className="font-mono text-xs text-chalk-dim transition-colors hover:text-chalk disabled:opacity-50"
    >
      {refresh.isPending ? "Syncing…" : "Sync now"}
    </button>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="relative min-h-screen">
      <PitchBackdrop />
      <header className="flex items-center gap-3 border-b border-chalk/10 bg-grassdeep/40 px-6 py-4 backdrop-blur-sm">
        <img src="/emblem.webp" alt="WC 2026 emblem" className="h-10 w-10 object-contain drop-shadow" />
        <span className="font-display text-3xl tracking-wider text-chalk drop-shadow sm:text-4xl">
          WORLD CUP 2026
        </span>
        <span className="text-sm text-chalk-dim">· Watch Party Predictor</span>
        <div className="ml-auto">
          <SyncButton />
        </div>
      </header>
      <main className="px-6 py-6">{children}</main>
    </div>
  );
}
