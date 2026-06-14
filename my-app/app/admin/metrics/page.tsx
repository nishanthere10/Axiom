"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { apiFetch } from "@/lib/api";

export default function AdminMetricsPage() {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  
  const [overview, setOverview] = useState<any>(null);
  const [providers, setProviders] = useState<any[]>([]);
  const [topics, setTopics] = useState<any[]>([]);
  const [memory, setMemory] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isLoaded) return;
    if (!isSignedIn) {
      setError("You must be signed in to view this page.");
      setLoading(false);
      return;
    }

    async function fetchData() {
      try {
        const token = await getToken();
        if (!token) throw new Error("No token available");

        const [ovRes, prRes, tpRes, memRes] = await Promise.all([
          apiFetch<any>("/admin/metrics/overview", token, { getToken }),
          apiFetch<any>("/admin/metrics/providers", token, { getToken }),
          apiFetch<any>("/admin/metrics/topics", token, { getToken }),
          apiFetch<any>("/admin/metrics/memory", token, { getToken })
        ]);

        setOverview(ovRes);
        setProviders(prRes.data || []);
        setTopics(tpRes.data || []);
        setMemory(memRes.data || []);
      } catch (err: any) {
        if (err.message.includes("403") || err.message.toLowerCase().includes("admin access")) {
          setError("Access Denied: You do not have admin privileges.");
        } else {
          setError(err.message || "Failed to load metrics");
        }
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [isLoaded, isSignedIn, getToken]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950 text-gray-400">
        <p>Loading metrics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-950">
        <div className="p-6 bg-red-900/20 border border-red-500/50 text-red-400 rounded-lg max-w-md text-center">
          <h2 className="text-xl font-bold mb-2">Error</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-200 p-8">
      <h1 className="text-3xl font-bold mb-8 text-white">Product Intelligence Dashboard</h1>
      
      {/* OVERVIEW PANEL */}
      <section className="mb-12">
        <h2 className="text-xl font-semibold mb-4 text-gray-300">Overview (Today)</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <StatCard title="Researches" value={overview?.research_count || 0} />
          <StatCard title="Comparisons" value={overview?.comparison_count || 0} />
          <StatCard title="Memory Hit Rate" value={`${overview?.memory_hit_rate || 0}%`} />
          <StatCard title="Avg Latency" value={`${overview?.avg_latency_ms || 0} ms`} />
          <StatCard title="Fallbacks" value={overview?.fallback_count || 0} />
          <StatCard title="Exports" value={overview?.export_count || 0} />
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* TOPIC PANEL */}
        <section>
          <h2 className="text-xl font-semibold mb-4 text-gray-300">Top Research Topics</h2>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
            <table className="w-full text-left">
              <thead>
                <tr className="text-gray-500 border-b border-gray-800">
                  <th className="pb-3 font-medium">Topic</th>
                  <th className="pb-3 font-medium text-right">Count</th>
                  <th className="pb-3 font-medium text-right">%</th>
                </tr>
              </thead>
              <tbody>
                {topics.length === 0 ? (
                  <tr><td colSpan={3} className="py-4 text-center text-gray-500">No data</td></tr>
                ) : topics.map((t, i) => (
                  <tr key={i} className="border-b border-gray-800/50 last:border-0">
                    <td className="py-3 text-gray-300">{t.topic || "Unknown"}</td>
                    <td className="py-3 text-right">{t.research_count}</td>
                    <td className="py-3 text-right">{t.percentage}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* PROVIDER PANEL */}
        <section>
          <h2 className="text-xl font-semibold mb-4 text-gray-300">Provider Health (30 Days)</h2>
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 overflow-x-auto">
            <table className="w-full text-left min-w-[500px]">
              <thead>
                <tr className="text-gray-500 border-b border-gray-800">
                  <th className="pb-3 font-medium">Provider</th>
                  <th className="pb-3 font-medium text-right">Reqs</th>
                  <th className="pb-3 font-medium text-right">Fails</th>
                  <th className="pb-3 font-medium text-right">Fallbacks</th>
                  <th className="pb-3 font-medium text-right">Avg Latency</th>
                </tr>
              </thead>
              <tbody>
                {providers.length === 0 ? (
                  <tr><td colSpan={5} className="py-4 text-center text-gray-500">No data</td></tr>
                ) : providers.map((p, i) => (
                  <tr key={i} className="border-b border-gray-800/50 last:border-0">
                    <td className="py-3 font-medium text-blue-400">{p.provider}</td>
                    <td className="py-3 text-right">{p.requests}</td>
                    <td className="py-3 text-right text-red-400">{p.failures}</td>
                    <td className="py-3 text-right text-orange-400">{p.fallbacks}</td>
                    <td className="py-3 text-right">{p.avg_latency_ms} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
      
      {/* MEMORY PANEL */}
      <section className="mt-12">
        <h2 className="text-xl font-semibold mb-4 text-gray-300">Memory Effectiveness (Daily Trend)</h2>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 overflow-x-auto">
          <table className="w-full text-left min-w-[600px]">
            <thead>
              <tr className="text-gray-500 border-b border-gray-800">
                <th className="pb-3 font-medium">Date</th>
                <th className="pb-3 font-medium text-right">Searches</th>
                <th className="pb-3 font-medium text-right">Hits</th>
                <th className="pb-3 font-medium text-right">Hit Rate</th>
                <th className="pb-3 font-medium text-right">Avg Latency</th>
              </tr>
            </thead>
            <tbody>
              {memory.length === 0 ? (
                <tr><td colSpan={5} className="py-4 text-center text-gray-500">No data</td></tr>
              ) : memory.map((m, i) => {
                const rate = m.memory_search_count > 0 
                  ? ((m.memory_hit_count / m.memory_search_count) * 100).toFixed(1) 
                  : 0;
                return (
                <tr key={i} className="border-b border-gray-800/50 last:border-0">
                  <td className="py-3 text-gray-400">{m.metric_date}</td>
                  <td className="py-3 text-right">{m.memory_search_count}</td>
                  <td className="py-3 text-right text-green-400">{m.memory_hit_count}</td>
                  <td className="py-3 text-right">{rate}%</td>
                  <td className="py-3 text-right">{m.avg_memory_latency_ms || 0} ms</td>
                </tr>
              )})}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function StatCard({ title, value }: { title: string; value: string | number }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 flex flex-col justify-center">
      <h3 className="text-sm text-gray-500 mb-1 font-medium uppercase tracking-wider">{title}</h3>
      <p className="text-3xl font-bold text-gray-100">{value}</p>
    </div>
  );
}
