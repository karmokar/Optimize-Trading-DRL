import { useState, useEffect, useRef, useMemo } from "react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Calendar, Bell, LayoutDashboard, Wallet } from "lucide-react";
import { runAIEngineAPI } from "@/services/portfolioApi";
import type { PendingReviewItem } from "@/services/portfolioApi";

import PortfolioAllocation from "@/components/PortfolioAllocation";
import type { PortfolioSlice } from "@/components/PortfolioAllocation";

// 1. Updated these imports to match the new Nifty 100 setup
import PerformanceAnalytics from "@/components/PerformanceAnalytics";
import type { AIPerformancePoint } from "@/components/PerformanceAnalytics";

import NewsFeed from "@/components/Newsfeed";
import type { SentimentNewsItem } from "@/components/Newsfeed";

function formatINR(amount: number): string {
  return `₹${Math.round(amount).toLocaleString("en-IN")}`;
}

export default function Dashboard() {
  const [portfolioData, setPortfolioData] = useState<PortfolioSlice[]>([
    { name: "Awaiting AI Output", value: 100 },
  ]);

  // 2. Updated state variables to use the AI data types
  const [aiData, setAiData] = useState<AIPerformancePoint[]>([]);

  const [sentimentNews, setSentimentNews] = useState<SentimentNewsItem[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [sharpeRatio, setSharpeRatio] = useState<number | null>(null);

  // Cash held back by the sentiment veto system (not invested in any stock).
  const [cashReservePercent, setCashReservePercent] = useState<number>(0);

  // Lifted up from PortfolioAllocation so the wallet badge can show ₹ too.
  const [investmentAmount, setInvestmentAmount] = useState<number>(1000000);

  const [showWalletPopup, setShowWalletPopup] = useState(false);
  const walletRef = useRef<HTMLDivElement>(null);

  const [pendingReview, setPendingReview] = useState<PendingReviewItem[]>([]);
  const [appliedDecisions, setAppliedDecisions] = useState<
    Record<string, "approve" | "veto">
  >({});

  const handleRunAI = async () => {
    setIsGenerating(true);
    try {
      const {
        formattedPortfolio,
        formattedNews,
        formattedPerformance,
        sharpeRatio,
        cashReservePercent,
        pendingReview,
      } = await runAIEngineAPI();
      setPortfolioData(formattedPortfolio);
      setSentimentNews(formattedNews);
      setAiData(formattedPerformance);
      setSharpeRatio(sharpeRatio);
      setCashReservePercent(cashReservePercent);
      setPendingReview(pendingReview);
      setAppliedDecisions({});
    } catch (error) {
      console.error("Failed to run AI:", error);
      alert("Error connecting to backend. Check terminal for details.");
    } finally {
      setIsGenerating(false);
    }
  };

  const hasRun = useRef(false);
  useEffect(() => {
    if (!hasRun.current) {
      hasRun.current = true;
      handleRunAI();
    }
  }, []);

  // Close the wallet popup when clicking anywhere outside it.
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (walletRef.current && !walletRef.current.contains(e.target as Node)) {
        setShowWalletPopup(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Stocks approved from the review panel get folded into the displayed
  // allocation table; stocks kept as cash ("veto") get folded into the
  // displayed cash reserve. Anything never applied stays out of both.

  const displayedPortfolioData: PortfolioSlice[] = useMemo(() => {
    const approvedFromReview = pendingReview
      .filter((item) => appliedDecisions[item.ticker] === "approve")
      .map((item) => ({ name: item.ticker, value: item.target_weight }));
    return [...portfolioData, ...approvedFromReview];
  }, [portfolioData, pendingReview, appliedDecisions]);

  const displayedCashReservePercent = useMemo(() => {
    const fromReview = pendingReview
      .filter((item) => appliedDecisions[item.ticker] === "veto")
      .reduce((sum, item) => sum + item.target_weight, 0);
    return cashReservePercent + fromReview;
  }, [cashReservePercent, pendingReview, appliedDecisions]);

  const cashReserveAmount =
    (displayedCashReservePercent / 100) * investmentAmount;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 p-6 font-sans">
      {/* NAVBAR */}
      <div className="flex justify-between items-center mb-6 bg-slate-900 p-4 rounded-xl border border-slate-800 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg">
            <LayoutDashboard size={20} className="text-white" />
          </div>
          <h1 className="text-xl font-semibold tracking-wide">
            DRL Portfolio Robo-Advisor | Arthur Dashboard
          </h1>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-sm text-slate-400 border-l border-slate-700 pl-6 ml-2">
            Welcome, Pranay
          </div>

          <div className="relative" ref={walletRef}>
            <button
              type="button"
              onClick={() => setShowWalletPopup((prev) => !prev)}
              className="flex items-center gap-1.5 bg-slate-800/70 border border-slate-700 rounded-full px-3 py-1.5 hover:bg-slate-800 transition-colors cursor-pointer"
            >
              <Wallet size={14} className="text-amber-400" />
              <span className="text-xs font-semibold text-amber-400">
                {displayedCashReservePercent.toFixed(1)}%
              </span>
            </button>

            {showWalletPopup && (
              <div className="absolute right-0 mt-2 w-64 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl p-4 z-50">
                <div className="flex items-center gap-2 mb-2">
                  <Wallet size={16} className="text-amber-400" />
                  <span className="text-sm font-semibold text-slate-200">
                    Cash Reserve
                  </span>
                </div>
                <div className="text-2xl font-bold text-slate-100 mb-1">
                  {formatINR(cashReserveAmount)}
                </div>
                <div className="text-xs text-slate-400 mb-3">
                  {displayedCashReservePercent.toFixed(1)}% of your{" "}
                  {formatINR(investmentAmount)} portfolio
                </div>
              </div>
            )}
          </div>

          <Calendar
            size={18}
            className="text-slate-400 cursor-pointer hover:text-white"
          />
          <Bell
            size={18}
            className="text-slate-400 cursor-pointer hover:text-white"
          />
          <Avatar className="h-8 w-8">
            <AvatarFallback className="bg-slate-700 text-slate-200">
              PK
            </AvatarFallback>
          </Avatar>
        </div>
      </div>

      {/* GRID — 4 columns now: Portfolio (1), Performance (2, wider), News (1) */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6 h-[75vh]">
        <div className="xl:col-span-1">
          <PortfolioAllocation
            portfolioData={displayedPortfolioData}
            isGenerating={isGenerating}
            totalValue={investmentAmount}
            onTotalValueChange={setInvestmentAmount}
          />
        </div>

        <div className="xl:col-span-2">
          <PerformanceAnalytics
            aiData={aiData}
            sharpeRatio={sharpeRatio ?? undefined}
            pendingReviewItems={pendingReview}
            onApplyDecisions={(decisions) => setAppliedDecisions(decisions)}
          />
        </div>

        <div className="xl:col-span-1">
          <NewsFeed sentimentNews={sentimentNews} />
        </div>
      </div>
    </div>
  );
}
