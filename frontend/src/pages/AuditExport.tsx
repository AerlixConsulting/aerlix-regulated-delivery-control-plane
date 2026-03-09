import { useState } from "react";
import axios from "axios";
import { FileDown, Loader2 } from "lucide-react";

const API = "/api/v1";

export default function AuditExport() {
  const [loading, setLoading] = useState(false);
  const [format, setFormat] = useState<"json" | "markdown">("json");
  const [releaseId, setReleaseId] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ format });
      if (releaseId) params.set("release_id", releaseId);

      const response = await axios.post(`${API}/audit/generate?${params}`, {}, {
        responseType: "blob",
      });

      const ext = format === "markdown" ? "md" : "json";
      const url = URL.createObjectURL(new Blob([response.data]));
      const a = document.createElement("a");
      a.href = url;
      a.download = `aerlix-audit-bundle.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError("Failed to generate audit bundle. Ensure the API server is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Audit Export</h1>
        <p className="text-slate-400 mt-1">
          Generate a comprehensive audit package including controls, evidence, traceability matrix,
          and exception register.
        </p>
      </div>

      {/* Export form */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-5">
        <h2 className="text-base font-medium text-white">Generate Audit Bundle</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Release ID (optional)</label>
            <input
              type="text"
              value={releaseId}
              onChange={(e) => setReleaseId(e.target.value)}
              placeholder="e.g. REL-001"
              className="w-full max-w-xs bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
            <p className="text-xs text-slate-500 mt-1">
              If provided, the bundle will include release-specific data.
            </p>
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Format</label>
            <div className="flex gap-3">
              {(["json", "markdown"] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFormat(f)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    format === f
                      ? "bg-blue-600 text-white"
                      : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                  }`}
                >
                  {f === "json" ? "JSON" : "Markdown"}
                </button>
              ))}
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-900/20 border border-red-700/40 rounded-lg px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

        <button
          onClick={handleExport}
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <FileDown size={14} />}
          {loading ? "Generating..." : "Download Audit Bundle"}
        </button>
      </div>

      {/* What's included */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">
          Bundle Contents
        </h2>
        <ul className="space-y-2 text-sm text-slate-300">
          {[
            "Control summary with implementation status and counts",
            "Evidence index organized by type and status",
            "Traceability matrix (requirements → controls → evidence)",
            "Release readiness report with policy evaluation",
            "Gap analysis (untested reqs, controls without evidence)",
            "Exception register with approval and expiration data",
            "Incident summary with severity breakdown",
          ].map((item) => (
            <li key={item} className="flex items-start gap-2">
              <span className="text-blue-400 mt-0.5">•</span>
              {item}
            </li>
          ))}
        </ul>
      </div>

      {/* CLI hint */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-5">
        <div className="text-sm font-medium text-slate-300 mb-2">CLI equivalent</div>
        <pre className="text-xs text-slate-400 bg-slate-900 p-3 rounded-lg overflow-x-auto">
          {`aerlix generate-audit-bundle --release-id REL-001 --format json --output /tmp/audit.json`}
        </pre>
      </div>
    </div>
  );
}
