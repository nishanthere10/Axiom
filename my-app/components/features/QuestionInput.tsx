"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@clerk/nextjs";
import { submitResearch, submitWorkspaceResearch, apiFetch } from "@/lib/api";
import { ResearchResponse } from "@/types";
import { ArrowRight, Lightbulb, FolderKanban } from "lucide-react";
import Loader from "@/components/loader";
import { motion, AnimatePresence } from "framer-motion";
import { Textarea } from "@/components/ui/textarea";

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
  workspaceId?: string;
  onSubmitted: (response: ResearchResponse) => void;
}

const CharCounter = ({ length }: { length: number }) => {
  const counterColor =
    length >= 950 ? "text-destructive-foreground" :
    length >= 800 ? "text-amber-500" :
    "text-muted-foreground/40";
  return (
    <span className={`text-xs tabular-nums font-mono select-none transition-colors duration-200 ${counterColor}`}>
      {length}/1000
    </span>
  );
};

const ErrorMessage = ({ message }: { message: string }) => (
  <motion.p 
    initial={{ opacity: 0, y: -10 }} 
    animate={{ opacity: 1, y: 0 }} 
    exit={{ opacity: 0, y: -10 }}
    className="text-xs text-destructive-foreground bg-destructive/10 border border-destructive/30 px-4 py-2.5 rounded-lg" 
    role="alert"
  >
    {message}
  </motion.p>
);

export default function QuestionInput({ workspaceId, onSubmitted }: Props) {
  const { getToken } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");

  useEffect(() => {
    if (!workspaceId) return;
    async function loadProjects() {
      try {
        const token = await getToken();
        if (!token) return;
        const data = await apiFetch<{ projects: any[] }>(
          `/workspaces/${workspaceId}/projects`,
          token
        );
        setProjects(data.projects?.filter((p: any) => p.status === "active") || []);
      } catch (e) {
        // Non-fatal
      }
    }
    loadProjects();
  }, [workspaceId, getToken]);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
    watch,
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const questionValue = watch("question", "");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const draft = localStorage.getItem("research_draft_question");
      if (draft && !questionValue) {
        setValue("question", draft, { shouldValidate: true });
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setValue]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      if (questionValue && questionValue.length > 0) {
        localStorage.setItem("research_draft_question", questionValue);
      } else {
        localStorage.removeItem("research_draft_question");
      }
    }
  }, [questionValue]);

  async function onSubmit(data: FormValues) {
    setIsSubmitting(true);
    setApiError(null);
    try {
      const token = (await getToken()) ?? "";
      let response;
      if (workspaceId) {
        response = await submitWorkspaceResearch(workspaceId, data.question, false, token, getToken, selectedProjectId || undefined);
      } else {
        response = await submitResearch(data.question, false, token);
      }
      if (typeof window !== "undefined") {
        localStorage.removeItem("research_draft_question");
      }
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
        <h1 className="text-2xl md:text-3xl font-medium text-foreground tracking-tight">
          What are you researching today?
        </h1>
        <p className="text-sm text-muted-foreground">
          Ask a complex technical question to get a structured engineering decision.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Sleek Textarea Wrapper */}
        <div className="relative group rounded-2xl border border-border/60 bg-surface/40 backdrop-blur-sm shadow-sm hover:border-primary/30 hover:bg-surface/80 hover:shadow-[0_0_15px_rgba(59,130,246,0.1)] focus-within:!bg-surface focus-within:shadow-[0_0_20px_rgba(59,130,246,0.15)] focus-within:ring-1 focus-within:ring-primary/20 focus-within:border-primary/40 transition-all duration-500">
          <Textarea
            id="question-input"
            {...register("question")}
            rows={3}
            placeholder="e.g. Should I use PostgreSQL or MongoDB for a high-write event log system?"
            disabled={isSubmitting}
            style={{ resize: "none", minHeight: "100px" }}
            className="w-full bg-transparent border-0 ring-0 focus-visible:ring-0 focus-visible:border-0 shadow-none text-foreground text-sm placeholder:text-muted-foreground/70 p-4 pb-14 focus:outline-none disabled:opacity-50 transition-all duration-200 leading-relaxed"
          />
          
          <div className="absolute bottom-3 right-3 flex items-center gap-4">
            {projects.length > 0 && (
              <div className="flex items-center gap-2 mr-2">
                <FolderKanban className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
                <select
                  value={selectedProjectId}
                  onChange={(e) => setSelectedProjectId(e.target.value)}
                  className="text-xs bg-transparent border-none text-muted-foreground focus:outline-none focus:text-foreground cursor-pointer"
                >
                  <option value="">No project</option>
                  {projects.map((p: any) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
            )}
            <CharCounter length={questionValue?.length ?? 0} />

            {/* Submit Icon Button */}
            <button
              id="submit-research-btn"
              type="submit"
              disabled={isSubmitting || !questionValue?.trim() || !!errors.question}
              className="flex items-center justify-center p-2.5 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50 disabled:bg-surface-hover disabled:text-muted-foreground transition-all duration-200"
            >
              {isSubmitting ? (
                <div className="w-5 h-5 relative flex items-center justify-center overflow-hidden">
                  <Loader scale={0.4} color="currentColor" />
                </div>
              ) : (
                <ArrowRight className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>

        {/* Validation errors */}
        <AnimatePresence>
          {errors.question && <ErrorMessage message={errors.question.message as string} />}
          {apiError && <ErrorMessage message={apiError} />}
        </AnimatePresence>
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
                className="text-left p-4 rounded-xl bg-surface/30 backdrop-blur-sm border border-border/40 hover:border-primary/30 hover:bg-surface-hover/80 hover:shadow-[0_8px_20px_rgba(0,0,0,0.12)] hover:shadow-primary/5 hover:-translate-y-0.5 transition-all duration-300 group"
              >
                <p className="text-xs text-muted-foreground group-hover:text-foreground font-medium leading-relaxed transition-colors">
                  &quot;{prompt}&quot;
                </p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
