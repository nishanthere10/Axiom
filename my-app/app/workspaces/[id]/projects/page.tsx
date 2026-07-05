"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { apiFetch } from "@/lib/api";
import { formatDistanceToNow } from "date-fns";
import { FolderKanban, Plus, FlaskConical, BookMarked } from "lucide-react";
import { cn } from "@/lib/utils";

const STATUS_COLORS: Record<string, string> = {
  active:    "bg-green-500/10 text-green-500 border-green-500/20",
  completed: "bg-blue-500/10  text-blue-500  border-blue-500/20",
  archived:  "bg-gray-500/10  text-gray-400  border-gray-500/20",
};

export default function ProjectsPage() {
  const params = useParams();
  const router = useRouter();
  const { getToken } = useAuth();
  const workspaceId = params.id as string;

  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const token = await getToken();
        if (!token) return;
        const data = await apiFetch<{ projects: any[] }>(
          `/workspaces/${workspaceId}/projects`,
          token, { getToken }
        );
        setProjects(data.projects || []);
      } catch (e) {
        console.error("Failed to load projects", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [workspaceId, getToken]);

  const createProject = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const token = await getToken();
      if (!token) return;
      const created = await apiFetch<any>(
        `/workspaces/${workspaceId}/projects`,
        token,
        { method: "POST", body: JSON.stringify({ name: newName.trim(), description: newDesc.trim() || undefined }), getToken }
      );
      setProjects(prev => [{ ...created, research_count: 0, decision_count: 0 }, ...prev]);
      setShowModal(false);
      setNewName("");
      setNewDesc("");
    } catch (e) {
      console.error("Failed to create project", e);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Projects</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Organize your research and decisions into projects.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors shrink-0"
        >
          <Plus className="w-4 h-4" />
          New Project
        </button>
      </div>

      {loading ? (
        <div className="h-64 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      ) : projects.length === 0 ? (
        <div className="text-center py-24 border border-dashed border-border/50 rounded-xl">
          <FolderKanban className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
          <h3 className="text-base font-medium text-foreground">No projects yet</h3>
          <p className="text-sm text-muted-foreground mt-2 max-w-xs mx-auto">
            Create a project to group related research sessions and decisions together.
          </p>
          <button onClick={() => setShowModal(true)}
            className="mt-4 px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors">
            Create your first project
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {projects.map((project: any) => (
            <div
              key={project.id}
              onClick={() => router.push(`/workspaces/${workspaceId}/projects/${project.id}`)}
              className="p-5 border border-border rounded-xl bg-surface hover:border-primary/30 cursor-pointer transition-colors group"
            >
              <div className="flex items-start justify-between gap-3 mb-3">
                <h3 className="text-base font-medium text-foreground group-hover:text-primary transition-colors">
                  {project.name}
                </h3>
                <span className={cn("shrink-0 text-xs px-2 py-0.5 rounded-full border capitalize", STATUS_COLORS[project.status] || STATUS_COLORS.active)}>
                  {project.status}
                </span>
              </div>
              {project.description && (
                <p className="text-sm text-muted-foreground line-clamp-2 mb-3">{project.description}</p>
              )}
              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <FlaskConical className="w-3.5 h-3.5" />
                  {project.research_count} research
                </span>
                <span className="flex items-center gap-1">
                  <BookMarked className="w-3.5 h-3.5" />
                  {project.decision_count} decisions
                </span>
                <span className="ml-auto">{formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create project modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-background border border-border rounded-2xl w-full max-w-md p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-semibold">New Project</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Name *</label>
                <input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && createProject()}
                  placeholder="e.g. Auth Migration Q3"
                  className="mt-1.5 w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Description (optional)</label>
                <textarea
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="What is this project about?"
                  className="mt-1.5 w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary resize-none"
                  rows={2}
                />
              </div>
            </div>
            <div className="flex gap-3 justify-end">
              <button onClick={() => setShowModal(false)} className="px-4 py-2 text-sm text-muted-foreground hover:text-foreground">Cancel</button>
              <button
                onClick={createProject}
                disabled={creating || !newName.trim()}
                className="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {creating ? "Creating…" : "Create Project"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
