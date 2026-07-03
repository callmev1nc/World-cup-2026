import type { Config } from "tailwindcss";

// BROADCAST PITCH — mowed-grass + chalk-line football palette.
// (Replaces the old neon-lime-on-black "tech" look.)
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Pitch grass (body / large fields)
        pitch: "#2f7a35", // grass base
        surface: "#276628",
        grass: "#2f7a35",
        "grass-2": "#286c2e", // mowed stripe
        grassdeep: "#1f5326",
        // Panels (dark green glass so chalk text reads over grass)
        card: "#0e2f17",
        "card-2": "#175025",
        // Chalk (pitch lines / primary text)
        chalk: { DEFAULT: "#f6f8f4", dim: "#c2d3c2" },
        // Accents
        neon: "#a6ff7a", // bright pitch-light (WIN bar / favourite)
        lime: "#7cff9b",
        flood: "#ffd27a", // warm floodlight amber (value / highlight)
        gold: "#ffd43d",
        danger: "#ff6b6b", // LOSS
      },
      fontFamily: {
        display: ['"Bebas Neue"', "system-ui", "sans-serif"],
        sans: ['"Inter"', "system-ui", "sans-serif"],
        mono: ['"Geist Mono"', "ui-monospace", "monospace"],
      },
    },
  },
} satisfies Config;
