import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { CheckCircle, Clock, AlertTriangle, XCircle } from "lucide-react";

const API = "/api/v1";

const statusColors: Record<string, string> = {
  verified: "text-emerald-400",
  implemented: "text-blue-400",
  approved: "text-sky-400",
  draft: "text-slate-400",
  deprecated: "text-slate-600",
};

const StatusIcon = ({ status }: { status: string }) => {
  switch (status) {
    case "verified":
      return <CheckCircle size={14} className="text-emerald-400" />;
    case "implemented":
      return <CheckCircle size={14} className="text-blue-400" />;
    case "approved":
      return <Clock size={14} className="text-sky-400" />;
    case "draft":
      return <Clock size={14} className="text-slate-400" />;
    default:
      return <XCircle size={14} className="text-slate-600" />;
  }
};

export default function Requirements() {
  const { data: requirements, isLoading } = useQuery({
    queryKey: ["requirements"],
    queryFn: () => axios.get(`${API}/requirements?limit=200`).then((r) => r.data),
  });

  const { data: gaps } = useQuery({
    queryKey: ["trace-gaps"],
    queryFn: () => axios.get(`${API}/traceability/gaps`).then((r) => r.data),
  });

  if (isLoading) {
    return <div className="text-slate-400">Loading requirements...</div>;
  }

  const untested = new Set(gaps?.untested_requirements || []);
  const unmapped = new Set(gaps?.unmapped_requirements || []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Requirements Traceability</h1>
        <p className="text-slate-400 mt-1">
          {requirements?.length ?? 0} requirements — track linkage to controls and test cases.
        </p>
      </div>

      {/* Gap alerts */}
      {(untested.size > 0 || unmapped.size > 0) && (
        <div className="flex gap-3 flex-wrap">
          {untested.size > 0 && (
            <div className="bg-amber-900/20 border border-amber-700/40 rounded-lg px-4 py-2 flex items-center gap-2 text-sm text-amber-400">
              <AlertTriangle size={14} />
              {untested.size} requirement{untested.size > 1 ? "s" : ""} have no test coverage
            </div>
          )}
          {unmapped.size > 0 && (
            <div className="bg-red-900/20 border border-red-700/40 rounded-lg px-4 py-2 flex items-center gap-2 text-sm text-red-400">
              <XCircle size={14} />
              {unmapped.size} requirement{unmapped.size > 1 ? "s" : ""} have no control mapping
            </div>
          )}
        </div>
      )}

      {/* Requirements table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800">
              <th className="text-left px-4 py-3 text-slate-400 font-medium">ID</th>
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Title</th>
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Type</th>
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Priority</th>
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Status</th>
              <th className="text-left px-4 py-3 text-slate-400 font-medium">Gaps</th>
            </tr>
          </thead>
          <tbody>
            {requirements?.map(
              (req: {
                req_id: string;
                title: string;
                req_type: string;
                priority: string;
                status: string;
                source: string;
              }) => (
                <tr
                  key={req.req_id}
                  className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors"
                >
                  <td className="px-4 py-3">
                    <code className="text-xs bg-slate-800 px-2 py-0.5 rounded text-blue-400">
                      {req.req_id}
                    </code>
                  </td>
                  <td className="px-4 py-3 text-slate-200 max-w-xs">
                    <div className="font-medium">{req.title}</div>
                    {req.source && (
                      <div className="text-xs text-slate-500 mt-0.5">{req.source}</div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs bg-slate-800 px-2 py-0.5 rounded text-slate-300 capitalize">
                      {req.req_type}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs capitalize ${
                        req.priority === "critical"
                          ? "text-red-400"
                          : req.priority === "high"
                          ? "text-amber-400"
                          : "text-slate-400"
                      }`}
                    >
                      {req.priority}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      <StatusIcon status={req.status} />
                      <span
                        className={`capitalize ${statusColors[req.status] || "text-slate-400"}`}
                      >
                        {req.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      {untested.has(req.req_id) && (
                        <span className="text-xs bg-amber-900/40 text-amber-400 px-1.5 py-0.5 rounded">
                          no tests
                        </span>
                      )}
                      {unmapped.has(req.req_id) && (
                        <span className="text-xs bg-red-900/40 text-red-400 px-1.5 py-0.5 rounded">
                          no controls
                        </span>
                      )}
                      {!untested.has(req.req_id) && !unmapped.has(req.req_id) && (
                        <CheckCircle size={12} className="text-emerald-400" />
                      )}
                    </div>
                  </td>
                </tr>
              )
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
