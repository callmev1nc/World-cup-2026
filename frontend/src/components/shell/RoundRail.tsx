import clsx from "clsx";
import { Radio } from "lucide-react";

const ROUNDS: { id: string; label: string }[] = [
  { id: "R32", label: "R32" },
  { id: "R16", label: "R16" },
  { id: "QF", label: "QF" },
  { id: "SF", label: "SF" },
  { id: "Final", label: "Final" },
];

interface Props {
  selectedRound: string;
  onSelect: (id: string) => void;
  liveRounds: Set<string>;
}

export function RoundRail({ selectedRound, onSelect, liveRounds }: Props) {
  return (
    <nav className="mb-6 flex flex-wrap items-center gap-2">
      {ROUNDS.map((r) => {
        const live = liveRounds.has(r.id);
        const active = r.id === selectedRound;
        return (
          <button
            key={r.id}
            disabled={!live}
            onClick={() => onSelect(r.id)}
            className={clsx(
              "flex items-center gap-1.5 rounded-full border px-4 py-1.5 font-mono text-xs uppercase tracking-widest transition-colors",
              active
                ? "border-neon/60 bg-neon/15 text-neon"
                : live
                  ? "border-chalk/15 bg-card/40 text-chalk hover:border-neon/30 hover:text-neon"
                  : "cursor-not-allowed border-white/5 bg-card/20 text-chalk-dim/50",
            )}
          >
            {live && <Radio className="h-3 w-3" />}
            {r.label}
          </button>
        );
      })}
    </nav>
  );
}
