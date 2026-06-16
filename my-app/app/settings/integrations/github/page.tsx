"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { motion } from "framer-motion";
import { Github, RefreshCw, CheckCircle2, AlertCircle } from "lucide-react";
import { apiFetch } from "@/lib/api";

interface Repository {
  id: string;
  name: string;
  owner: string;
  full_name: string;
  url: string;
  private: boolean;
  selected?: boolean;
}

interface ActiveRepository {
  repository_id: string;
  repository_name: string;
  repository_owner: string;
  last_synced_at?: string;
}

export default function GitHubIntegrationPage() {
  const { getToken } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [activeRepos, setActiveRepos] = useState<ActiveRepository[]>([]);
  const [availableRepos, setAvailableRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncingMap, setSyncingMap] = useState<Record<string, boolean>>({});

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const token = await getToken();
      const data = await apiFetch("/github/status", {
        headers: { Authorization: `Bearer ${token}` }
      });
      setIsConnected(data.is_connected);
      setActiveRepos(data.active_repositories || []);
      
      if (data.is_connected) {
        fetchAvailableRepos();
      }
    } catch (error) {
      console.error("Failed to fetch GitHub status", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailableRepos = async () => {
    try {
      const token = await getToken();
      const data = await apiFetch("/github/repositories", {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAvailableRepos(data.repositories || []);
    } catch (error) {
      console.error("Failed to fetch available repos", error);
    }
  };

  const connectClerk = async () => {
    // In a real app, this might redirect to Clerk OAuth if not already linked.
    // For now, we assume the user linked it in Clerk settings, and we just verify.
    try {
      const token = await getToken();
      await apiFetch("/github/connect", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchStatus();
    } catch (e) {
      alert("Failed to connect. Make sure you linked your GitHub account in Clerk.");
    }
  };

  const selectRepo = async (repo: Repository) => {
    try {
      const token = await getToken();
      await apiFetch("/github/repositories/select", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          repository_id: repo.id,
          repository_name: repo.name,
          repository_owner: repo.owner,
          repository_url: repo.url,
          is_private: repo.private
        }),
      });
      fetchStatus();
    } catch (error) {
      console.error("Failed to select repo", error);
    }
  };

  const syncRepo = async (repoId: string) => {
    setSyncingMap(prev => ({ ...prev, [repoId]: true }));
    try {
      const token = await getToken();
      await apiFetch(`/github/repositories/${repoId}/sync`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      // Give it a few seconds to finish sync for demo purposes
      setTimeout(() => fetchStatus(), 5000);
    } catch (error) {
      console.error("Failed to sync repo", error);
    } finally {
      setTimeout(() => setSyncingMap(prev => ({ ...prev, [repoId]: false })), 5000);
    }
  };

  if (loading) {
    return <div className="p-10 text-center text-muted-foreground">Loading...</div>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">GitHub Context Provider</h1>
        <p className="text-muted-foreground mt-2">
          Connect your GitHub account to allow Atlas to understand your repository architecture, stack, and context.
        </p>
      </div>

      {!isConnected ? (
        <div className="border border-border/50 rounded-xl p-8 bg-surface text-center space-y-4">
          <Github className="w-12 h-12 mx-auto text-muted-foreground" />
          <h2 className="text-xl font-semibold">Not Connected</h2>
          <p className="text-sm text-muted-foreground max-w-md mx-auto">
            Atlas needs read-only access to your repositories to generate architectural summaries. We do not index source code.
          </p>
          <button 
            onClick={connectClerk}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition"
          >
            Verify GitHub Connection
          </button>
        </div>
      ) : (
        <div className="space-y-8">
          {/* Active Repositories */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Active Repositories</h2>
            {activeRepos.length === 0 ? (
              <div className="text-sm text-muted-foreground p-4 border border-dashed border-border rounded-lg text-center">
                No repositories selected. Select one below.
              </div>
            ) : (
              <div className="grid gap-4">
                {activeRepos.map(repo => (
                  <div key={repo.repository_id} className="flex items-center justify-between p-4 border border-border/50 rounded-lg bg-surface">
                    <div>
                      <h3 className="font-medium">{repo.repository_owner} / {repo.repository_name}</h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        {repo.last_synced_at 
                          ? `Last synced: ${new Date(repo.last_synced_at).toLocaleString()}` 
                          : "Never synced"}
                      </p>
                    </div>
                    <button
                      onClick={() => syncRepo(repo.repository_id)}
                      disabled={syncingMap[repo.repository_id]}
                      className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-md text-sm font-medium hover:bg-secondary/80 disabled:opacity-50"
                    >
                      {syncingMap[repo.repository_id] ? (
                        <RefreshCw className="w-4 h-4 animate-spin" />
                      ) : (
                        <RefreshCw className="w-4 h-4" />
                      )}
                      {syncingMap[repo.repository_id] ? "Syncing..." : "Sync Now"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Available Repositories */}
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">Available Repositories</h2>
            <div className="grid gap-4 max-h-96 overflow-y-auto pr-2">
              {availableRepos.map(repo => (
                <div key={repo.id} className="flex items-center justify-between p-4 border border-border/50 rounded-lg bg-surface/50">
                  <div>
                    <h3 className="font-medium">{repo.full_name}</h3>
                    <span className="text-xs uppercase tracking-widest text-muted-foreground">
                      {repo.private ? "Private" : "Public"}
                    </span>
                  </div>
                  {repo.selected ? (
                    <span className="flex items-center gap-1 text-sm text-success">
                      <CheckCircle2 className="w-4 h-4" /> Added
                    </span>
                  ) : (
                    <button
                      onClick={() => selectRepo(repo)}
                      className="px-4 py-1.5 border border-border text-foreground rounded text-sm hover:bg-surface-hover transition"
                    >
                      Add
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
