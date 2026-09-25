import axios from "axios";
import type { SentimentNewsItem } from "@/components/Newsfeed";

const API_BASE_URL = "http://localhost:5000";

function authHeaders() {
  const token = localStorage.getItem("token");
  return {
    Authorization: `Bearer ${token}`,
  };
}

export interface AIPerformancePoint {
  month: string;
  ai: number;
}

export interface PortfolioSlice {
  name: string;
  value: number;
}

export interface PendingReviewItem {
  ticker: string;
  target_weight: number;
  sentiment_score: number;
  headline_sample: string;
  link: string;
}

export type { SentimentNewsItem };

export const runAIEngineAPI = async () => {
  const response = await axios.post(
    `${API_BASE_URL}/api/portfolio/run-ai`,
    {},
    { headers: authHeaders() },
  );
  const aiData = response.data.data;

  console.log("RAW AI DATA PAYLOAD:", aiData);

  const formattedPortfolio: PortfolioSlice[] = Object.keys(
    aiData.active_allocations || {},
  ).map((ticker) => ({
    name: ticker,
    value: aiData.active_allocations[ticker],
  }));

  const cashReservePercent: number = aiData.cash_reserve ?? 0;

   const pendingReview: PendingReviewItem[] = (aiData.pending_review || []).map(
    (item: any) => ({
      ticker: item.ticker,
      target_weight: item.target_weight,
      sentiment_score: item.sentiment_score,
      headline_sample: item.headline_sample,
      link: item.link,
    }),
  );

  const entryDate = aiData.date ? new Date(aiData.date) : new Date();

  const formattedNews: SentimentNewsItem[] = (aiData.sentiment_log || []).map(
    (trade: any) => {
      const rawLink = trade.link;
      const url = rawLink && rawLink !== "#" ? rawLink : undefined;

      return {
        headline: trade.headline_sample,
        tag: trade.sentiment_score >= 0 ? "Pos" : "Neg",
        score: trade.sentiment_score,
        url,
        time: entryDate.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };
    },
  );

  const formattedPerformance: AIPerformancePoint[] = (
    aiData.performance_history || []
  ).map((point: any) => ({
    month: point.month,
    ai: point.ai ?? point.value ?? 1.0,
  }));
  const sharpeRatio: number | null = aiData.sharpe_ratio ?? null;

  return {
    formattedNews,
    formattedPortfolio,
    formattedPerformance,
    sharpeRatio,
    cashReservePercent,
    pendingReview,
  };
};

export interface Nifty100BenchmarkPoint {
  month: string;
  benchmark: number;
}

export async function getNifty100Performance(
  months: number = 12,
): Promise<Nifty100BenchmarkPoint[]> {
  const response = await axios.get(`${API_BASE_URL}/api/nifty100-performance`, {
    params: { months },
    headers: authHeaders(),
  });
  return response.data;
}
