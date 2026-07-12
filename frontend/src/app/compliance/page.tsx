import { ComplianceViewer } from "@/components/compliance/ComplianceViewer";
import type { Verdict } from "@/lib/types";

import verdictSample from "../../../../data/fixtures/verdict_sample.json";

export default function CompliancePage() {
  const verdict = verdictSample as unknown as Verdict;

  return (
    <main className="min-h-screen">
      <header className="border-b border-neutral-800 px-6 py-4">
        <h1 className="text-lg font-semibold">Compliance Verifier</h1>
        <p className="font-mono text-xs text-neutral-500">
          spec.pdf vs submittal.pdf — {verdict.req_id}
        </p>
      </header>
      <ComplianceViewer verdict={verdict} extractionConfidence={verdictSample.extraction_confidence} />
    </main>
  );
}
