import { SummaryCardSpec, HighlightType } from "@/lib/visuals";
import { BarChart2, Scale, AlertTriangle, CheckCircle2, TrendingUp, ShieldCheck } from "lucide-react";

const CONFIDENCE_STYLES: Record<string, { bg: string; text: string; bar: string }> = {
  high:   { bg: "bg-emerald-500/10 border border-emerald-500/20", text: "text-emerald-400", bar: "from-emerald-500 to-teal-400"   },
  medium: { bg: "bg-amber-500/10 border border-amber-500/20",     text: "text-amber-400",   bar: "from-amber-500 to-orange-400"   },
  low:    { bg: "bg-red-500/10 border border-red-500/20",         text: "text-red-400",      bar: "from-red-500 to-rose-400"       },
};

const HIGHLIGHT_STYLES: Record<
  HighlightType,
  { bg: string; border: string; label: string; iconBg: string; iconColor: string; Icon: React.FC<{ className?: string }> }
> = {
  metric:         { bg: "bg-blue-950/40",    border: "border-blue-800/40",    label: "text-blue-400",    iconBg: "bg-blue-500/15",    iconColor: "text-blue-400",    Icon: BarChart2     },
  tradeoff:       { bg: "bg-purple-950/40",  border: "border-purple-800/40",  label: "text-purple-400",  iconBg: "bg-purple-500/15",  iconColor: "text-purple-400",  Icon: Scale         },
  warning:        { bg: "bg-red-950/40",     border: "border-red-800/40",     label: "text-red-400",     iconBg: "bg-red-500/15",     iconColor: "text-red-400",     Icon: AlertTriangle },
  recommendation: { bg: "bg-emerald-950/40", border: "border-emerald-800/40", label: "text-emerald-400", iconBg: "bg-emerald-500/15", iconColor: "text-emerald-400", Icon: CheckCircle2  },
};

export default function ResearchSummaryCardRenderer({ spec }: { spec: SummaryCardSpec }) {
  const confidenceKey = (spec.confidence ?? "").toLowerCase() as keyof typeof CONFIDENCE_STYLES;
  const confStyle = CONFIDENCE_STYLES[confidenceKey] ?? CONFIDENCE_STYLES["medium"];

  return (
    <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
      {/* Top accent bar */}
      <div className={`h-0.5 w-full bg-gradient-to-r ${confStyle.bar}`} />

      <div className="p-6 space-y-6">
        {/* Title + summary */}
        <div className="space-y-2">
          <h4 className="font-semibold text-lg leading-snug">{spec.title}</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">{spec.summary}</p>
        </div>

        {/* Confidence + Consensus */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className={`flex items-center gap-3 p-4 rounded-lg ${confStyle.bg}`}>
            <div className={`p-2 rounded-md ${confStyle.bg}`}>
              <ShieldCheck className={`w-4 h-4 ${confStyle.text}`} />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold mb-0.5">Confidence</p>
              <p className={`font-bold text-base capitalize ${confStyle.text}`}>{spec.confidence}</p>
            </div>
          </div>
          <div className="flex items-start gap-3 bg-muted/20 border border-border/50 p-4 rounded-lg">
            <div className="p-2 rounded-md bg-muted/40 mt-0.5">
              <TrendingUp className="w-4 h-4 text-muted-foreground" />
            </div>
            <div className="min-w-0">
              <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold mb-0.5">Industry Consensus</p>
              <p className="text-sm font-medium text-foreground leading-snug">{spec.consensus}</p>
            </div>
          </div>
        </div>

        {/* Highlights */}
        {spec.highlights && spec.highlights.length > 0 && (
          <div className="space-y-3">
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold">Key Highlights</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {spec.highlights.map((h, i) => {
                const hType = (h.highlight_type ?? "metric") as HighlightType;
                const hs = HIGHLIGHT_STYLES[hType];
                const { Icon } = hs;
                return (
                  <div key={i} className={`flex items-start gap-3 p-3 rounded-lg border ${hs.bg} ${hs.border}`}>
                    <div className={`p-1.5 rounded-md shrink-0 mt-0.5 ${hs.iconBg}`}>
                      <Icon className={`w-3.5 h-3.5 ${hs.iconColor}`} />
                    </div>
                    <div className="min-w-0">
                      <span className={`block text-[10px] uppercase tracking-widest font-bold mb-0.5 ${hs.label}`}>{h.label}</span>
                      <span className="block text-sm font-medium text-foreground leading-snug">{h.value}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
