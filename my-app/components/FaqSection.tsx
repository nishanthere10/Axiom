"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

const FAQS = [
  {
    question: "Does Atlas train its models on my proprietary codebase?",
    answer: "Absolutely not. We use stateless API endpoints from enterprise-tier providers (OpenAI, Anthropic). Your data is never used to train foundational models. Period.",
  },
  {
    question: "Which underlying AI models does Atlas use?",
    answer: "We intelligently route requests depending on the task. For deep architectural reasoning, we primarily use Claude 3.5 Sonnet and GPT-4o. You'll always get frontier-level intelligence.",
  },
  {
    question: "Can I export these decisions to my existing wiki?",
    answer: "Yes. Every decision is generated as pure GitHub-Flavored Markdown. You can 1-click copy it into Jira, Confluence, Notion, or directly into a markdown file in your codebase.",
  },
  {
    question: "How does the Trust Scoring work?",
    answer: "Atlas doesn't just guess. It generates multiple internal hypotheses, cross-references them against known engineering patterns, and calculates a confidence metric. If the AI isn't sure, it tells you.",
  }
];

export default function FaqSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section className="w-full py-40 px-10 sm:px-16 md:px-24 lg:px-48 border-t border-white/5 bg-background">
      <div className="max-w-4xl mx-auto space-y-16">
        <div className="text-center space-y-4">
          <h2 className="text-3xl md:text-5xl font-display font-bold tracking-tight">Frequently Asked Questions</h2>
          <p className="text-muted-foreground">Everything you need to know about security, AI models, and workflow.</p>
        </div>

        <div className="space-y-4">
          {FAQS.map((faq, idx) => {
            const isOpen = openIndex === idx;
            return (
              <div 
                key={idx} 
                className={cn(
                  "border border-white/10 rounded-xl overflow-hidden transition-all duration-300",
                  isOpen ? "bg-surface/50 border-primary/30 shadow-lg shadow-primary/5" : "bg-background hover:bg-surface/30"
                )}
              >
                <button
                  onClick={() => setOpenIndex(isOpen ? null : idx)}
                  className="w-full flex items-center justify-between p-6 text-left focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:outline-none rounded-xl"
                >
                  <span className="font-display font-semibold text-lg text-foreground">{faq.question}</span>
                  <ChevronDown className={cn(
                    "w-5 h-5 text-muted-foreground transition-transform duration-300 shrink-0",
                    isOpen && "rotate-180 text-primary"
                  )} />
                </button>
                
                <div 
                  className={cn(
                    "grid transition-all duration-300 ease-in-out",
                    isOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
                  )}
                >
                  <div className="overflow-hidden">
                    <p className="p-6 pt-0 text-muted-foreground leading-relaxed">
                      {faq.answer}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
