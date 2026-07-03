import { motion } from "motion/react";

const reveal = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 120, damping: 18 } },
};

const waitPulse = {
  show: { opacity: [0.35, 1, 0.35], transition: { duration: 2.4, repeat: Infinity, ease: "easeInOut" as const } },
};

export function WaitingCard({ label, sub }: { label: string; sub: string }) {
  return (
    <motion.div
      variants={reveal} initial="hidden" animate="show"
      className="flex items-center gap-3 rounded-2xl border border-white/5 bg-card/40 p-5"
    >
      <motion.span variants={waitPulse} initial="hidden" animate="show" className="h-2.5 w-2.5 rounded-full bg-flood" />
      <div>
        <div className="font-display text-xl tracking-wide text-chalk-dim">{label}</div>
        <div className="font-mono text-xs text-chalk-dim">{sub}</div>
      </div>
    </motion.div>
  );
}
