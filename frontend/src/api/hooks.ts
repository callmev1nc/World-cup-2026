import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Prediction, MatchSummary, BestBet } from "../types";

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function fetcher<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`fetch ${path} failed: ${res.status}`);
  return res.json();
}

export function useMatches() {
  return useQuery<MatchSummary[]>({
    queryKey: ["matches"],
    queryFn: () => fetcher("/matches"),
    staleTime: 30_000,
  });
}

export function usePrediction(matchId: string | null) {
  return useQuery<Prediction>({
    queryKey: ["predict", matchId],
    queryFn: () => fetcher(`/predict/${matchId}`),
    enabled: !!matchId,
    refetchInterval: (query) => {
      const state = query.state.data?.state;
      if (state === "waiting_result") return 30_000;
      return false;
    },
    staleTime: 15_000,
  });
}

export function useRefresh() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => fetch(`${BASE}/refresh`, { method: "POST" }).then(r => r.json()),
    onSuccess: () => qc.invalidateQueries(),
  });
}

export function useBestBets() {
  return useQuery<BestBet[]>({
    queryKey: ["best-bets"],
    queryFn: () => fetcher("/best-bets"),
    staleTime: 30_000,
  });
}
