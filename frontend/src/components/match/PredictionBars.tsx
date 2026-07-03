import { motion } from "motion/react";
import clsx from "clsx";
import { useEffect, useState } from "react";
import { useMotionValue, animate } from "motion/react";

function useCountUp(target: number, duration = 1.1): number {
  const mv = useMotionValue(0);
  const [v, setV] = useState(0);
  const reduce = typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  useEffect(() => {
    if (reduce) { setV(target); return; }
    const controls = animate(mv, target, { duration, ease: "easeOut" as const, onUpdate: (x) => setV(x) });
    return () => controls.stop();
  }, [target, duration, reduce, mv]);
  return v;
}

const pct = (x: number) => `${Math.round(x * 100)}%`;

const barGrow = {
  hidden: { width: 0 },
  show: (w: number) => ({ width: `${Math.round(w * 100)}%`, transition: { type: "spring" as const, stiffness: 90, damping: 20 } }),
};

function BarRow({ label, value, color }: { label: string; value: number; color: string }) {
  const shown = useCountUp(value);
  return (
    <div className="flex items-center gap-3">
      <span className="w-12 font-mono text-[11px] text-chalk-dim">{label}</span>
      <div className="relative h-3 flex-1 overflow-hidden rounded-full bg-card-2">
        <motion.div custom={value} variants={barGrow} initial="hidden" animate="show" className={clsx("h-full rounded-full", color)} />
      </div>
      <span className="w-10 text-right font-mono text-sm nums text-chalk">{pct(shown)}</span>
    </div>
  );
}

export function PredictionBars({ win, draw, loss }: { win: number; draw: number; loss: number }) {
  const rows = [
    { label: "WIN", value: win, color: "bg-neon" },
    { label: "DRAW", value: draw, color: "bg-chalk-dim" },
    { label: "LOSS", value: loss, color: "bg-danger" },
  ];
  return (
    <div className="space-y-2.5">
      {rows.map((r) => (<BarRow key={r.label} {...r} />))}
    </div>
  );
}
