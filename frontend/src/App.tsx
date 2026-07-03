import { useState } from "react";
import clsx from "clsx";
import type { Prediction } from "./types";
import { AppShell } from "./components/shell/AppShell";
import { RoundRail } from "./components/shell/RoundRail";
import { MarqueeMatch } from "./components/match/MarqueeMatch";
import { BestBets } from "./components/match/BestBets";
import { useMatches, usePrediction, useBestBets } from "./api/hooks";

const FALLBACK: Prediction = {
  match_id: "spain-aut",
  round: "R32",
  home: "Spain",
  away: "Austria",
  kickoff: "2026-07-02T19:00:00Z",
  state: "predictable",
  elo_home: 2144,
  elo_away: 1698,
  rank_home: 2,
  rank_away: 22,
  form_home: ["W", "W", "D", "W", "W"],
  form_away: ["L", "W", "D", "L", "W"],
  win: 0.484,
  draw: 0.303,
  loss: 0.213,
  predicted_score: "2-1",
  score_top: [["2-1", 0.14], ["1-1", 0.13], ["2-0", 0.11], ["1-0", 0.09], ["3-1", 0.08]],
  ou: { "2.5": { over: 0.49, under: 0.51 } },
  btts_yes: 0.47,
  double_chance: { "1x": 0.787, x2: 0.516, "12": 0.697 },
  total_goals: { "0-1": 0.22, "2-3": 0.48, "4-5": 0.24, "6+": 0.06 },
  win_to_nil: { home: 0.18, away: 0.09 },
  corners_over_95: null,
  advance: { home: 0.67, away: 0.33 },
  pens: { score: "4-3", winner: "home" },
  team_stats: { home: {gfpg: 2.25, gapg: 0.75, clean_sheet: 0.417, fail_score: 0.25} },
  top_scorers_home: [{name: "Mikel Oyarzabal", goals: 13}],
  top_scorers_away: [{name: "Marko Arnautović", goals: 8}],
  value_bets: [
    { market: "Over/Under 2.5 Under", model_prob: 0.51, odds: 2.3, edge: 0.07, kelly: 0.02, settles: "90min" },
  ],
  actual_score: null,
  result: null,
  clv: null,
};

const ROUND_HEADER: Record<string, string> = {
  R32: "Round of 32", R16: "Round of 16", QF: "Quarter-Finals", SF: "Semi-Finals", Final: "Final",
};

const STATE_LABEL: Record<string, string> = {
  predictable: "Forecast", scheduled: "Scheduled", waiting_result: "Waiting", finished: "FT", pending: "TBD",
};

export default function App() {
  const [selectedId, setSelectedId] = useState<string>("spain-aut");
  const [selectedRound, setSelectedRound] = useState<string>("R32");
  const { data: matches } = useMatches();
  const { data: prediction } = usePrediction(selectedId);
  const { data: bestBets } = useBestBets();

  const activePrediction = prediction ?? FALLBACK;

  const liveRounds = new Set((matches ?? []).map((m) => m.round));
  const effectiveRound = liveRounds.has(selectedRound) ? selectedRound : "R32";
  const roundMatches = (matches ?? []).filter((m) => m.round === effectiveRound);

  return (
    <AppShell>
      <RoundRail selectedRound={effectiveRound} onSelect={setSelectedRound} liveRounds={liveRounds} />

      <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        <div className="space-y-6">
          <MarqueeMatch p={activePrediction} />

          <div className="space-y-3">
            <h2 className="font-display text-2xl tracking-wide text-chalk-dim">
              {ROUND_HEADER[effectiveRound] ?? effectiveRound}
              <span className="ml-3 font-mono text-xs text-chalk-dim/70 nums">{roundMatches.length} matches</span>
            </h2>

            <div className="max-h-[68vh] space-y-2 overflow-y-auto pr-1">
              {roundMatches.map((m) => {
                const active = m.match_id === selectedId;
                return (
                  <button
                    key={m.match_id}
                    onClick={() => setSelectedId(m.match_id)}
                    className={clsx(
                      "w-full rounded-xl border p-4 text-left transition-colors",
                      active
                        ? "border-neon/40 bg-card ring-1 ring-neon/30"
                        : "border-white/5 bg-card/60 hover:border-neon/20 hover:bg-card",
                    )}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="truncate font-display text-lg tracking-wide text-chalk">
                        {m.home} <span className="text-chalk-dim">v</span> {m.away}
                      </span>
                      <span
                        className={clsx(
                          "shrink-0 rounded-full px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider",
                          m.state === "finished" && "bg-chalk/10 text-chalk",
                          m.state === "predictable" && "bg-neon/10 text-neon",
                          m.state === "pending" && "bg-flood/10 text-flood",
                          (m.state === "scheduled" || m.state === "waiting_result") && "bg-chalk/5 text-chalk-dim",
                        )}
                      >
                        {STATE_LABEL[m.state] ?? m.state}
                      </span>
                    </div>
                  </button>
                );
              })}

              {roundMatches.length === 0 && (
                <div className="rounded-xl border border-white/5 bg-card/40 p-4 text-sm text-chalk-dim">
                  No matches in this round yet.
                </div>
              )}
            </div>
          </div>
        </div>

        <BestBets picks={bestBets} />
      </div>
    </AppShell>
  );
}
