import { useState } from "react";
import { motion, type Variants } from "motion/react";
import clsx from "clsx";
import { Trophy, ChevronDown } from "lucide-react";
import type { Prediction } from "../../types";
import { PredictionBars } from "./PredictionBars";
import { Ball } from "../shell/AppShell";

/* ── motion vocab ── */
const reveal: Variants = {
  hidden: { opacity: 0, y: 24 },
  show: (i = 0) => ({
    opacity: 1, y: 0,
    transition: { delay: i * 0.07, type: "spring" as const, stiffness: 130, damping: 18 },
  }),
};
const flipIn: Variants = {
  hidden: { rotateX: -90, opacity: 0 },
  show: (i = 0) => ({
    rotateX: 0, opacity: 1,
    transition: { delay: 0.15 + i * 0.09, type: "spring" as const, stiffness: 200, damping: 18 },
  }),
};

/* ── team identity ── */
const ABBR: Record<string, string> = {
  spain: "ESP", austria: "AUT", portugal: "POR", croatia: "CRO", belgium: "BEL", senegal: "SEN",
  england: "ENG", "congo dr": "CGO", "dr congo": "CGO", usa: "USA", "united states": "USA",
  "bosnia & herzegovina": "BIH", france: "FRA", sweden: "SWE", "south africa": "RSA", canada: "CAN",
  "côte d'ivoire": "CIV", "cote d'ivoire": "CIV", "ivory coast": "CIV", norway: "NOR",
  brazil: "BRA", japan: "JPN", germany: "GER", paraguay: "PAR", netherlands: "NED",
  morocco: "MAR", mexico: "MEX", ecuador: "ECU", switzerland: "SUI", algeria: "ALG",
  australia: "AUS", egypt: "EGY", argentina: "ARG", "cape verde": "CPV", "cabo verde": "CPV",
  colombia: "COL", ghana: "GHA",
};
const COLORS: Record<string, string> = {
  ESP: "#C60B1E", AUT: "#ED2939", POR: "#006233", CRO: "#D01012", BEL: "#C8102E", SEN: "#00853F",
  ENG: "#CE1124", CGO: "#007FFF", USA: "#002868", BIH: "#002395", FRA: "#0055A4", SWE: "#006AA7",
  RSA: "#007749", CAN: "#D80621", CIV: "#FF8200", NOR: "#EF2B2D",
  BRA: "#FFCC00", JPN: "#012169", GER: "#DD0000", PAR: "#D52B1E", NED: "#FF6600",
  MAR: "#C1272D", MEX: "#006847", ECU: "#0033A0", SUI: "#DA291C", ALG: "#006233",
  AUS: "#FFCD00", EGY: "#C8102E", ARG: "#75AADB", CPV: "#0033A0", COL: "#FCD116", GHA: "#CE1126",
};
const abbr = (n: string) => ABBR[n.toLowerCase()] ?? n.slice(0, 3).toUpperCase();
const teamColor = (n: string) => COLORS[abbr(n)] ?? "#175025";

// ISO 3166 codes for flagcdn.com (England = gb-eng). Used for real flag images.
const FLAG: Record<string, string> = {
  ESP: "es", AUT: "at", POR: "pt", CRO: "hr", BEL: "be", SEN: "sn",
  ENG: "gb-eng", CGO: "cd", USA: "us", BIH: "ba", FRA: "fr", SWE: "se",
  RSA: "za", CAN: "ca", CIV: "ci", NOR: "no",
  BRA: "br", JPN: "jp", GER: "de", PAR: "py", NED: "nl", MAR: "ma", MEX: "mx",
  ECU: "ec", SUI: "ch", ALG: "dz", AUS: "au", EGY: "eg", ARG: "ar", CPV: "cv", COL: "co", GHA: "gh",
};

const pct = (x: number) => `${Math.round(x * 100)}%`;

const ROUND_LABEL: Record<string, string> = {
  R32: "Round of 32", R16: "Round of 16", QF: "Quarter-Final", SF: "Semi-Final", Final: "Final",
};
const roundLabel = (r: string) => ROUND_LABEL[r] ?? r;

// Market-type accent for value-bet badges: 1X2 chalk, totals neon, BTTS flood.
function marketAccent(market: string): string {
  if (market.startsWith("1X2")) return "text-chalk";
  if (market.startsWith("Over")) return "text-neon";
  if (market.startsWith("BTTS")) return "text-flood";
  return "text-gold";
}

