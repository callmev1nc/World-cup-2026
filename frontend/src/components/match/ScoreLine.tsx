import { motion } from "motion/react";

const flipIn = {
  hidden: { rotateX: -90, opacity: 0 },
  show: (i = 0) => ({ rotateX: 0, opacity: 1, transition: { delay: 0.15 + i * 0.09, type: "spring" as const, stiffness: 200, damping: 18 } }),
};

export function ScoreLine({ score }: { score: string }) {
  const chars = score.split("");
  return (
    <div className="flex items-center justify-center gap-1" style={{ perspective: 600 }}>
      {chars.map((c, i) => (
        <motion.span
          key={i}
          custom={i}
          variants={flipIn}
          initial="hidden"
          animate="show"
          className="nums inline-block font-display text-6xl text-chalk sm:text-7xl"
          style={{ transformStyle: "preserve-3d", minWidth: c === "-" ? "0.35em" : "0.62em", textAlign: "center" }}
        >
          {c === "-" ? "\u2013" : c}
        </motion.span>
      ))}
    </div>
  );
}
