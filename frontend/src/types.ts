// Shared API/UI contract — mirrors backend/src/wcpredictor/schemas.py exactly.
// When you change one, change the other.

export type MatchState =
  | "predictable" // data available now -> full prediction shown
  | "scheduled" // teams known, kickoff upcoming
  | "waiting_result" // played, result not fetched yet -> pulsing card
  | "finished" // result in -> pred-vs-actual + Elo delta + CLV
  | "pending"; // matchup not set (e.g. R16 slot waiting on R32)

export type Settles = "90min" | "advance"; // bookmaker 1X2 = 90min; "to advance" = ET+pens

export interface ValueBet {
  market: string;
  model_prob: number; // 0..1
  odds: number; // decimal
  edge: number; // model_prob - devigged_implied (0..1)
  kelly: number; // quarter-Kelly stake fraction of bankroll
  settles: Settles;
}

export interface Prediction {
  match_id: string;
  round: string; // "R32" | "R16" | "QF" | "SF" | "Final"
  home: string;
  away: string;
  kickoff: string | null; // ISO-8601, e.g. "2026-07-03T18:00:00Z"
  state: MatchState;
  elo_home: number;
  elo_away: number;
  rank_home: number;
  rank_away: number;
  form_home: string[]; // ["W","W","D","L","W"]
  form_away: string[];
  win: number; // 90-min 1X2 (home win)  — win+draw+loss ~= 1
  draw: number;
  loss: number;
  predicted_score: string; // "2-1"
  score_top: [string, number][]; // [("2-1",.14), ...]
  ou: Record<string, { over: number; under: number }>; // {"2.5": {over,under}}
  btts_yes: number; // both teams to score
  double_chance: Record<string, number>; // {"1x","x2","12"}
  total_goals: Record<string, number>; // {"0-1","2-3","4-5","6+"}
  win_to_nil: Record<string, number>; // {"home","away"}
  corners_over_95: number | null; // secondary market (0..1)
  advance: { home: number; away: number } | null; // knockout "to qualify"
  pens: { score: string; winner: "home" | "away" } | null; // shootout guess for drawn knockouts
  team_stats: Record<string, Record<string, number>>;
  top_scorers_home: {name: string; goals: number}[];
  top_scorers_away: {name: string; goals: number}[];
  value_bets: ValueBet[];
  // only when state === "finished":
  actual_score: string | null;
  result: "home" | "draw" | "away" | null;
  clv: Record<string, number> | null;
}

export interface MatchSummary {
  match_id: string;
  round: string;
  home: string;
  away: string;
  kickoff: string | null;
  state: MatchState;
}

// One +EV pick from GET /best-bets — a ValueBet tagged with its match context.
export interface BestBet {
  match_id: string;
  home: string;
  away: string;
  round: string;
  market: string;
  model_prob: number;
  odds: number;
  edge: number;
  kelly: number;
  settles: Settles;
}