function formatKickoff(iso: string | null): string {
  if (!iso) return "Kickoff TBC";
  return new Date(iso).toLocaleString(undefined, {
    weekday: "short", hour: "2-digit", minute: "2-digit", month: "short", day: "numeric",
  });
}

function FormPips({ form }: { form: string[] }) {
  const c = (r: string) => (r === "W" ? "bg-neon" : r === "D" ? "bg-chalk-dim" : "bg-danger");
  return (
    <div className="flex gap-1">
      {form.map((r, i) => (<span key={i} className={clsx("h-1.5 w-1.5 rounded-full", c(r))} />))}
    </div>
  );
}

function TeamBadge({ name }: { name: string }) {
  const a = abbr(name);
  const code = FLAG[a];
  const c = teamColor(name);
  const [broken, setBroken] = useState(false);
  return (
    <div
      className="flex h-14 w-20 items-center justify-center overflow-hidden rounded-xl"
      style={{ backgroundColor: `${c}33`, boxShadow: `inset 0 0 0 2px ${c}, 0 8px 20px -8px ${c}` }}
    >
      {code && !broken ? (
        <img
          src={`https://flagcdn.com/w160/${code}.png`}
          alt={`${name} flag`}
          onError={() => setBroken(true)}
          className="h-full w-full object-cover"
        />
      ) : (
        <span className="font-display text-2xl tracking-wide text-chalk">{a}</span>
      )}
    </div>
  );
}

function ScoreDigits({ score }: { score: string }) {
  const chars = score.split("");
  return (
    <div className="flex items-center gap-0.5" style={{ perspective: 600 }}>
      {chars.map((c, i) => (
        <motion.span
          key={i} custom={i} variants={flipIn} initial="hidden" animate="show"
          className="nums inline-block font-display text-6xl text-chalk sm:text-7xl"
          style={{ transformStyle: "preserve-3d", minWidth: c === "-" ? "0.35em" : "0.62em", textAlign: "center" }}
        >
          {c === "-" ? "–" : c}
        </motion.span>
      ))}
    </div>
  );
}

function ScorerList({ title, scorers }: { title: string; scorers?: {name: string; goals: number}[] }) {
  if (!scorers || scorers.length === 0) return null;
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-wider text-chalk-dim">{title} · recent internationals</div>
      {scorers.map((s, i) => (
        <div key={i} className="font-mono text-xs text-chalk">
          {s.name} <span className="text-chalk-dim">· {s.goals}</span>
        </div>
      ))}
    </div>
  );
}

function Chip({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="rounded-xl border border-chalk/10 bg-card-2/70 px-3 py-2 text-center">
      <div className="font-mono text-[10px] uppercase tracking-wider text-chalk-dim">{label}</div>
      <div className={clsx("font-mono text-sm nums", accent ?? "text-chalk")}>{value}</div>
    </div>
  );
}

function ValueBadge({ vb }: { vb: Prediction["value_bets"][number] }) {
  return (
    <motion.div variants={reveal} custom={3} initial="hidden" animate="show"
      className="flex items-center gap-2 rounded-xl border border-gold/30 bg-gold/5 px-3 py-2">
      <Trophy className="h-4 w-4 text-gold" />
      <div className="text-xs">
        <span className="font-mono text-gold">VALUE · <span className={marketAccent(vb.market)}>{vb.market}</span></span>
        <span className="ml-2 text-chalk-dim">
          @{vb.odds} · edge +{pct(vb.edge)} · ¼-Kelly {(vb.kelly * 100).toFixed(1)}%
        </span>
      </div>
    </motion.div>
  );
}

