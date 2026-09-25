import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import { Maximize2, X, ChevronRight } from "lucide-react";
import { getNifty100Performance } from "@/services/portfolioApi";

export interface AIPerformancePoint {
  month: string;
  ai: number;
}

// Added to match the Python backend output
export interface PendingReviewItem {
  ticker: string;
  target_weight: number;
  sentiment_score: number;
  headline_sample: string;
  link: string;
}

interface PerformanceAnalyticsProps {
  aiData?: AIPerformancePoint[];
  vetoMonths?: string[];
  sharpeRatio?: number;
  pendingReviewItems?: PendingReviewItem[]; // New prop
  onApplyDecisions?: (decisions: Record<string, "approve" | "veto">) => void; // New callback
}

interface ChartRow {
  month: string;
  ai: number;
  benchmark: number | null;
  drawdown: number;
}

export default function PerformanceAnalytics({
  aiData = [],
  vetoMonths = [],
  sharpeRatio,
  pendingReviewItems = [],
  onApplyDecisions,
}: PerformanceAnalyticsProps) {
  const [benchmarkData, setBenchmarkData] = useState<
    { month: string; benchmark: number }[] | null
  >(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  // Modal State
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const [decisions, setDecisions] = useState<
    Record<string, "approve" | "veto">
  >({});

  useEffect(() => {
    let cancelled = false;

    async function fetchBenchmark() {
      setIsLoading(true);
      setError(null);
      try {
        const monthFetch = aiData.length > 0 ? aiData.length : 12;
        const data = await getNifty100Performance(monthFetch);
        if (!cancelled) setBenchmarkData(data);
      } catch (err) {
        console.error("Failed to fetch Nifty 100 data:", err);
        if (!cancelled) setError("Couldn't load live Nifty 100 data.");
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    fetchBenchmark();
    return () => {
      cancelled = true;
    };
  }, [aiData]);

  const chartData: ChartRow[] = useMemo(() => {
    if (!benchmarkData) return [];
    let peak = -Infinity;
    return benchmarkData.map((bpoint) => {
      const aiPoint = aiData.find((a) => a.month === bpoint.month);
      let drawdownPct = 0;
      if (aiPoint && aiPoint.ai != null) {
        peak = Math.max(peak, aiPoint.ai);
        drawdownPct = peak > 0 ? ((peak - aiPoint.ai) / peak) * 100 : 0;
      }
      return {
        month: bpoint.month,
        ai: aiPoint ? aiPoint.ai : (null as any),
        benchmark: bpoint.benchmark,
        drawdown: Number(drawdownPct.toFixed(2)),
      };
    });
  }, [aiData, benchmarkData]);

  const stats = useMemo(() => {
    if (aiData.length === 0) {
      return { totalReturnPct: 0, maxDrawdownPct: 0, vetoCount: 0 };
    }
    const first = aiData[0]?.ai ?? 1;
    const last = aiData[aiData.length - 1]?.ai ?? first;
    const totalReturnPct = ((last - first) / first) * 100;
    const maxDrawdownPct = Math.max(0, ...chartData.map((d) => d.drawdown));
    return {
      totalReturnPct,
      maxDrawdownPct,
      vetoCount: vetoMonths.length,
    };
  }, [aiData, chartData, vetoMonths]);

  const pendingCount = pendingReviewItems.length;

  const handleDecide = (ticker: string, decision: "approve" | "veto") => {
    setDecisions((prev) => {
      const next = { ...prev, [ticker]: decision };
      onApplyDecisions?.(next);
      return next;
    });
  };
  const renderChartBody = (chartHeightClass: string) => (
    <>
      <div className="grid grid-cols-4 gap-3 mb-5">
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-2.5">
          <div className="text-xs text-slate-400 mb-1">Total return</div>
          <div
            className={`text-lg font-semibold ${
              stats.totalReturnPct >= 0 ? "text-emerald-400" : "text-red-400"
            }`}
          >
            {stats.totalReturnPct >= 0 ? "+" : ""}
            {stats.totalReturnPct.toFixed(1)}%
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-2.5">
          <div className="text-xs text-slate-400 mb-1">Sharpe ratio</div>
          <div className="text-lg font-semibold text-slate-100">
            {sharpeRatio != null ? sharpeRatio.toFixed(2) : "—"}
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-2.5">
          <div className="text-xs text-slate-400 mb-1">Historical loss</div>
          <div className="text-lg font-semibold text-red-400">
            −{stats.maxDrawdownPct.toFixed(1)}%
          </div>
        </div>

        {/* Updated Veto Interventions Tile */}
        <div
          onClick={() => {
            if (pendingCount > 0) setIsReviewModalOpen(true);
          }}
          className={`bg-slate-800/50 border rounded-lg px-3 py-2.5 transition-all ${
            pendingCount > 0
              ? "border-blue-500/40 hover:bg-slate-800 hover:border-blue-500/60 cursor-pointer"
              : "border-slate-700/50"
          }`}
        >
          <div className="text-xs text-slate-400 mb-1">Veto interventions</div>
          <div
            className={`text-lg font-semibold flex items-center gap-1 ${
              pendingCount > 0 ? "text-blue-400" : "text-slate-100"
            }`}
          >
            {pendingCount > 0 ? (
              <>
                {pendingCount} pending{" "}
                <ChevronRight size={18} className="mt-0.5" />
              </>
            ) : (
              stats.vetoCount
            )}
          </div>
        </div>
      </div>

      {/* Chart Loading / Error / Render Logic remains identical */}
      {isLoading ? (
        <div
          className={`${chartHeightClass} w-full flex flex-col items-center justify-center text-slate-400`}
        >
          <div className="w-10 h-10 border-4 border-slate-700 border-t-blue-500 rounded-full animate-spin mb-3"></div>
          <p className="animate-pulse text-sm">
            Fetching live Nifty 100 data...
          </p>
        </div>
      ) : error ? (
        <div
          className={`${chartHeightClass} w-full flex flex-col items-center justify-center text-slate-400 gap-2`}
        >
          <p className="text-red-400 text-sm">{error}</p>
          <p className="text-xs text-slate-500">
            Check that the backend is running and reachable.
          </p>
        </div>
      ) : (
        <div className={`${chartHeightClass} w-full`}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#334155"
                vertical={false}
              />
              <XAxis
                dataKey="month"
                stroke="#94a3b8"
                fontSize={10}
                tickLine={false}
                axisLine={false}
                interval="preserveStartEnd"
                height={30}
              />
              <YAxis
                yAxisId="growth"
                stroke="#94a3b8"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                domain={[0.9, 1.5]}
              />
              <YAxis yAxisId="drawdown" hide domain={[0, 40]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#0f172a",
                  borderColor: "#1e293b",
                  color: "#fff",
                }}
                formatter={(value: any, name: any) => {
                  if (name === "drawdown") return [`−${value}%`, "Drawdown"];
                  return [Number(value).toFixed(2), String(name)];
                }}
              />

              {vetoMonths.map((m) => (
                <ReferenceLine
                  key={m}
                  x={m}
                  yAxisId="growth"
                  stroke="#8B90AA"
                  strokeDasharray="2 3"
                  strokeOpacity={0.6}
                />
              ))}

              <Area
                yAxisId="drawdown"
                type="monotone"
                dataKey="drawdown"
                name="Historical loss"
                stroke="none"
                fill="#F76C6C"
                fillOpacity={0.18}
              />

              <Line
                yAxisId="growth"
                type="monotone"
                dataKey="benchmark"
                name="Buy & Hold (Nifty 100)"
                stroke="#f59e0b"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                connectNulls
              />
              <Line
                yAxisId="growth"
                type="monotone"
                dataKey="ai"
                name="AI Robo-Advisor"
                stroke="#3b82f6"
                strokeWidth={2.5}
                dot={{ r: 3 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="flex items-center gap-6 mt-4 text-sm text-slate-400">
        <span className="flex items-center gap-2">
          <span className="w-4 h-0.5 bg-blue-500 inline-block" />
          AI Robo-Advisor
        </span>
        <span className="flex items-center gap-2">
          <span
            className="w-4 h-0.5 inline-block"
            style={{ borderTop: "2px dashed #f59e0b" }}
          />
          Buy &amp; Hold (Nifty 100)
        </span>
        <span className="flex items-center gap-2">
          <span className="w-3 h-3 bg-red-400/70 inline-block rounded-sm" />
          Historical loss
        </span>
      </div>
    </>
  );

  return (
    <>
      <Card className="bg-slate-900 border-slate-800 shadow-xl flex flex-col">
        <CardHeader className="flex flex-row items-start justify-between space-y-0">
          <div>
            <CardTitle className="text-slate-200">
              Performance vs Benchmark
            </CardTitle>
            <p className="text-sm text-slate-400">
              AI Robo-Advisor vs Nifty 100 — last 12 months, risk-adjusted view
            </p>
          </div>
          <button
            onClick={() => setIsExpanded(true)}
            className="text-slate-400 hover:text-slate-200 transition-colors p-1.5 rounded-md hover:bg-slate-800"
            aria-label="Expand chart"
          >
            <Maximize2 size={18} />
          </button>
        </CardHeader>

        <CardContent className="flex-1 flex flex-col">
          {renderChartBody("h-[400px]")}
        </CardContent>
      </Card>

      {/* Fullscreen Chart Modal */}
      {isExpanded && (
        <div className="fixed inset-0 z-[50] bg-slate-950/95 flex items-center justify-center p-8">
          <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-6xl max-h-[92vh] flex flex-col p-6 relative">
            <button
              onClick={() => setIsExpanded(false)}
              className="absolute top-5 right-5 text-slate-400 hover:text-slate-200 transition-colors p-1.5 rounded-md hover:bg-slate-800"
            >
              <X size={22} />
            </button>
            <h2 className="text-xl font-semibold text-slate-200 mb-1">
              Performance vs Benchmark
            </h2>
            <p className="text-sm text-slate-400 mb-5">
              AI Robo-Advisor vs Nifty 100 — last 12 months, risk-adjusted view
            </p>
            {renderChartBody("h-[600px]")}
          </div>
        </div>
      )}

      {/* Veto Review Modal */}
      {isReviewModalOpen && (
        <div className="fixed inset-0 z-[60] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#171717] border border-[#2A2A2A] rounded-xl shadow-2xl w-full max-w-[460px] flex flex-col p-5 relative">
            <button
              onClick={() => setIsReviewModalOpen(false)}
              className="absolute top-5 right-5 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <X size={20} />
            </button>

            <h2 className="text-[17px] font-semibold text-slate-100 mb-1.5">
              Review flagged trades
            </h2>
            <p className="text-[13px] text-slate-400 mb-5 leading-relaxed pr-6">
              These trades breached the sentiment threshold. Approve to invest,
              or keep as cash.
            </p>

            <div className="flex flex-col gap-3 mb-6 max-h-[50vh] overflow-y-auto pr-1 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
              {pendingReviewItems.map((item) => {
                const currentDecision = decisions[item.ticker];

                return (
                  <div
                    key={item.ticker}
                    className="flex items-center justify-between p-3.5 rounded-lg border border-[#2A2A2A] bg-[#1E1E1E]"
                  >
                    <div>
                      <div className="font-semibold text-sm text-slate-100 mb-0.5">
                        {item.ticker}
                      </div>
                      <div className="text-[12px] text-slate-400">
                        Target {item.target_weight}%{" "}
                        <span className="text-red-400/90 ml-1">
                          Sentiment {item.sentiment_score}
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleDecide(item.ticker, "approve")}
                        className={`px-3 py-1.5 rounded-md text-[12px] font-medium border transition-colors ${
                          currentDecision === "approve"
                            ? "bg-green-950/40 border-green-500/40 text-green-400"
                            : "border-transparent text-green-500/70 hover:bg-[#2A2A2A]"
                        }`}
                      >
                        Approve
                      </button>
                      <button
                        onClick={() => handleDecide(item.ticker, "veto")}
                        className={`px-3 py-1.5 rounded-md text-[12px] font-medium border transition-colors ${
                          currentDecision === "veto"
                            ? "bg-red-950/40 border-red-500/40 text-red-400"
                            : "border-transparent text-red-500/70 hover:bg-[#2A2A2A]"
                        }`}
                      >
                        Keep cash
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
