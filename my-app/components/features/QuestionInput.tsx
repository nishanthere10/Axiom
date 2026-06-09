"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@clerk/nextjs";
import { submitResearch } from "@/lib/api";
import { ResearchResponse } from "@/types";

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
    formState: { errors },
    watch,
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const questionValue = watch("question", "");

  async function onSubmit(data: FormValues) {
    setIsSubmitting(true);
    setApiError(null);
    try {
      const token = await getToken() ?? "";
      const response = await submitResearch(data.question, false, token);
      onSubmitted(response);
    } catch (err) {
      setApiError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-semibold text-foreground tracking-tight mb-2">
          Atlas Research
        </h1>
        <p className="text-muted-foreground text-sm">
          Ask a technical question. Get a structured engineering decision.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="relative">
          <textarea
            id="question-input"
            {...register("question")}
            rows={5}
            placeholder="e.g. Should I use PostgreSQL or MongoDB for a high-write event log system?"
            disabled={isSubmitting}
            className="w-full rounded-md bg-surface border border-border text-foreground placeholder:text-muted-foreground text-sm p-4 resize-none focus:outline-none focus:ring-1 focus:ring-primary/50 disabled:opacity-50 transition-colors"
          />
          <span className="absolute bottom-3 right-3 text-xs text-muted-foreground tabular-nums">
            {questionValue?.length ?? 0}/1000
          </span>
        </div>

        {errors.question && (
          <p className="text-sm text-destructive" role="alert">
            {errors.question.message}
          </p>
        )}

        {apiError && (
          <p className="text-sm text-destructive" role="alert">
            {apiError}
          </p>
        )}

        <button
          id="submit-research-btn"
          type="submit"
          disabled={isSubmitting}
          className="w-full py-2 px-4 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 focus:ring-2 focus:ring-primary/50 focus:ring-offset-1 focus:ring-offset-background disabled:opacity-50 transition-all duration-200"
        >
          {isSubmitting ? "Submitting…" : "Generate Decision"}
        </button>
      </form>
    </div>
  );
}
