'use client';

import React from 'react';
import Link from 'next/link';
import { 
  GitBranch, 
  Database, 
  CheckCircle2, 
  Lightbulb, 
  Clock,
  Layers,
  FileText,
  Activity,
  Plus
} from 'lucide-react';

export function WorkspaceCommandCenter({ dashboardData, workspaceId }: { dashboardData: any, workspaceId: string }) {
  // 🛑 DEFENSIVE GUARD: Ensure data exists before checking .length
  if (!dashboardData || !dashboardData.recent_decisions || !dashboardData.recent_research) {
    return null;
  }

  if (!dashboardData.recent_decisions.length && !dashboardData.recent_research.length && !dashboardData.connected_repositories.length) {
    return <EmptyWorkspaceState workspaceId={workspaceId} />;
  }

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto w-full text-foreground">
      <WorkspaceHeader workspace={dashboardData.workspace} stats={dashboardData} />
      
      {/* Dense IDE-like Bento Box Layout */}
      <div className="flex flex-wrap gap-4 items-stretch">
        <div className="flex-[2_1_600px] min-w-[320px] flex">
          <DecisionTimeline decisions={dashboardData.recent_decisions} workspaceId={workspaceId} />
        </div>
        
        <div className="flex-[1_1_320px] min-w-[320px] flex flex-col gap-4">
          <DecisionStatusSummary summary={dashboardData.decision_summary} />
          <WorkspaceInsights insights={dashboardData.quick_insights} />
        </div>
        
        <div className="flex-[1_1_320px] min-w-[320px] flex">
          <RecentResearchPanel research={dashboardData.recent_research} summary={dashboardData.research_summary} workspaceId={workspaceId} />
        </div>
        
        <div className="flex-[1_1_320px] min-w-[320px] flex">
          <RepositoryPanel repos={dashboardData.connected_repositories} summary={dashboardData.repository_summary} workspaceId={workspaceId} />
        </div>

        <div className="flex-[1_1_320px] min-w-[320px] flex">
          <ComparisonPanel comparisons={dashboardData.recent_comparisons} summary={dashboardData.comparison_summary} workspaceId={workspaceId} />
        </div>

        <div className="flex-[1_1_320px] min-w-[320px] flex">
          <MemoryPanel summary={dashboardData.memory_summary} workspaceId={workspaceId} />
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------
// Sub-components matching IDE aesthetics (dense, dark, structured)
// ---------------------------------------------------------

function EmptyWorkspaceState({ workspaceId }: { workspaceId: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center border border-border rounded-lg bg-surface mt-12 mx-auto max-w-2xl">
      <Layers className="w-8 h-8 text-muted-foreground mb-4" strokeWidth={2} />
      <h2 className="text-xl font-semibold mb-2 text-foreground">Workspace Inactive</h2>
      <p className="text-muted-foreground text-sm mb-6 max-w-md">
        Connect a repository to gain intelligent context, or start your first research session to begin building decision intelligence.
      </p>
      <div className="flex gap-4">
        <Link href={`/workspaces/${workspaceId}/settings`} className="px-4 py-2 text-sm border border-border rounded-md hover:bg-surface-hover transition-colors font-medium">
          Connect GitHub
        </Link>
        <Link href={`/workspaces/${workspaceId}/research`} className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity font-medium">
          Start Research
        </Link>
      </div>
    </div>
  );
}

function WorkspaceHeader({ workspace, stats }: { workspace: any, stats: any }) {
  return (
    <div className="flex flex-col md:flex-row justify-between items-start md:items-end border-b border-border pb-6 gap-4">
      <div className="space-y-1">
        <div className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-2">
          Workspace Overview
        </div>
        <h1 className="text-2xl font-semibold flex items-center gap-2 text-foreground">
          {workspace.icon && <span>{workspace.icon}</span>}
          {workspace.name}
        </h1>
        <p className="text-muted-foreground text-sm">{workspace.description || "No description provided."}</p>
        
        <div className="flex flex-wrap gap-4 mt-4 text-xs font-mono text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <GitBranch className="w-3.5 h-3.5" />
            <span>{stats.repository_summary.connected_repos} Repos</span>
          </div>
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{Object.values(stats.decision_summary).reduce((a: any, b: any) => a + b, 0)} Decisions</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5" />
            <span>{stats.research_summary.total_sessions} Sessions</span>
          </div>
        </div>
      </div>
      <Link href={`/workspaces/${workspace.id}/research`} className="px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:opacity-90 transition-opacity font-medium flex items-center gap-2">
        <Plus className="w-4 h-4" />
        New Research
      </Link>
    </div>
  );
}

function CardWrapper({ children, className = "" }: { children: React.ReactNode, className?: string }) {
  return (
    <div className={`w-full bg-surface border border-border rounded-lg p-5 flex flex-col ${className}`}>
      {children}
    </div>
  );
}

function DecisionTimeline({ decisions, workspaceId }: { decisions: any[], workspaceId: string }) {
  return (
    <CardWrapper>
      <div className="flex items-center gap-2 mb-4 border-b border-border pb-3">
        <CheckCircle2 className="w-4 h-4 text-muted-foreground" />
        <h2 className="text-sm font-semibold tracking-wide uppercase text-muted-foreground">Decision Timeline</h2>
      </div>
      
      {decisions.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-sm text-muted-foreground font-mono">
          No decisions recorded.
        </div>
      ) : (
        <div className="flex flex-col gap-0">
          {decisions.map((d, idx) => (
            <div key={idx} className="flex gap-4 py-3 border-b border-border/50 last:border-0 hover:bg-surface-hover/50 transition-colors px-2 -mx-2 rounded-md">
              <div className="w-20 shrink-0 text-xs font-mono text-muted-foreground pt-0.5">
                {new Date(d.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
              </div>
              
              <div className="flex-1 min-w-0">
                <Link href={`/workspaces/${workspaceId}/decisions/${d.id}`} className="text-sm font-medium text-foreground hover:underline block truncate mb-1.5">
                  {d.title}
                </Link>
                <div className="flex flex-wrap gap-2 items-center text-[11px] font-mono">
                  <span className={`px-1.5 py-0.5 rounded-sm capitalize border ${
                    d.status === 'implemented' ? 'text-success border-success/30 bg-success/10' :
                    d.status === 'approved' ? 'text-primary border-primary/30 bg-primary/10' :
                    d.status === 'rejected' ? 'text-destructive border-destructive/30 bg-destructive/10' :
                    'text-yellow-500 border-yellow-500/30 bg-yellow-500/10'
                  }`}>
                    {d.status || 'proposed'}
                  </span>
                  {d.confidence && (
                    <span className="text-muted-foreground flex items-center gap-1">
                      cnf:{d.confidence}%
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </CardWrapper>
  );
}

function DecisionStatusSummary({ summary }: { summary: any }) {
  return (
    <CardWrapper>
      <div className="flex items-center gap-2 mb-4 border-b border-border pb-3">
        <Activity className="w-4 h-4 text-muted-foreground" />
        <h3 className="text-sm font-semibold tracking-wide uppercase text-muted-foreground">Status Overview</h3>
      </div>
      <div className="grid grid-cols-2 gap-2 text-sm mt-auto">
        <div className="flex justify-between items-center bg-background p-2 rounded-md border border-border">
          <span className="text-muted-foreground text-xs font-medium">Proposed</span>
          <span className="font-mono">{summary.proposed}</span>
        </div>
        <div className="flex justify-between items-center bg-background p-2 rounded-md border border-border">
          <span className="text-primary text-xs font-medium">Approved</span>
          <span className="font-mono text-primary">{summary.approved}</span>
        </div>
        <div className="flex justify-between items-center bg-background p-2 rounded-md border border-border">
          <span className="text-success text-xs font-medium">Implemented</span>
          <span className="font-mono text-success">{summary.implemented}</span>
        </div>
        <div className="flex justify-between items-center bg-background p-2 rounded-md border border-border">
          <span className="text-destructive text-xs font-medium">Rejected</span>
          <span className="font-mono text-destructive">{summary.rejected}</span>
        </div>
      </div>
    </CardWrapper>
  );
}

function WorkspaceInsights({ insights }: { insights: any }) {
  if (!insights.most_common_decision_category && !insights.most_referenced_repository && !insights.most_active_research_area) {
    return null;
  }
  return (
    <CardWrapper>
      <div className="flex items-center gap-2 mb-4 border-b border-border pb-3">
        <Lightbulb className="w-4 h-4 text-muted-foreground" />
        <h3 className="text-sm font-semibold tracking-wide uppercase text-muted-foreground">Insights</h3>
      </div>
      <div className="flex flex-col gap-3 text-sm mt-auto">
        {insights.most_common_decision_category && (
          <div className="flex justify-between items-start border-b border-border/50 pb-2 last:border-0 last:pb-0">
            <span className="text-muted-foreground text-xs">Primary Category</span>
            <span className="font-medium text-foreground text-right">{insights.most_common_decision_category}</span>
          </div>
        )}
        {insights.most_referenced_repository && (
          <div className="flex justify-between items-start border-b border-border/50 pb-2 last:border-0 last:pb-0">
            <span className="text-muted-foreground text-xs">Top Repository</span>
            <span className="font-mono text-xs text-foreground text-right">{insights.most_referenced_repository}</span>
          </div>
        )}
        {insights.most_active_research_area && (
          <div className="flex justify-between items-start pb-2 last:pb-0">
            <span className="text-muted-foreground text-xs">Active Focus</span>
            <span className="font-medium text-foreground text-right">{insights.most_active_research_area}</span>
          </div>
        )}
      </div>
    </CardWrapper>
  );
}

function RepositoryPanel({ repos, summary, workspaceId }: { repos: any[], summary: any, workspaceId: string }) {
  return (
    <CardWrapper>
      <div className="flex justify-between items-center mb-4 border-b border-border pb-3">
        <div className="flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold tracking-wide uppercase text-muted-foreground">Repositories</h3>
        </div>
        <span className="text-xs font-mono bg-background px-2 py-0.5 rounded-sm border border-border">{summary.connected_repos}</span>
      </div>
      
      {repos.length === 0 ? (
        <p className="text-sm text-muted-foreground font-mono m-auto">No repositories connected.</p>
      ) : (
        <div className="flex flex-col gap-2 mt-auto">
          {repos.map((r, i) => (
            <div key={i} className="flex justify-between items-center p-2 rounded-md bg-background border border-border hover:bg-surface-hover transition-colors">
              <div className="font-mono text-xs truncate mr-2">{r.repository_name}</div>
              <div className="text-[10px] uppercase text-muted-foreground shrink-0">
                {new Date(r.last_synced_at).toLocaleDateString()}
              </div>
            </div>
          ))}
          {summary.connected_repos > 5 && (
            <Link href={`/workspaces/${workspaceId}/settings`} className="text-xs font-medium text-muted-foreground hover:text-foreground mt-2 transition-colors">
              View all repositories &rarr;
            </Link>
          )}
        </div>
      )}
    </CardWrapper>
  );
}

function RecentResearchPanel({ research, summary, workspaceId }: { research: any[], summary: any, workspaceId: string }) {
  return (
    <CardWrapper>
      <div className="flex justify-between items-center mb-4 border-b border-border pb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold tracking-wide uppercase text-muted-foreground">Research</h3>
        </div>
        <span className="text-xs font-mono bg-background px-2 py-0.5 rounded-sm border border-border">{summary.total_sessions}</span>
      </div>
      
      {research.length === 0 ? (
        <p className="text-sm text-muted-foreground font-mono m-auto">No recent research.</p>
      ) : (
        <div className="flex flex-col gap-2 mt-auto">
          {research.map((r, i) => (
            <Link key={i} href={`/workspaces/${workspaceId}/research/${r.id}`} className="flex flex-col p-2.5 rounded-md bg-background border border-border hover:bg-surface-hover transition-colors">
              <div className="font-medium text-sm text-foreground truncate">{r.question || 'Untitled Session'}</div>
              <div className="text-[10px] font-mono text-muted-foreground mt-1 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {new Date(r.created_at).toLocaleDateString()}
              </div>
            </Link>
          ))}
          {summary.total_sessions > 5 && (
            <Link href={`/workspaces/${workspaceId}/research`} className="text-xs font-medium text-muted-foreground hover:text-foreground mt-2 transition-colors">
              View all research &rarr;
            </Link>
          )}
        </div>
      )}
    </CardWrapper>
  );
}

function ComparisonPanel({ comparisons, summary, workspaceId }: { comparisons: any[], summary: any, workspaceId: string }) {
  if (comparisons.length === 0) return null;
  return (
    <CardWrapper>
      <div className="flex justify-between items-center mb-4 border-b border-border pb-3">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold tracking-wide uppercase text-muted-foreground">Comparisons</h3>
        </div>
        <span className="text-xs font-mono bg-background px-2 py-0.5 rounded-sm border border-border">{summary.total_comparisons}</span>
      </div>
      
      <div className="flex flex-col gap-2 mt-auto">
        {comparisons.map((c, i) => (
          <Link key={i} href={`/workspaces/${workspaceId}/compare/${c.id}`} className="flex flex-col p-2.5 rounded-md bg-background border border-border hover:bg-surface-hover transition-colors">
            <div className="font-mono text-xs text-foreground truncate">CMP-{c.id.substring(0, 8).toUpperCase()}</div>
            <div className="text-[10px] font-mono text-muted-foreground mt-1 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {new Date(c.created_at).toLocaleDateString()}
            </div>
          </Link>
        ))}
      </div>
    </CardWrapper>
  );
}

function MemoryPanel({ summary, workspaceId }: { summary: any, workspaceId: string }) {
  return (
    <CardWrapper>
      <div className="flex items-center gap-2 mb-4 border-b border-border pb-3">
        <Database className="w-4 h-4 text-muted-foreground" />
        <h3 className="text-sm font-semibold tracking-wide uppercase text-muted-foreground">Memory Stats</h3>
      </div>
      
      <div className="flex flex-col gap-2 text-sm mt-auto">
        <div className="flex justify-between items-center p-2 rounded-md bg-background border border-border">
          <span className="text-muted-foreground text-xs font-medium">Global</span>
          <span className="font-mono text-xs">{summary.global_memories}</span>
        </div>
        <div className="flex justify-between items-center p-2 rounded-md bg-background border border-border">
          <span className="text-muted-foreground text-xs font-medium">Workspace</span>
          <span className="font-mono text-xs text-primary">{summary.workspace_memories}</span>
        </div>
        <div className="flex justify-between items-center p-2 rounded-md bg-background border border-border">
          <span className="text-muted-foreground text-xs font-medium">Pinned</span>
          <span className="font-mono text-xs">{summary.pinned_memories}</span>
        </div>
      </div>
      
      <Link href={`/workspaces/${workspaceId}/memory`} className="w-full mt-4 py-2 rounded-md border border-border text-center text-xs font-medium hover:bg-surface-hover transition-colors">
        Manage Memory
      </Link>
    </CardWrapper>
  );
}
