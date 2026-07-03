import { motion, type Variants } from "motion/react";
import clsx from "clsx";
import { Ticket } from "lucide-react";
import type { BestBet } from "../../types";

const reveal: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: (i = 0) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.05, type: "spring" as const, stiffness: 140, damping: 18 },
  }),
};

const pct = (x: number) => `${Math.round(x * 100)}%`;

// Same accent logic as the value badges — totals neon, BTTS flood, 1X2 chalk.
function marketAccent(market: string): string {
  if (market.startsWith("1X2")) return "text-chalk";
  if (market.startsWith("Over")) return "text-neon";
  if (market.startsWith("BTTS")) return "text-flood";
  return "text-gold";
}

export function BestBets({ picks }: { picks: BestBet[] | undefined }) {
  return (
    <aside className="halo rounded-3xl border border-chalk/15 bg-card/85 p-6 backdrop-blur">
      <div className="flex items-center gap-2">
        <Ticket className="h-5 w-5 text-gold" />
        <h2 className="font-display text-2xl tracking-wide text-chalk">Best Bets</h2>
        <span className="font-mono text-[10px] uppercase tracking-widest text-chalk-dim">across all matches</span>
      </div>

      <div className="mt-4 space-y-3">
        {!picks || picks.length === 0 ? (
          <div className="rounded-2xl border border-chalk/10 bg-card/60 p-5 text-sm text-chalk-dim">
            No +EV picks right now — the model and the market agree. Check back closer to kickoff.
          </div>
        ) : (
          <ol className="space-y-2">
            {picks.map((b, i) => (
              <motion.li
                key={`${b.match_id}-${b.market}`}
                variants={reveal} custom={i} initial="hidden" animate="show"
                className="rounded-xl border border-chalk/10 bg-chalk/5 px-3 py-2.5"
              >
                <div className="flex items-center justify-between">
                  <span className={clsx("font-mono text-sm", marketAccent(b.market))}>{b.market}</span>
                  <span className="font-mono text-sm text-gold nums">@{b.odds}</span>
                </div>
                <div className="mt-0.5 flex items-center justify-between font-mono text-[11px] text-chalk-dim">
                  <span className="truncate">{b.home} v {b.away}</span>
                  <span className="nums shrink-0">
                    edge <span className="text-neon">+{pct(b.edge)}</span> · ¼-Kelly {(b.kelly * 100).toFixed(1)}%
                  </span>
                </div>
              </motion.li>
            ))}
          </ol>
        )}

        <div className="font-mono text-[10px] text-chalk-dim">
          paper-trade only · 90-min lines · ranked by model edge
        </div>
      </div>
    </aside>
  );
}
