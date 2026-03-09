import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import {
  Shield,
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileCheck,
  TrendingUp,
} from "lucide-react";

const API = "/api/v1";

interface DashboardSummary {
  total_requirements: number;
  requirements_with_controls: number;
  requirements_with_tests: number;
  total_controls: number;
  controls_implemented: number;
  controls_with_evidence: number;
  total_evidence_items: number;
  evidence_valid: number;
  evidence_expired: number;
  total_releases: number;
  releases_approved: number;
  releases_blocked: number;
  open_exceptions: number;
  open_incidents: number;
  compliance_score: number;
  audit_completeness_score: number;
}

function StatCard({
  title,
  value,
  sub,
  icon: Icon,
  color = "blue",
  status,
}: {
  title: string;
  value: number | string;
  sub?: string;
  icon: React.ElementType;
  color?: string;
  status?: "good" | "warning" | "bad";
}) {
  const colorMap: Record<string, string> = {
    blue: "bg-blue-600",
    green: "bg-emerald-600",
    red: "bg-red-600",
    yellow: "bg-amber-500",
    purple: "bg-purple-600",
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">{title}</div>
          <div className="text-3xl font-bold text-white">{value}</div>
          {sub && <div className="text-sm text-slate-400 mt-1">{sub}</div>}
        </div>
        <div className={`${colorMap[color] || colorMap.blue} p-2 rounded-lg`}>
          <Icon size={20} className="text-white" />
        </div>
      </div>
      {status && (
        <div className="mt-3 flex items-center gap-1 text-xs">
          {status === "good" && <CheckCircle size={12} className="text-emerald-400" />}
          {status === "warning" && <AlertTriangle size={12} className="text-amber-400" />}
          {status === "bad" && <XCircle size={12} className="text-red-400" />}
          <span
            className={
              status === "good"
                ? "text-emerald-400"
                : status === "warning"
                ? "text-amber-400"
                : "text-red-400"
            }
          >
            {status === "good" ? "On track" : status === "warning" ? "Needs attention" : "Action required"}
          </span>
        </div>
      )}
    </div>
  );
}

function ScoreRing({ score, label }: { score: number; label: string }) {
  const r = 52;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 90 ? "#10b981" : score >= 70 ? "#f59e0b" : "#ef4444";

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width="128" height="128" viewBox="0 0 128 128">
        <circle cx="64" cy="64" r={r} fill="none" stroke="#1e293b" strokeWidth="10" />
        <circle
          cx="64"
          cy="64"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 64 64)"
        />
        <text x="64" y="64" textAnchor="middle" dominantBaseline="middle" fill="white" fontSize="22" fontWeight="bold">
          {score.toFixed(0)}%
        </text>
      </svg>
      <div className="text-sm text-slate-400">{label}</div>
    </div>
  );
}

export default function Dashboard() {
  const { data: auditSummary, isLoading } = useQuery({
    queryKey: ["audit-summary"],
    queryFn: () => axios.get(`${API}/audit/summary`).then((r) => r.data),
  });

  const { data: traceStats } = useQuery({
    queryKey: ["trace-stats"],
    queryFn: () => axios.get(`${API}/traceability/stats`).then((r) => r.data),
  });

  const { data: releases } = useQuery({
    queryKey: ["releases"],
    queryFn: () => axios.get(`${API}/releases`).then((r) => r.data),
  });

  const { data: requirements } = useQuery({
    queryKey: ["requirements-count"],
    queryFn: () => axios.get(`${API}/requirements/count`).then((r) => r.data),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">Loading dashboard...</div>
      </div>
    );
  }

  const approved = releases?.filter((r: { status: string }) => r.status === "approved").length ?? 0;
  const blocked = releases?.filter((r: { status: string }) => r.status === "blocked").length ?? 0;
  const totalReleases = releases?.length ?? 0;

  const complianceScore = auditSummary?.audit_completeness_score ?? 0;
  const traceScore = traceStats
    ? (traceStats.req_test_coverage_pct +
        traceStats.req_control_coverage_pct +
        traceStats.control_evidence_coverage_pct) /
      3
    : 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Compliance Overview</h1>
        <p className="text-slate-400 mt-1">
          Real-time posture across requirements, controls, evidence, and releases.
        </p>
      </div>

      {/* Score rings */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-6">
          Posture Scores
        </div>
        <div className="flex gap-12 justify-around flex-wrap">
          <ScoreRing score={complianceScore} label="Audit Completeness" />
          <ScoreRing score={traceScore} label="Traceability Coverage" />
          <ScoreRing
            score={totalReleases > 0 ? (approved / totalReleases) * 100 : 0}
            label="Release Approval Rate"
          />
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Requirements"
          value={requirements?.count ?? traceStats?.total_requirements ?? "—"}
          sub={`${traceStats?.req_control_coverage_pct ?? 0}% mapped to controls`}
          icon={FileCheck}
          color="blue"
          status={
            (traceStats?.req_control_coverage_pct ?? 0) >= 90
              ? "good"
              : (traceStats?.req_control_coverage_pct ?? 0) >= 70
              ? "warning"
              : "bad"
          }
        />
        <StatCard
          title="Controls"
          value={traceStats?.total_controls ?? auditSummary?.control_summary?.total_controls ?? "—"}
          sub={`${traceStats?.control_evidence_coverage_pct ?? 0}% have evidence`}
          icon={Shield}
          color="purple"
          status={
            (traceStats?.control_evidence_coverage_pct ?? 0) >= 80
              ? "good"
              : (traceStats?.control_evidence_coverage_pct ?? 0) >= 60
              ? "warning"
              : "bad"
          }
        />
        <StatCard
          title="Releases Approved"
          value={approved}
          sub={`${blocked} blocked • ${totalReleases} total`}
          icon={CheckCircle}
          color={blocked > 0 ? "yellow" : "green"}
          status={blocked === 0 ? "good" : "warning"}
        />
        <StatCard
          title="Open Exceptions"
          value={auditSummary?.open_exceptions ?? "—"}
          sub="Unresolved risk exceptions"
          icon={AlertTriangle}
          color={auditSummary?.open_exceptions > 0 ? "yellow" : "green"}
          status={auditSummary?.open_exceptions === 0 ? "good" : "warning"}
        />
      </div>

      {/* Gaps summary */}
      {auditSummary?.total_gaps > 0 && (
        <div className="bg-amber-900/20 border border-amber-700/40 rounded-xl p-5">
          <div className="flex items-center gap-2 text-amber-400 font-medium mb-3">
            <AlertTriangle size={16} />
            {auditSummary.total_gaps} Identified Gap{auditSummary.total_gaps > 1 ? "s" : ""}
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            {auditSummary.control_summary && (
              <div className="text-slate-300">
                <div className="font-medium text-white">
                  {auditSummary.control_summary.not_implemented_count ?? 0}
                </div>
                <div className="text-slate-400">Controls not implemented</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Evidence summary */}
      {auditSummary?.evidence_summary && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">
            Evidence Summary
          </div>
          <div className="flex gap-8 flex-wrap">
            <div>
              <div className="text-2xl font-bold text-white">
                {auditSummary.evidence_summary.total}
              </div>
              <div className="text-sm text-slate-400">Total evidence items</div>
            </div>
            {Object.entries(auditSummary.evidence_summary.by_status || {}).map(
              ([status, count]) => (
                <div key={status}>
                  <div className="text-2xl font-bold text-white">{count as number}</div>
                  <div className="text-sm text-slate-400 capitalize">{status}</div>
                </div>
              )
            )}
          </div>
        </div>
      )}
    </div>
  );
}
