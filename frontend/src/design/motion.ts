import type { Variants } from "motion/react";

export const reveal: Variants = {
  hidden: { opacity: 0, y: 24 },
  show: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.06, type: "spring" as const, stiffness: 120, damping: 18 },
  }),
};

export const barGrow: Variants = {
  hidden: { width: 0 },
  show: (w: number) => ({
    width: `${w * 100}%`,
    transition: { type: "spring" as const, stiffness: 90, damping: 20 },
  }),
};

export const countUp = {
  initial: { scale: 0.8, opacity: 0 },
  animate: { scale: 1, opacity: 1, transition: { type: "spring" as const, stiffness: 200 } },
};
