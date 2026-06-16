"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@clerk/nextjs";
import { submitResearch } from "@/lib/api";
import { ResearchResponse } from "@/types";
import { ArrowRight, Lightbulb } from "lucide-react";
import Loader from "@/components/loader";

const SUGGESTED_PROMPTS = [
  "Design a high-write event logging system using Kafka and ClickHouse.",
  "Compare PostgreSQL vs MongoDB for a geospatial analytics dashboard.",
  "Architecture for a scalable, rate-limited API gateway using Redis."
];

const schema = z.object({
  question: z
    .string()
    .min(10, "Question must be at least 10 characters.")
    .max(1000, "Question must be at most 1000 characters."),
});

type FormValues = z.infer<typeof schema>;

interface Props {
  onSubmitted: (response: ResearchResponse) => void;
}

export default function QuestionInput({ onSubmitted }: Props) {
  const { getToken } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
    watch,
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const questionValue = watch("question", "");

  useEffect(() => {
    const draft = localStorage.getItem("research_draft_question");
    // Only restore if current input is empty, prevents overriding active typing
    if (draft && !questionValue) {
      setValue("question", draft, { shouldValidate: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setValue]);

  useEffect(() => {
    if (questionValue && questionValue.length > 0) {
      localStorage.setItem("research_draft_question", questionValue);
    } else {
      localStorage.removeItem("research_draft_question");
    }
  }, [questionValue]);

  async function onSubmit(data: FormValues) {
    setIsSubmitting(true);
    setApiError(null);
    try {
      const token = (await getToken()) ?? "";
      const response = await submitResearch(data.question, false, token);
      localStorage.removeItem("research_draft_question");
      setValue("question", "");
      onSubmitted(response);
    } catch (err) {
      setApiError(
        err instanceof Error ? err.message : "An unexpected error occurred."
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Heading */}
      <div className="mb-8 text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-sm bg-surface border border-border text-primary text-xs font-mono tracking-widest uppercase mb-3">
          <span className="relative flex h-1.5 w-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-primary" />
          </span>
          Ready
        </div>
        <h1 className="text-2xl font-semibold text-foreground tracking-tight">
          Atlas Research
        </h1>
        <p className="text-sm text-muted-foreground">
          Ask a technical question. Get a structured engineering decision.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
        {/* Textarea — grows with content */}
        <div className="relative group">
          <textarea
            id="question-input"
            {...register("question")}
            rows={4}
            placeholder="e.g. Should I use PostgreSQL or MongoDB for a high-write event log system?"
            disabled={isSubmitting}
            style={{ resize: "vertical", minHeight: "120px", maxHeight: "400px" }}
            className="w-full rounded-lg bg-surface border border-border text-foreground text-sm placeholder:text-muted-foreground p-4 pr-16 focus:outline-none focus:ring-2 focus:ring-primary/40 focus:border-primary/60 disabled:opacity-50 transition-all duration-200 font-mono leading-relaxed"
          />
          {/* Character counter with visual warning */}
          {(() => {
            const len = questionValue?.length ?? 0;
            const counterColor =
              len >= 950 ? "text-destructive-foreground" :
              len >= 800 ? "text-amber-500" :
              "text-muted-foreground";
            return (
              <span className={`absolute bottom-3 right-3 text-xs tabular-nums font-mono select-none transition-colors duration-200 ${counterColor}`}>
                {len}/1000
              </span>
            );
          })()}
        </div>

        {/* Validation errors */}
        {errors.question && (
          <p className="text-xs text-destructive-foreground bg-destructive/10 border border-destructive/30 px-3 py-2 rounded-md" role="alert">
            {errors.question.message}
          </p>
        )}
        {apiError && (
          <p className="text-xs text-destructive-foreground bg-destructive/10 border border-destructive/30 px-3 py-2 rounded-md" role="alert">
            {apiError}
          </p>
        )}

        {/* Submit */}
        <button
          id="submit-research-btn"
          type="submit"
          disabled={isSubmitting}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 focus:ring-2 focus:ring-primary/50 focus:ring-offset-1 focus:ring-offset-background disabled:opacity-50 transition-all duration-200"
        >
          {isSubmitting ? (
            <>
              <div className="w-4 h-4 relative flex items-center justify-center overflow-hidden">
                <Loader scale={0.3} color="currentColor" />
              </div>
              Submitting…
            </>
          ) : (
            <>
              Generate Decision
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      {/* Zero State Prompts */}
      {!isSubmitting && questionValue?.length === 0 && (
        <div className="mt-12 space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-widest px-1">
            <Lightbulb className="w-3.5 h-3.5" />
            <span>Try these templates</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {SUGGESTED_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setValue("question", prompt, { shouldValidate: true });
                  handleSubmit(onSubmit)();
                }}
                className="text-left p-4 rounded-xl bg-surface border border-border/50 hover:border-primary/40 hover:bg-surface-hover hover:shadow-[0_0_15px_rgba(59,130,246,0.1)] transition-all duration-300 group"
              >
                <p className="text-xs text-muted-foreground group-hover:text-foreground font-medium leading-relaxed transition-colors">
                  "{prompt}"
                </p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
