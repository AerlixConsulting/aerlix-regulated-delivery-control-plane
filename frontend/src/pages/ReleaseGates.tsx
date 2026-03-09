import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { CheckCircle, XCircle, AlertTriangle, Play } from "lucide-react";
import { useState } from "react";

const API = "/api/v1";

export default function ReleaseGates() {
  const [evaluating, setEvaluating] = useState<string | null>(null);
  const [evalResult, setEvalResult] = useState<Record<string, unknown> | null>(null);
  const queryClient = useQueryClient();

  const { data: releases, isLoading } = useQuery({
    queryKey: ["releases"],
    queryFn: () => axios.get(`${API}/releases`).then((r) => r.data),
  });

  const evaluateMutation = useMutation({
    mutationFn: (releaseId: string) =>
      axios.post(`${API}/policies/evaluate/${releaseId}`).then((r) => r.data),
    onSuccess: (data) => {
      setEvalResult(data);
      queryClient.invalidateQueries({ queryKey: ["releases"] });
    },
    onSettled: () => setEvaluating(null),
  });

  const handleEvaluate = (releaseId: string) => {
    setEvaluating(releaseId);
    setEvalResult(null);
    evaluateMutation.mutate(releaseId);
  };

  if (isLoading) return <div className="text-slate-400">Loading releases...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Release Gates</h1>
        <p className="text-slate-400 mt-1">
          Policy-based release readiness evaluation for {releases?.length ?? 0} releases.
        </p>
      </div>

      {/* Release list */}
      <div className="space-y-3">
        {releases?.map(
          (rel: {
            release_id: string;
            name: string;
            version: string;
            status: string;
            compliance_score: number;
            target_env: string;
          }) => (
            <div
              key={rel.release_id}
              className="bg-slate-900 border border-slate-800 rounded-xl p-5"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    {rel.status === "approved" ? (
                      <CheckCircle size={18} className="text-emerald-400" />
                    ) : rel.status === "blocked" ? (
                      <XCircle size={18} className="text-red-400" />
                    ) : (
                      <AlertTriangle size={18} className="text-amber-400" />
                    )}
                    <h3 className="font-medium text-white">{rel.name}</h3>
                    <code className="text-xs bg-slate-800 px-2 py-0.5 rounded text-blue-400">
                      {rel.release_id}
                    </code>
                  </div>
                  <div className="mt-2 flex gap-4 text-sm text-slate-400">
                    <span>v{rel.version}</span>
                    {rel.target_env && <span>→ {rel.target_env}</span>}
                    {rel.compliance_score != null && (
                      <span
                        className={
                          rel.compliance_score >= 90
                            ? "text-emerald-400"
                            : rel.compliance_score >= 70
                            ? "text-amber-400"
                            : "text-red-400"
                        }
                      >
                        Score: {rel.compliance_score.toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleEvaluate(rel.release_id)}
                  disabled={evaluating === rel.release_id}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg transition-colors"
                >
                  <Play size={12} />
                  {evaluating === rel.release_id ? "Evaluating..." : "Evaluate"}
                </button>
              </div>
            </div>
          )
        )}
      </div>

      {/* Evaluation result */}
      {evalResult && (
        <div
          className={`border rounded-xl p-5 ${
            evalResult.overall_passed
              ? "bg-emerald-900/20 border-emerald-700/40"
              : "bg-red-900/20 border-red-700/40"
          }`}
        >
          <div className="flex items-center gap-2 mb-4">
            {evalResult.overall_passed ? (
              <CheckCircle size={18} className="text-emerald-400" />
            ) : (
              <XCircle size={18} className="text-red-400" />
            )}
            <h3 className="font-medium text-white">
              {evalResult.overall_passed ? "Release APPROVED" : "Release BLOCKED"}
            </h3>
            <span className="text-sm text-slate-400">
              Score: {(evalResult.compliance_score as number)?.toFixed(1)}% — {evalResult.blocking_failures as number} blocking
              failure(s)
            </span>
          </div>

          <div className="space-y-2">
            {(evalResult.checks as Array<{
              rule_id: string;
              rule_name: string;
              passed: boolean;
              blocking: boolean;
              severity: string;
              message: string;
            }>)?.map((check) => (
              <div
                key={check.rule_id}
                className={`flex items-start gap-3 p-3 rounded-lg ${
                  check.passed ? "bg-slate-800/50" : check.blocking ? "bg-red-900/20" : "bg-amber-900/20"
                }`}
              >
                {check.passed ? (
                  <CheckCircle size={14} className="text-emerald-400 mt-0.5 shrink-0" />
                ) : (
                  <XCircle size={14} className="text-red-400 mt-0.5 shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 text-sm">
                    <code className="text-xs text-slate-500">{check.rule_id}</code>
                    <span className="font-medium text-white">{check.rule_name}</span>
                    {check.blocking && !check.passed && (
                      <span className="text-xs bg-red-900/60 text-red-400 px-1.5 py-0.5 rounded">
                        BLOCKING
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-slate-400 mt-0.5">{check.message}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
