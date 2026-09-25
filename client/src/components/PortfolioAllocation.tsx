import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

export interface PortfolioSlice {
  name: string;
  value: number;
}

interface PortfolioAllocationProps {
  portfolioData: PortfolioSlice[];
  isGenerating: boolean;
  topN?: number;
  totalValue: number;
  onTotalValueChange: (value: number) => void;
}

const CASH_LABEL = "Cash Reserve";

function formatINR(amount: number): string {
  return `₹${Math.round(amount).toLocaleString("en-IN")}`;
}

export default function PortfolioAllocation({
  portfolioData,
  isGenerating,
  topN = 100,
}: PortfolioAllocationProps) {
  const [userTotalValue, setUserTotalValue] = useState<number>(1000000);

  const { equityRows, cashRow, othersRow, maxWeight } = useMemo(() => {
    const cash = portfolioData.find((s) => s.name === CASH_LABEL) ?? null;
    const equity = portfolioData
      .filter((s) => s.name !== CASH_LABEL)
      .sort((a, b) => b.value - a.value);

    const top = equity.slice(0, topN);
    const rest = equity.slice(topN);

    const others =
      rest.length > 0
        ? {
            name: `Others (${rest.length})`,
            value: rest.reduce((sum, s) => sum + s.value, 0),
          }
        : null;

    const allWeights = [
      ...top.map((s) => s.value),
      ...(cash ? [cash.value] : []),
      ...(others ? [others.value] : []),
    ];
    return {
      equityRows: top,
      cashRow: cash,
      othersRow: others,
      maxWeight: Math.max(1, ...allWeights),
    };
  }, [portfolioData, topN]);

  const renderRow = (
    label: string,
    weight: number,
    dotClass: string,
    barClass: string,
    key: string,
  ) => (
    // FIX: Swapped flexbox for a strict 12-column grid. Nothing can overflow now.
    <div key={key} className="grid grid-cols-12 items-center py-2 gap-1 w-full">
      {/* Stock gets 4/12 width */}
      <div className="col-span-4 flex items-center gap-2 overflow-hidden">
        <span className={`w-2 h-2 rounded-full shrink-0 ${dotClass}`} />
        <span className="text-sm text-slate-200 truncate">{label}</span>
      </div>

      {/* Progress Bar gets 3/12 width */}
      <div className="col-span-3 flex items-center px-1">
        <div className="w-full h-1.5 rounded-full bg-slate-800/60 overflow-hidden">
          <div
            className={`h-full rounded-full ${barClass}`}
            style={{ width: `${(weight / maxWeight) * 100}%` }}
          />
        </div>
      </div>

      {/* Weight gets 2/12 width (shifted safely to the left) */}
      <div className="col-span-2 text-sm font-bold text-slate-100 text-right">
        {weight.toFixed(1)}%
      </div>

      {/* Value gets 3/12 width (anchored firmly to the right) */}
      <div className="col-span-3 text-sm text-slate-400 text-right pr-2 truncate">
        {formatINR((weight / 100) * userTotalValue)}
      </div>
    </div>
  );

  return (
    <Card className="bg-slate-900 border-slate-800 shadow-xl flex flex-col h-full max-h-[644px]">
      <CardHeader className="pb-4">
        <CardTitle className="text-slate-200 text-xl">
          Current Portfolio Allocation
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col min-h-0">
        {isGenerating ? (
          <div className="h-full w-full flex flex-col items-center justify-center text-slate-400">
            <Loader2 size={48} className="animate-spin text-blue-500 mb-4" />
            <p className="animate-pulse">Analyzing Nifty 100 Assets...</p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between bg-slate-800/40 border border-slate-700/50 rounded-lg px-4 py-2.5 mb-6 focus-within:border-blue-500/50 focus-within:bg-slate-800/60 transition-colors">
              <label
                htmlFor="portfolioValue"
                className="text-sm text-slate-400 cursor-pointer"
              >
                Investment amount (₹)
              </label>
              <input
                id="portfolioValue"
                type="number"
                min="0"
                value={userTotalValue || ""}
                onChange={(e) => setUserTotalValue(Number(e.target.value))}
                className="bg-slate-900 border border-slate-700 rounded-md px-3 py-1 text-right text-lg font-bold text-slate-100 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 w-36 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                placeholder="0"
              />
            </div>

            {/* FIX: Applied the exact same 12-column grid structure to the Header */}
            <div className="grid grid-cols-12 items-center pb-2 border-b border-slate-800/60 text-xs text-slate-500 font-medium w-full gap-1">
              <div className="col-span-4 pl-4">Stock</div>
              <div className="col-span-3"></div>
              <div className="col-span-2 text-right">Weight</div>
              <div className="col-span-3 text-right pr-2">Value</div>
            </div>

            <div className="flex-1 overflow-y-auto overflow-x-hidden mt-2 min-h-0 pr-2 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
              {equityRows.map((s) =>
                renderRow(
                  s.name,
                  s.value,
                  "bg-blue-500",
                  "bg-blue-500",
                  s.name,
                ),
              )}
              {cashRow &&
                renderRow(
                  cashRow.name,
                  cashRow.value,
                  "bg-slate-400",
                  "bg-slate-500",
                  "cash",
                )}
              {othersRow &&
                renderRow(
                  othersRow.name,
                  othersRow.value,
                  "bg-slate-600",
                  "bg-slate-500",
                  "others",
                )}
            </div>

            <div className="flex items-center gap-5 mt-4 pt-4 border-t border-slate-800/60 text-xs text-slate-400">
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" />
                Equity
              </span>
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-slate-400 inline-block" />
                Cash
              </span>
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-slate-600 inline-block" />
                Other (grouped, &lt;
                {maxWeight > 0
                  ? (equityRows[equityRows.length - 1]?.value.toFixed(0) ?? 3)
                  : 3}
                % each)
              </span>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
