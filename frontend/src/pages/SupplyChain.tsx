import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { Package, CheckCircle, XCircle, AlertTriangle, Shield } from "lucide-react";

const API = "/api/v1";

export default function SupplyChain() {
  const { data: releases, isLoading } = useQuery({
    queryKey: ["releases-detail"],
    queryFn: () =>
      axios.get(`${API}/releases?limit=50`).then(async (r) => {
        const releases = r.data;
        const details = await Promise.all(
          releases.map((rel: { release_id: string }) =>
            axios.get(`${API}/releases/${rel.release_id}`).then((d) => d.data)
          )
        );
        return details;
      }),
  });

  if (isLoading) return <div className="text-slate-400">Loading supply chain data...</div>;

  const allArtifacts = releases?.flatMap(
    (rel: { release_id: string; name: string; artifacts: unknown[] }) =>
      (rel.artifacts || []).map((art) => ({ ...art, release_name: rel.name }))
  ) ?? [];

  const hasSbomCount = allArtifacts.filter((a: { has_sbom: boolean }) => a.has_sbom).length;
  const hasProvCount = allArtifacts.filter((a: { has_provenance: boolean }) => a.has_provenance).length;
  const hasSigCount = allArtifacts.filter((a: { has_signature: boolean }) => a.has_signature).length;
  const criticalTotal = allArtifacts.reduce(
    (sum: number, a: { critical_vulns: number }) => sum + (a.critical_vulns || 0),
    0
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Supply Chain Integrity</h1>
        <p className="text-slate-400 mt-1">
          SBOM coverage, provenance verification, and vulnerability posture for {allArtifacts.length}{" "}
          artifact{allArtifacts.length !== 1 ? "s" : ""}.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 uppercase tracking-wider mb-2">SBOM Coverage</div>
          <div className="text-2xl font-bold text-white">
            {allArtifacts.length > 0
              ? `${Math.round((hasSbomCount / allArtifacts.length) * 100)}%`
              : "—"}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {hasSbomCount}/{allArtifacts.length} artifacts
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 uppercase tracking-wider mb-2">Provenance</div>
          <div className="text-2xl font-bold text-white">
            {allArtifacts.length > 0
              ? `${Math.round((hasProvCount / allArtifacts.length) * 100)}%`
              : "—"}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {hasProvCount}/{allArtifacts.length} artifacts
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-xs text-slate-400 uppercase tracking-wider mb-2">Signatures</div>
          <div className="text-2xl font-bold text-white">
            {allArtifacts.length > 0
              ? `${Math.round((hasSigCount / allArtifacts.length) * 100)}%`
              : "—"}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {hasSigCount}/{allArtifacts.length} signed
          </div>
        </div>
        <div
          className={`border rounded-xl p-4 ${
            criticalTotal > 0
              ? "bg-red-900/20 border-red-700/40"
              : "bg-slate-900 border-slate-800"
          }`}
        >
          <div className="text-xs text-slate-400 uppercase tracking-wider mb-2">Critical CVEs</div>
          <div
            className={`text-2xl font-bold ${criticalTotal > 0 ? "text-red-400" : "text-white"}`}
          >
            {criticalTotal}
          </div>
          <div className="text-xs text-slate-500 mt-1">Across all artifacts</div>
        </div>
      </div>

      {/* Artifact table */}
      {allArtifacts.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-800">
            <span className="text-sm font-medium text-slate-300">Artifacts</span>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="text-left px-4 py-2 text-slate-400">Artifact</th>
                <th className="text-left px-4 py-2 text-slate-400">Version</th>
                <th className="text-left px-4 py-2 text-slate-400">SBOM</th>
                <th className="text-left px-4 py-2 text-slate-400">Provenance</th>
                <th className="text-left px-4 py-2 text-slate-400">Signed</th>
                <th className="text-left px-4 py-2 text-slate-400">Critical CVEs</th>
                <th className="text-left px-4 py-2 text-slate-400">High CVEs</th>
              </tr>
            </thead>
            <tbody>
              {allArtifacts.map(
                (art: {
                  artifact_id: string;
                  name: string;
                  version: string;
                  artifact_type: string;
                  has_sbom: boolean;
                  has_provenance: boolean;
                  has_signature: boolean;
                  critical_vulns: number;
                  high_vulns: number;
                  release_name: string;
                }) => (
                  <tr
                    key={art.artifact_id}
                    className="border-b border-slate-800/50 hover:bg-slate-800/20"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Package size={14} className="text-slate-400 shrink-0" />
                        <div>
                          <div className="text-white">{art.name}</div>
                          <div className="text-xs text-slate-500">{art.release_name}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-xs">{art.version}</td>
                    <td className="px-4 py-3">
                      {art.has_sbom ? (
                        <CheckCircle size={14} className="text-emerald-400" />
                      ) : (
                        <XCircle size={14} className="text-red-400" />
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {art.has_provenance ? (
                        <CheckCircle size={14} className="text-emerald-400" />
                      ) : (
                        <XCircle size={14} className="text-red-400" />
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {art.has_signature ? (
                        <CheckCircle size={14} className="text-emerald-400" />
                      ) : (
                        <XCircle size={14} className="text-red-400" />
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={art.critical_vulns > 0 ? "text-red-400 font-medium" : "text-slate-400"}
                      >
                        {art.critical_vulns}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={art.high_vulns > 3 ? "text-amber-400 font-medium" : "text-slate-400"}
                      >
                        {art.high_vulns}
                      </span>
                    </td>
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>
      )}

      {allArtifacts.length === 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-400 text-sm">
          No build artifacts found. Create a release with artifacts to see supply chain data.
        </div>
      )}
    </div>
  );
}