function MoreMarkets({ p }: { p: Prediction }) {
  const [open, setOpen] = useState(false);
  const ou15 = p.ou?.["1.5"];
  const ou35 = p.ou?.["3.5"];
  return (
    <div className="mt-4 rounded-2xl border border-chalk/10 bg-card-2/40">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-4 py-2.5 font-mono text-[11px] uppercase tracking-widest text-chalk-dim transition-colors hover:text-chalk"
      >
        <span>More markets</span>
        <ChevronDown className={clsx("h-4 w-4 transition-transform", open && "rotate-180")} />
      </button>
      <motion.div
        initial={false}
        animate={{ height: open ? "auto" : 0, opacity: open ? 1 : 0 }}
        transition={{ type: "spring" as const, stiffness: 200, damping: 26 }}
        className="overflow-hidden"
      >
        <div className="space-y-3 px-4 pb-4">
          <div>
            <div className="mb-1.5 font-mono text-[10px] uppercase tracking-wider text-chalk-dim">Correct Score</div>
            <div className="flex flex-wrap gap-1.5">
              {p.score_top.slice(0, 5).map(([s, prob]) => (
                <span key={s} className="rounded-lg bg-chalk/5 px-2 py-1 font-mono text-xs text-chalk">
                  {s} <span className="text-chalk-dim">{pct(prob)}</span>
                </span>
              ))}
            </div>
          </div>
          <div>
            <div className="mb-1.5 font-mono text-[10px] uppercase tracking-wider text-chalk-dim">Double Chance</div>
            <div className="grid grid-cols-3 gap-2">
              <Chip label="1X" value={pct(p.double_chance["1x"])} />
              <Chip label="X2" value={pct(p.double_chance["x2"])} />
              <Chip label="12" value={pct(p.double_chance["12"])} />
            </div>
          </div>
          <div>
            <div className="mb-1.5 font-mono text-[10px] uppercase tracking-wider text-chalk-dim">Total Goals</div>
            <div className="grid grid-cols-4 gap-2">
              <Chip label="0-1" value={pct(p.total_goals["0-1"])} />
              <Chip label="2-3" value={pct(p.total_goals["2-3"])} />
              <Chip label="4-5" value={pct(p.total_goals["4-5"])} />
              <Chip label="6+" value={pct(p.total_goals["6+"])} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {ou15 && <Chip label="Over 1.5" value={pct(ou15.over)} accent={ou15.over > 0.55 ? "text-neon" : "text-chalk"} />}
            {ou35 && <Chip label="Over 3.5" value={pct(ou35.over)} accent={ou35.over > 0.55 ? "text-neon" : "text-chalk"} />}
            <Chip label="Win to Nil H" value={pct(p.win_to_nil["home"])} accent="text-flood" />
            <Chip label="Win to Nil A" value={pct(p.win_to_nil["away"])} accent="text-flood" />
          </div>
        </div>
      </motion.div>
    </div>
  );
}

