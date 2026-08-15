"use client";

import { useEffect, useState, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { motion, AnimatePresence } from "framer-motion";
import { RefreshCw, CheckCircle2, ChevronRight, Folder, Loader2 } from "lucide-react";

// Custom Github SVG icon
function GithubIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.02c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A4.8 4.8 0 0 0 8 18v4" />
    </svg>
  );
}

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
  selected_paths?: string[];
}

interface FolderTree {
  folders: { name: string; files: string[]; count: number }[];
  total_count: number;
}

export default function GitHubIntegrationPage() {
  const { getToken } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [activeRepos, setActiveRepos] = useState<ActiveRepository[]>([]);
  const [availableRepos, setAvailableRepos] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);

  // Sync state
  const [syncRepo, setSyncRepo] = useState<ActiveRepository | null>(null);
  const [syncStep, setSyncStep] = useState<number>(0); // 0=List, 1=Picker, 2=Syncing, 3=Done
  const [repoTree, setRepoTree] = useState<FolderTree | null>(null);
  const [selectedFolders, setSelectedFolders] = useState<Set<string>>(new Set());
  
  // Progress state
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState<{current: number; total: number; percent: number; last_file?: string} | null>(null);

  useEffect(() => {
    fetchStatus();
  }, []);

  useEffect(() => {
    let isMounted = true;
    let timeoutId: NodeJS.Timeout;

    const pollProgress = async () => {
      // 🛑 STRICT GUARD: Do not execute if jobId is missing or stringified "undefined"
      if (!jobId || jobId === "undefined" || jobId === "null") {
        return; 
      }

      try {
        const token = await getToken();
        if (!token) return;
        const data = await apiFetch<any>(`/github/sync-jobs/${jobId}/progress`, token);
        
        setProgress({
          current: data.progress_current,
          total: data.progress_total,
          percent: data.percent,
          last_file: data.last_file
        });

        if (data.status === "completed" || data.status === "failed") {
          setSyncStep(3);
          fetchStatus();
          return; // stop polling
        }
      } catch (error) {
        console.error("Polling error:", error);
      }
      
      // Only continue polling if mounted and the job isn't finished
      if (isMounted) {
        timeoutId = setTimeout(pollProgress, 2000); 
      }
    };

    // Only start the initial poll if we have a valid ID
    if (jobId && jobId !== "undefined" && jobId !== "null") {
       pollProgress();
    }

    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
    };
  }, [jobId]);

  const fetchStatus = async () => {
    try {
      const token = await getToken();
      if (!token) return;
      const data = await apiFetch<any>("/github/status", token);
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
      if (!token) return;
      const data = await apiFetch<any>("/github/repositories", token);
      setAvailableRepos(data.repositories || []);
    } catch (error) {
      console.error("Failed to fetch available repos", error);
    }
  };

  const connectClerk = async () => {
    try {
      const token = await getToken();
      if (!token) return;
      await apiFetch("/github/connect", token, { method: "POST" });
      fetchStatus();
    } catch (e) {
      alert("Failed to connect. Make sure you linked your GitHub account in Clerk.");
    }
  };

  const selectAvailableRepo = async (repo: Repository) => {
    try {
      const token = await getToken();
      if (!token) return;
      await apiFetch("/github/repositories/select", token, {
        method: "POST",
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

  const disconnectRepo = async (repoId: string) => {
    try {
      const token = await getToken();
      if (!token) return;
      await apiFetch(`/github/repositories/${repoId}/disconnect`, token, {
        method: "DELETE"
      });
      fetchStatus();
    } catch (error) {
      console.error("Failed to disconnect repo", error);
    }
  };

  const startConfiguringSync = async (repo: ActiveRepository) => {
    setSyncRepo(repo);
    setSyncStep(1);
    setRepoTree(null);
    setSelectedFolders(new Set(repo.selected_paths || []));

    try {
      const token = await getToken();
      if (!token) return;
      const tree = await apiFetch<FolderTree>(`/github/repositories/${repo.repository_id}/files`, token);
      setRepoTree(tree);
      
      // Auto-select all if none were previously selected
      if (!repo.selected_paths || repo.selected_paths.length === 0) {
        setSelectedFolders(new Set(tree.folders.map(f => f.name)));
      }
    } catch (e) {
      console.error("Failed to fetch tree", e);
    }
  };

  const toggleFolder = (folderName: string) => {
    const newSet = new Set(selectedFolders);
    if (newSet.has(folderName)) newSet.delete(folderName);
    else newSet.add(folderName);
    setSelectedFolders(newSet);
  };

  const getTotalSelectedFiles = () => {
    if (!repoTree) return 0;
    return repoTree.folders
      .filter(f => selectedFolders.has(f.name))
      .reduce((sum, f) => sum + f.count, 0);
  };

  const startSync = async () => {
    if (!syncRepo || selectedFolders.size === 0) return;
    setSyncStep(2);
    setProgress({ current: 0, total: getTotalSelectedFiles(), percent: 0 });

    try {
      const token = await getToken();
      if (!token) return;
      const res = await apiFetch<any>(`/github/repositories/${syncRepo.repository_id}/sync`, token, {
        method: "POST",
        body: JSON.stringify({
          selected_folders: Array.from(selectedFolders),
          total_files: getTotalSelectedFiles()
        })
      });
      
      setJobId(res.job_id);
    } catch (e) {
      console.error("Failed to start sync", e);
      setSyncStep(1);
    }
  };



  if (loading) return <div className="p-10 text-center text-muted-foreground flex flex-col items-center gap-2 mt-20"><Loader2 className="w-6 h-6 animate-spin text-primary" /> Loading GitHub Context...</div>;

  return (
    <div className="relative w-full min-h-[calc(100vh-8rem)] flex flex-col pt-8 max-w-4xl mx-auto px-6 space-y-8">
      <div className="absolute inset-0 -z-10 flex items-center justify-center pointer-events-none">
        <div className="absolute w-[600px] h-[600px] bg-primary/5 rounded-full blur-[100px]" />
        <div className="absolute w-[400px] h-[400px] bg-blue-500/5 rounded-full blur-[80px] translate-x-1/4 -translate-y-1/4" />
      </div>

      <div className="text-center md:text-left">
        <h1 className="text-3xl font-medium tracking-tight text-foreground">GitHub Context Provider</h1>
        <p className="text-sm text-muted-foreground mt-2">
          Connect your GitHub account to allow Axiom to understand your repository architecture, stack, and context.
        </p>
      </div>

      {!isConnected ? (
        <div className="relative group rounded-2xl border border-border/60 bg-surface/40 backdrop-blur-sm shadow-sm p-10 text-center space-y-5 transition-all duration-300">
          <GithubIcon className="w-14 h-14 mx-auto text-muted-foreground group-hover:text-foreground transition-colors" />
          <h2 className="text-2xl font-medium tracking-tight">Not Connected</h2>
          <p className="text-sm text-muted-foreground max-w-md mx-auto leading-relaxed">
            Axiom needs read-only access to your repositories to generate architectural summaries. We do not index source code.
          </p>
          <button onClick={connectClerk} className="mt-4 px-6 py-3 bg-primary text-primary-foreground rounded-xl font-medium hover:bg-primary/90 focus:ring-2 focus:ring-primary/50 transition-all duration-200 shadow-sm inline-flex items-center gap-2">
            Verify GitHub Connection
          </button>
        </div>
      ) : syncStep === 0 ? (
        <div className="space-y-8">
          <div className="space-y-4">
            <h2 className="text-xl font-medium tracking-tight">Active Repositories</h2>
            {activeRepos.length === 0 ? (
              <div className="text-sm text-muted-foreground p-6 border border-dashed border-border/60 rounded-2xl bg-surface/20 text-center">
                No repositories selected. Select one below.
              </div>
            ) : (
              <div className="grid gap-4">
                {activeRepos.map(repo => (
                  <div key={repo.repository_id} className="flex items-center justify-between p-5 border border-border/60 rounded-2xl bg-surface/40 backdrop-blur-sm hover:border-border/80 hover:bg-surface/80 transition-all duration-300 shadow-sm group">
                    <div>
                      <h3 className="font-medium text-foreground">{repo.repository_owner} / {repo.repository_name}</h3>
                      <p className="text-xs text-muted-foreground/80 mt-1">
                        {repo.last_synced_at ? `Last synced: ${new Date(repo.last_synced_at).toLocaleString()}` : "Never synced"}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => disconnectRepo(repo.repository_id)}
                        className="px-3 py-2 border border-destructive/30 text-destructive rounded-xl text-sm font-medium hover:bg-destructive/10 transition-all duration-200"
                      >
                        Disconnect
                      </button>
                      <button
                        onClick={() => startConfiguringSync(repo)}
                        className="flex items-center gap-2 px-4 py-2 bg-surface/60 border border-border/40 text-foreground rounded-xl text-sm font-medium hover:bg-surface hover:border-border/80 transition-all duration-200"
                      >
                        Configure Sync <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-foreground transition-colors" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="space-y-4">
            <h2 className="text-xl font-medium tracking-tight">Available Repositories</h2>
            <div className="grid gap-3 max-h-96 overflow-y-auto pr-2 pb-8">
              {availableRepos.map(repo => (
                <div key={repo.id} className="flex items-center justify-between p-4 border border-border/40 rounded-xl bg-surface/20 backdrop-blur-sm hover:bg-surface/50 hover:border-border/60 transition-all duration-200">
                  <div>
                    <h3 className="font-medium text-sm text-foreground">{repo.full_name}</h3>
                    <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground/70">
                      {repo.private ? "Private" : "Public"}
                    </span>
                  </div>
                  {repo.selected ? (
                    <span className="flex items-center gap-1.5 text-xs font-medium text-success">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Added
                    </span>
                  ) : (
                    <button onClick={() => selectAvailableRepo(repo)} className="px-4 py-1.5 bg-surface/50 border border-border/50 text-foreground rounded-lg text-xs font-medium hover:bg-surface hover:border-border/80 transition-all duration-200">
                      Add
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="relative group rounded-2xl border border-border/60 bg-surface/40 backdrop-blur-sm shadow-sm p-8 overflow-hidden transition-all duration-300">
          <div className="flex items-center gap-4 mb-8 border-b border-border/40 pb-4">
            <button onClick={() => setSyncStep(0)} className="text-muted-foreground hover:text-foreground text-sm font-medium px-2 py-1 rounded-md hover:bg-surface-hover transition-colors">← Back</button>
            <h2 className="text-lg font-medium tracking-tight">Sync: <span className="text-muted-foreground font-normal">{syncRepo?.repository_owner}/</span>{syncRepo?.repository_name}</h2>
          </div>

          <AnimatePresence mode="wait">
            {syncStep === 1 && (
              <motion.div key="step1" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium">Select Folders to Contextualize</h3>
                  <p className="text-sm text-muted-foreground mt-1">We found .md files in the following folders. Select which ones contain relevant architectural or API context.</p>
                </div>

                {!repoTree ? (
                  <div className="flex items-center justify-center py-10 gap-2 text-muted-foreground"><Loader2 className="w-5 h-5 animate-spin text-primary" /> Fetching file tree...</div>
                ) : (
                  <div className="grid gap-3 max-h-[400px] overflow-y-auto pr-2">
                    <div className="flex justify-end gap-3 mb-2">
                      <button onClick={() => setSelectedFolders(new Set(repoTree.folders.map(f => f.name)))} className="text-xs font-medium text-primary hover:text-primary/80 transition-colors">Select All</button>
                      <button onClick={() => setSelectedFolders(new Set())} className="text-xs font-medium text-muted-foreground hover:text-foreground transition-colors">Deselect All</button>
                    </div>
                    {repoTree.folders.map(f => (
                      <label key={f.name} className={`flex items-center gap-4 p-4 border rounded-xl cursor-pointer transition-all duration-200 ${selectedFolders.has(f.name) ? "border-primary/40 bg-primary/5 shadow-[0_4px_12px_rgba(59,130,246,0.05)]" : "border-border/40 bg-surface/30 hover:border-border/80 hover:bg-surface/60"}`}>
                        <input type="checkbox" className="w-4 h-4 rounded border-border text-primary focus:ring-primary/50" checked={selectedFolders.has(f.name)} onChange={() => toggleFolder(f.name)} />
                        <Folder className={`w-5 h-5 ${selectedFolders.has(f.name) ? "text-primary/80" : "text-muted-foreground/60"}`} />
                        <div className="flex-1">
                          <p className="font-medium text-sm text-foreground">{f.name === "root" ? "/" : f.name}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">{f.count} Markdown files</p>
                        </div>
                      </label>
                    ))}
                  </div>
                )}

                <div className="pt-6 border-t border-border/40 flex items-center justify-between">
                  <div className="text-sm text-muted-foreground">
                    Will sync <strong className="text-foreground font-medium">{getTotalSelectedFiles()}</strong> files across <strong className="text-foreground font-medium">{selectedFolders.size}</strong> folders
                  </div>
                  <button onClick={startSync} disabled={selectedFolders.size === 0} className="px-6 py-2.5 bg-primary text-primary-foreground rounded-xl text-sm font-medium disabled:opacity-50 hover:bg-primary/90 transition-colors shadow-sm">
                    Start Parallel Sync
                  </button>
                </div>
              </motion.div>
            )}

            {syncStep === 2 && (
              <motion.div key="step2" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-8 py-8 text-center">
                <Loader2 className="w-12 h-12 animate-spin text-primary mx-auto" />
                <div className="space-y-2">
                  <h3 className="text-2xl font-bold">Vectorizing Documentation...</h3>
                  <p className="text-muted-foreground">Reading, summarizing, and embedding files into Pinecone in parallel.</p>
                </div>

                <div className="max-w-md mx-auto space-y-4 pt-4">
                  <div className="h-3 w-full bg-border rounded-full overflow-hidden">
                    <div className="h-full bg-primary transition-all duration-500 ease-out" style={{ width: `${progress?.percent || 0}%` }} />
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground truncate max-w-[200px]">
                      {progress?.last_file ? progress.last_file : "Initializing..."}
                    </span>
                    <span className="font-medium text-foreground">{progress?.current || 0} / {progress?.total || getTotalSelectedFiles()}</span>
                  </div>
                </div>
              </motion.div>
            )}

            {syncStep === 3 && (
              <motion.div key="step3" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="space-y-6 py-8 text-center">
                <div className="w-16 h-16 bg-success/10 border border-success/20 text-success rounded-full flex items-center justify-center mx-auto mb-6 shadow-[0_0_20px_rgba(34,197,94,0.15)]">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h3 className="text-2xl font-medium tracking-tight">Sync Complete!</h3>
                <p className="text-muted-foreground max-w-sm mx-auto mt-2">
                  Successfully embedded {progress?.current} markdown files. They are now available as context during your research sessions.
                </p>
                <div className="pt-8">
                  <button onClick={() => setSyncStep(0)} className="px-6 py-2.5 border border-border/60 bg-surface/50 rounded-xl text-sm font-medium hover:bg-surface hover:border-border/80 transition-all duration-200">
                    Return to Repositories
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
