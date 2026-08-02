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
    <section className="w-full py-40 px-10 sm:px-16 md:px-24 lg:px-48 border-t border-zinc-900 bg-zinc-950/40 backdrop-blur-md">
      <div className="max-w-3xl mx-auto space-y-16">
        <div className="text-left space-y-4 animate-in fade-in slide-in-from-bottom-8 duration-700">
          <h2 className="text-3xl font-sans font-medium tracking-tight text-zinc-100">Frequently Asked Questions</h2>
          <p className="text-zinc-400">Everything you need to know about security, AI models, and workflow.</p>
        </div>

        <div className="space-y-0 border-t border-zinc-800">
          {FAQS.map((faq, idx) => {
            const isOpen = openIndex === idx;
            return (
              <div 
                key={idx} 
                className="border-b border-zinc-800 transition-colors duration-300 hover:bg-zinc-900/50"
              >
                <button
                  onClick={() => setOpenIndex(isOpen ? null : idx)}
                  className="w-full flex items-center justify-between py-6 text-left focus-visible:ring-2 focus-visible:ring-zinc-500 focus-visible:outline-none"
                >
                  <span className="font-sans font-medium text-lg text-zinc-100">{faq.question}</span>
                  <ChevronDown className={cn(
                    "w-5 h-5 text-zinc-500 transition-transform duration-300 shrink-0",
                    isOpen && "rotate-180 text-zinc-300"
                  )} />
                </button>
                
                <div 
                  className={cn(
                    "grid transition-all duration-300 ease-in-out",
                    isOpen ? "grid-rows-[1fr] opacity-100 pb-6" : "grid-rows-[0fr] opacity-0"
                  )}
                >
                  <div className="overflow-hidden">
                    <p className="text-zinc-400 leading-relaxed max-w-2xl">
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