export function MarqueeMatch({ p }: { p: Prediction }) {
  const ou25 = p.ou?.["2.5"];
  const isFinished = p.state === "finished";
  const winnerName =
    p.result === "home" ? p.home : p.result === "away" ? p.away : null;
  const penWinner = p.pens?.winner === "home" ? p.home : p.pens?.winner === "away" ? p.away : null;
  const scoreShown = isFinished && p.actual_score ? p.actual_score : p.predicted_score;

  if (p.state === "pending") {
    return (
      <motion.section
        variants={reveal} initial="hidden" animate="show" custom={1}
        className="halo relative overflow-hidden rounded-3xl border border-chalk/15 bg-card/85 p-10 text-center backdrop-blur"
      >
        <Ball className="mx-auto h-8 w-8 opacity-70" />
        <div className="mt-4 font-display text-2xl tracking-wide text-chalk">{p.home}</div>
        <div className="my-1 font-mono text-[11px] uppercase tracking-widest text-chalk-dim">vs</div>
        <div className="font-display text-2xl tracking-wide text-chalk">{p.away}</div>
        <div className="mt-5 inline-flex items-center gap-2 rounded-full bg-flood/10 px-3 py-1 font-mono text-xs text-flood ring-1 ring-flood/30">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-flood" />
          {roundLabel(p.round)} · awaiting Round of 32 result
        </div>
      </motion.section>
    );
  }

  return (
    <motion.section
      variants={reveal} initial="hidden" animate="show" custom={1}
      className="halo relative overflow-hidden rounded-3xl border border-chalk/15 bg-card/85 p-6 backdrop-blur sm:p-8"
    >
      <div className="mb-6 flex items-center justify-between">
        <span className="inline-flex items-center gap-2 rounded-full bg-chalk/10 px-3 py-1 font-mono text-[11px] uppercase tracking-widest text-chalk ring-1 ring-chalk/15">
          <Ball className="h-3.5 w-3.5" /> {p.round} · {roundLabel(p.round)}
        </span>
        <span className="font-mono text-xs text-chalk-dim">{formatKickoff(p.kickoff)}</span>
      </div>

      {/* broadcast scorebug */}
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
        <div className="flex flex-col items-center gap-2">
          <TeamBadge name={p.home} />
          <span className="font-display text-2xl tracking-wide text-chalk">{p.home.toUpperCase()}</span>
          <span className="font-mono text-[11px] text-chalk-dim nums">POWER {p.elo_home}{p.rank_home ? ` · #${p.rank_home}` : ''}</span>
          <FormPips form={p.form_home} />
        </div>
        <div className="text-center">
          <div className="mb-1 font-mono text-[10px] uppercase tracking-widest text-chalk-dim">
            {isFinished ? "Full Time" : "Predicted"}
          </div>
          <div className="rounded-2xl bg-grassdeep/70 px-5 py-1 ring-1 ring-chalk/15">
            <ScoreDigits score={scoreShown} />
          </div>
        </div>
        <div className="flex flex-col items-center gap-2">
          <TeamBadge name={p.away} />
          <span className="font-display text-2xl tracking-wide text-chalk">{p.away.toUpperCase()}</span>
          <span className="font-mono text-[11px] text-chalk-dim nums">POWER {p.elo_away}{p.rank_away ? ` · #${p.rank_away}` : ''}</span>
          <FormPips form={p.form_away} />
        </div>
      </div>

      {/* finished result banner */}
      {isFinished && winnerName && (
        <div className="mt-5 rounded-xl bg-chalk/5 px-3 py-2 text-center font-mono text-xs text-chalk-dim">
          <span className="text-chalk">{winnerName}</span> advance ✓
          {p.actual_score ? ` · FT ${p.actual_score}` : ""}
          {p.pens && (
            <span className="text-flood"> · won {p.pens.score} on pens</span>
          )}
        </div>
      )}

      {/* 1X2 + markets (forecasts only) */}
      {!isFinished && (
        <>
          <div className="mt-6">
            <PredictionBars win={p.win} draw={p.draw} loss={p.loss} />
          </div>

          {p.team_stats?.home && (
            <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
              <Chip label="GF/g" value={p.team_stats.home.gfpg.toFixed(2)} />
              <Chip label="GA/g" value={p.team_stats.home.gapg.toFixed(2)} />
              <Chip label="Clean %" value={pct(p.team_stats.home.clean_sheet)} />
              <Chip label="BTTS No" value={pct(1 - p.team_stats.home.fail_score)} />
            </div>
          )}

          <div className="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
            <Chip label="BTTS" value={pct(p.btts_yes)} accent={p.btts_yes > 0.55 ? "text-neon" : "text-chalk"} />
            {ou25 && <Chip label="Over 2.5" value={pct(ou25.over)} accent={ou25.over > 0.55 ? "text-neon" : "text-chalk"} />}
            {p.corners_over_95 != null && <Chip label="Corners O9.5" value={pct(p.corners_over_95)} accent="text-flood" />}
            {p.advance && <Chip label="To Advance" value={`${abbr(p.home)} ${pct(p.advance.home)}`} accent="text-neon" />}
          </div>
          <MoreMarkets p={p} />

          {(p.top_scorers_home?.length || p.top_scorers_away?.length) ? (
            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <ScorerList title={p.home} scorers={p.top_scorers_home} />
              <ScorerList title={p.away} scorers={p.top_scorers_away} />
            </div>
          ) : null}
        </>
      )}

      {/* penalty-shootout guess — any level knockout after ET goes to pens */}
      {!isFinished && p.pens && penWinner && (
        <motion.div variants={reveal} custom={3} initial="hidden" animate="show"
          className="mt-4 flex items-center gap-2 rounded-xl border border-flood/30 bg-flood/5 px-3 py-2">
          <Ball className="h-4 w-4" />
          <span className="font-mono text-xs text-flood">
            IF DRAWN (AET) · {penWinner} win <span className="text-chalk">{p.pens.score}</span> on pens
            <span className="text-chalk-dim"> · illustrative ~50/50</span>
          </span>
        </motion.div>
      )}

      {/* value bets */}
      {!isFinished && p.value_bets.length > 0 && (
        <div className="mt-4 space-y-2">
          {p.value_bets.map((vb, i) => (<ValueBadge key={i} vb={vb} />))}
        </div>
      )}

      <div className="mt-4 font-mono text-[10px] text-chalk-dim">
        1X2 settles 90-min · paper-trade only · no real wager
      </div>
    </motion.section>
  );
}
