import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { AlertTriangle, CheckCircle, XCircle, Clock } from "lucide-react";

const API = "/api/v1";

export default function IncidentsExceptions() {
  const { data: evidence, isLoading } = useQuery({
    queryKey: ["evidence"],
    queryFn: () =>
      axios.get(`${API}/evidence?limit=200`).then((r) => r.data),
  });

  if (isLoading) return <div className="text-slate-400">Loading...</div>;

  // Filter incidents (manual_upload rejected) and exceptions (expired evidence)
  const incidentEvidence = evidence?.filter(
    (e: { status: string; evidence_type: string }) =>
      e.status === "rejected"
  );
  const expiredEvidence = evidence?.filter(
    (e: { status: string }) => e.status === "expired"
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Incidents & Exceptions</h1>
        <p className="text-slate-400 mt-1">
          Open incidents, risk exceptions, and evidence anomalies affecting release readiness.
        </p>
      </div>

      {/* Rejected evidence (incidents) */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-800 bg-red-900/20 flex items-center gap-2">
          <XCircle size={14} className="text-red-400" />
          <span className="text-sm font-medium text-red-400">
            Rejected Evidence ({incidentEvidence?.length ?? 0})
          </span>
        </div>
        {incidentEvidence?.length === 0 ? (
          <div className="px-4 py-6 text-sm text-slate-500 text-center">No rejected evidence items.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="text-left px-4 py-2 text-slate-400">Evidence ID</th>
                <th className="text-left px-4 py-2 text-slate-400">Title</th>
                <th className="text-left px-4 py-2 text-slate-400">Type</th>
                <th className="text-left px-4 py-2 text-slate-400">Source</th>
              </tr>
            </thead>
            <tbody>
              {incidentEvidence?.map(
                (ev: {
                  evidence_id: string;
                  title: string;
                  evidence_type: string;
                  source_system: string;
                  collected_at: string;
                }) => (
                  <tr key={ev.evidence_id} className="border-b border-slate-800/50 hover:bg-slate-800/20">
                    <td className="px-4 py-3">
                      <code className="text-xs bg-slate-800 px-2 py-0.5 rounded text-red-400">
                        {ev.evidence_id}
                      </code>
                    </td>
                    <td className="px-4 py-3 text-slate-200">{ev.title}</td>
                    <td className="px-4 py-3 text-slate-400 text-xs capitalize">
                      {ev.evidence_type.replace(/_/g, " ")}
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs">{ev.source_system}</td>
                  </tr>
                )
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Expired evidence (exceptions) */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-800 bg-amber-900/20 flex items-center gap-2">
          <Clock size={14} className="text-amber-400" />
          <span className="text-sm font-medium text-amber-400">
            Expired Evidence ({expiredEvidence?.length ?? 0})
          </span>
        </div>
        {expiredEvidence?.length === 0 ? (
          <div className="px-4 py-6 text-sm text-slate-500 text-center">No expired evidence items.</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="text-left px-4 py-2 text-slate-400">Evidence ID</th>
                <th className="text-left px-4 py-2 text-slate-400">Title</th>
                <th className="text-left px-4 py-2 text-slate-400">Collected</th>
              </tr>
            </thead>
            <tbody>
              {expiredEvidence?.map(
                (ev: {
                  evidence_id: string;
                  title: string;
                  collected_at: string;
                }) => (
                  <tr key={ev.evidence_id} className="border-b border-slate-800/50 hover:bg-slate-800/20">
                    <td className="px-4 py-3">
                      <code className="text-xs bg-slate-800 px-2 py-0.5 rounded text-amber-400">
                        {ev.evidence_id}
                      </code>
                    </td>
                    <td className="px-4 py-3 text-slate-200">{ev.title}</td>
                    <td className="px-4 py-3 text-xs text-slate-400">
                      {new Date(ev.collected_at).toLocaleDateString()}
                    </td>
                  </tr>
                )
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Healthy evidence */}
      <div className="bg-emerald-900/10 border border-emerald-700/30 rounded-xl p-4 flex items-center gap-2 text-sm text-emerald-400">
        <CheckCircle size={14} />
        {evidence?.filter((e: { status: string }) => e.status === "valid").length ?? 0} evidence items
        are valid and current.
      </div>
    </div>
  );
}
