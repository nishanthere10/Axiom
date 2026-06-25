import { Evidence } from "@/types";
import { ExternalLink, CheckCircle, AlertTriangle } from "lucide-react";

export default function EvidenceCard({ evidence }: { evidence: Evidence[] }) {
  if (!evidence || evidence.length === 0) return null;

  return (
    <div className="space-y-3">
      <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground border-b border-border pb-2">
        Evidence Sources
      </h3>
      <div className="space-y-2">
        {evidence.map((item, index) => {
          const isHighTrust   = item.trust_score >= 0.8;
          const isMediumTrust = item.trust_score >= 0.5 && item.trust_score < 0.8;
          const trustColor = isHighTrust
            ? "text-success"
            : isMediumTrust
            ? "text-amber-500"
            : "text-destructive-foreground";
          const TrustIcon = isHighTrust ? CheckCircle : AlertTriangle;

          return (
            <div
              key={`${item.url}-${index}`}
              className="p-3 rounded-lg border border-border bg-surface hover:border-primary/40 hover:bg-surface-hover transition-all duration-200 flex flex-col justify-between gap-2"
            >
              <div>
                <div className="flex items-start justify-between mb-1.5">
                  <span className="text-xs font-mono text-muted-foreground bg-surface-hover px-2 py-0.5 rounded-sm">
                    [{index + 1}]
                  </span>
                  <div className={`flex items-center gap-1 ${trustColor}`}>
                    <TrustIcon className="w-3.5 h-3.5" />
                    <span className="text-xs font-mono tabular-nums">
                      {(item.trust_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                <h4 className="text-xs font-medium text-foreground mb-1 line-clamp-2 leading-relaxed">
                  {item.title}
                </h4>
                <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                  &ldquo;{item.claim}&rdquo;
                </p>
              </div>
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-primary hover:underline underline-offset-2 mt-1 w-fit"
              >
                <ExternalLink className="w-3 h-3" />
                View Source
              </a>
            </div>
          );
        })}
      </div>
    </div>
  );
}
