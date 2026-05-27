import { Evidence } from "@/types";
import { ExternalLink, CheckCircle, AlertTriangle } from "lucide-react";

export default function EvidenceCard({ evidence }: { evidence: Evidence[] }) {
  if (!evidence || evidence.length === 0) return null;

  return (
    <div className="space-y-4 mb-8">
      <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground border-b border-border pb-2">
        Evidence Sources
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {evidence.map((item, index) => {
          const isHighTrust = item.trust_score >= 0.8;
          const isMediumTrust = item.trust_score >= 0.5 && item.trust_score < 0.8;
          return (
            <div
              key={item.url}
              className="p-4 rounded-md border border-border bg-card shadow-sm hover:border-primary/50 transition-colors flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between mb-2">
                  <span className="text-xs font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">
                    [Source {index + 1}]
                  </span>
                  <div className="flex items-center space-x-1">
                    {isHighTrust ? (
                      <CheckCircle className="w-4 h-4 text-emerald-500" />
                    ) : isMediumTrust ? (
                      <AlertTriangle className="w-4 h-4 text-amber-500" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-destructive" />
                    )}
                    <span className={`text-xs font-medium ${isHighTrust ? "text-emerald-500" : isMediumTrust ? "text-amber-500" : "text-destructive"}`}>
                      {(item.trust_score * 100).toFixed(0)}% Trust
                    </span>
                  </div>
                </div>
                <h4 className="text-sm font-medium text-foreground mb-1 line-clamp-2">
                  {item.title}
                </h4>
                <p className="text-sm text-muted-foreground line-clamp-3 mb-3">
                  "{item.claim}"
                </p>
              </div>
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-primary flex items-center hover:underline mt-auto"
              >
                <ExternalLink className="w-3 h-3 mr-1" />
                View Source
              </a>
            </div>
          );
        })}
      </div>
    </div>
  );
}
