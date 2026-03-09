import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { CheckCircle, AlertTriangle, XCircle } from "lucide-react";

const API = "/api/v1";

const statusColors: Record<string, { bg: string; text: string }> = {
  implemented: { bg: "bg-emerald-900/30", text: "text-emerald-400" },
  inherited: { bg: "bg-sky-900/30", text: "text-sky-400" },
  partially_implemented: { bg: "bg-amber-900/30", text: "text-amber-400" },
  planned: { bg: "bg-blue-900/30", text: "text-blue-400" },
  not_implemented: { bg: "bg-red-900/30", text: "text-red-400" },
  not_applicable: { bg: "bg-slate-800", text: "text-slate-500" },
};

export default function Controls() {
  const { data: controls, isLoading } = useQuery({
    queryKey: ["controls"],
    queryFn: () => axios.get(`${API}/controls?limit=200`).then((r) => r.data),
  });

  const { data: gaps } = useQuery({
    queryKey: ["trace-gaps"],
    queryFn: () => axios.get(`${API}/traceability/gaps`).then((r) => r.data),
  });

  if (isLoading) {
    return <div className="text-slate-400">Loading controls...</div>;
  }

  const noEvidence = new Set(gaps?.controls_without_evidence || []);

  const familyGroups: Record<string, typeof controls> = {};
  for (const ctrl of controls || []) {
    if (!familyGroups[ctrl.family]) familyGroups[ctrl.family] = [];
    familyGroups[ctrl.family].push(ctrl);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Controls & Evidence</h1>
        <p className="text-slate-400 mt-1">
          {controls?.length ?? 0} NIST 800-53 controls — implementation status and evidence coverage.
        </p>
      </div>

      {noEvidence.size > 0 && (
        <div className="bg-amber-900/20 border border-amber-700/40 rounded-lg px-4 py-2 flex items-center gap-2 text-sm text-amber-400">
          <AlertTriangle size={14} />
          {noEvidence.size} control{noEvidence.size > 1 ? "s" : ""} have no evidence items
        </div>
      )}

      {Object.entries(familyGroups).map(([family, familyControls]) => (
        <div key={family} className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800 bg-slate-800/50">
            <span className="text-sm font-medium text-slate-300">{family}</span>
            <span className="ml-2 text-xs text-slate-500">{familyControls.length} controls</span>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="text-left px-4 py-2 text-slate-400 font-medium">Control ID</th>
                <th className="text-left px-4 py-2 text-slate-400 font-medium">Title</th>
                <th className="text-left px-4 py-2 text-slate-400 font-medium">Baseline</th>
                <th className="text-left px-4 py-2 text-slate-400 font-medium">Evidence</th>
              </tr>
            </thead>
            <tbody>
              {familyControls.map(
                (ctrl: {
                  control_id: string;
                  title: string;
                  baseline: string;
                }) => (
                  <tr
                    key={ctrl.control_id}
                    className="border-b border-slate-800/50 hover:bg-slate-800/20 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <code className="text-xs bg-slate-800 px-2 py-0.5 rounded text-blue-400">
                        {ctrl.control_id}
                      </code>
                    </td>
                    <td className="px-4 py-3 text-slate-200">{ctrl.title}</td>
                    <td className="px-4 py-3">
                      <span className="text-xs capitalize text-slate-400">{ctrl.baseline || "—"}</span>
                    </td>
                    <td className="px-4 py-3">
                      {noEvidence.has(ctrl.control_id) ? (
                        <div className="flex items-center gap-1 text-amber-400 text-xs">
                          <AlertTriangle size={12} />
                          No evidence
                        </div>
                      ) : (
                        <div className="flex items-center gap-1 text-emerald-400 text-xs">
                          <CheckCircle size={12} />
                          Evidenced
                        </div>
                      )}
                    </td>
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
