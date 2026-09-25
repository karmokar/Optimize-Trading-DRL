import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export interface SentimentNewsItem {
  headline: string;
  time: string;
  tag: "Pos" | "Neg";
  score: number;
  url?: string;
}

interface NewsFeedProps {
  sentimentNews: SentimentNewsItem[];
}

export default function NewsFeed({ sentimentNews }: NewsFeedProps) {
  return (
    <Card className="bg-slate-900 border-slate-800 shadow-xl flex flex-col h-full max-h-[644px]">
      <CardHeader>
        <CardTitle className="text-slate-200">Financial News Feed</CardTitle>
      </CardHeader>

      <CardContent className="flex-1 overflow-y-auto pr-2 min-h-0 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
        <div className="space-y-4 mt-2">
          {sentimentNews.length === 0 ? (
            <p className="text-slate-500 text-sm text-center mt-10">
              No recent News.
            </p>
          ) : (
            sentimentNews.map((news, i) => {
              const content = (
                <>
                  <div className="flex-1 pr-4">
                    <p className="text-sm font-medium text-slate-200 line-clamp-2">
                      {news.headline}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">{news.time}</p>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <Badge
                      className={
                        news.tag === "Pos" ? "bg-emerald-500 text-white" : ""
                      }
                      variant={news.tag === "Pos" ? "default" : "destructive"}
                    >
                      {news.tag}
                    </Badge>
                    <span
                      className={`text-xs font-bold ${
                        news.tag === "Pos" ? "text-emerald-400" : "text-red-400"
                      }`}
                    >
                      {Number(news.score).toFixed(2)}
                    </span>
                  </div>
                </>
              );

              const rowClassName =
                "flex items-center justify-between p-3 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:bg-slate-800 transition-colors";

              return news.url ? (
                <a
                  key={i}
                  href={news.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={rowClassName}
                >
                  {content}
                </a>
              ) : (
                <div
                  key={i}
                  className={`${rowClassName} opacity-70 cursor-default`}
                >
                  {content}
                </div>
              );
            })
          )}
        </div>
      </CardContent>
    </Card>
  );
}
