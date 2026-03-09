import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { GitBranch, Box, FileCheck, AlertTriangle } from "lucide-react";

const API = "/api/v1";

export default function Traceability() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["trace-stats"],
    queryFn: () => axios.get(`${API}/traceability/stats`).then((r) => r.data),
  });

  const { data: gaps } = useQuery({
    queryKey: ["trace-gaps"],
    queryFn: () => axios.get(`${API}/traceability/gaps`).then((r) => r.data),
  });

  if (statsLoading) return <div className="text-slate-400">Loading traceability data...</div>;

  const coverageItems = [
    {
      label: "Requirement → Control coverage",
      pct: stats?.req_control_coverage_pct ?? 0,
      icon: FileCheck,
    },
    {
      label: "Requirement → Test coverage",
      pct: stats?.req_test_coverage_pct ?? 0,
      icon: GitBranch,
    },
    {
      label: "Control → Evidence coverage",
      pct: stats?.control_evidence_coverage_pct ?? 0,
      icon: Box,
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Traceability Graph</h1>
        <p className="text-slate-400 mt-1">
          End-to-end linkage from requirements through controls, tests, evidence, and releases.
        </p>
      </div>

      {/* Coverage meters */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {coverageItems.map(({ label, pct, icon: Icon }) => (
          <div key={label} className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <Icon size={16} className="text-blue-400" />
              <span className="text-sm text-slate-400">{label}</span>
            </div>
            <div className="text-3xl font-bold text-white mb-2">{pct.toFixed(1)}%</div>
            <div className="w-full bg-slate-800 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${
                  pct >= 90
                    ? "bg-emerald-500"
                    : pct >= 70
                    ? "bg-amber-500"
                    : "bg-red-500"
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Gap breakdown */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">
          Gap Analysis
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          <div>
            <div className="text-2xl font-bold text-white">{stats?.untested_requirements ?? 0}</div>
            <div className="text-sm text-slate-400">Untested requirements</div>
            {gaps?.untested_requirements?.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {gaps.untested_requirements.map((id: string) => (
                  <code key={id} className="text-xs bg-amber-900/30 text-amber-400 px-1.5 py-0.5 rounded">
                    {id}
                  </code>
                ))}
              </div>
            )}
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{stats?.unmapped_requirements ?? 0}</div>
            <div className="text-sm text-slate-400">Requirements without controls</div>
            {gaps?.unmapped_requirements?.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {gaps.unmapped_requirements.map((id: string) => (
                  <code key={id} className="text-xs bg-red-900/30 text-red-400 px-1.5 py-0.5 rounded">
                    {id}
                  </code>
                ))}
              </div>
            )}
          </div>
          <div>
            <div className="text-2xl font-bold text-white">
              {stats?.controls_without_evidence ?? 0}
            </div>
            <div className="text-sm text-slate-400">Controls without evidence</div>
            {gaps?.controls_without_evidence?.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {gaps.controls_without_evidence.map((id: string) => (
                  <code key={id} className="text-xs bg-amber-900/30 text-amber-400 px-1.5 py-0.5 rounded">
                    {id}
                  </code>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Summary table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">
          Totals
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <div className="text-2xl font-bold text-white">{stats?.total_requirements ?? 0}</div>
            <div className="text-sm text-slate-400">Requirements</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{stats?.total_controls ?? 0}</div>
            <div className="text-sm text-slate-400">Controls</div>
          </div>
        </div>
      </div>

      <div className="bg-blue-900/10 border border-blue-700/30 rounded-xl p-5 text-sm text-blue-300">
        <div className="flex items-center gap-2 font-medium mb-1">
          <AlertTriangle size={14} />
          Interactive graph visualization
        </div>
        Graph visualization (D3/Cytoscape) is available in the full deployment. Use the{" "}
        <code className="bg-slate-800 px-1 rounded">GET /api/v1/traceability/graph</code> endpoint to
        retrieve the raw graph data for custom visualization.
      </div>
    </div>
  );
}
