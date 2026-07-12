import { ComplianceViewer } from "@/components/compliance/ComplianceViewer";
import type { Verdict } from "@/lib/types";

// Server-side fetch target. Distinct from NEXT_PUBLIC_API_URL (used by the
// browser) because inside Docker this page fetches from the backend
// container over the internal network (http://backend:8000), not localhost.
const API_INTERNAL_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
const SUBMITTAL_ID = "submittal";

async function fetchVerdicts(): Promise<Verdict[]> {
  const res = await fetch(`${API_INTERNAL_URL}/api/verify/${SUBMITTAL_ID}`, {
    method: "POST",
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Verify API failed: ${res.status} ${await res.text()}`);
  }
  return res.json();
}

export default async function CompliancePage() {
  let verdicts: Verdict[] = [];
  let error: string | null = null;

  try {
    verdicts = await fetchVerdicts();
  } catch (err) {
    error = err instanceof Error ? err.message : "Unknown error";
  }

  if (error || verdicts.length === 0) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6 text-center">
        <p className="font-mono text-sm text-deviation">
          {error ?? "No verdicts returned."}
        </p>
      </main>
    );
  }

  // Surface a real deviation over a passing requirement when both exist.
  const verdict = verdicts.find((v) => v.status === "NON_CONFORMANCE") ?? verdicts[0];

  return (
    <main className="min-h-screen">
      <header className="border-b border-neutral-800 px-6 py-4">
        <h1 className="text-lg font-semibold">Compliance Verifier</h1>
        <p className="font-mono text-xs text-neutral-500">
          spec.pdf vs submittal.pdf — {verdict.req_id} ({verdicts.length} requirement
          {verdicts.length === 1 ? "" : "s"} checked)
        </p>
      </header>
      <ComplianceViewer verdict={verdict} />
    </main>
  );
}
