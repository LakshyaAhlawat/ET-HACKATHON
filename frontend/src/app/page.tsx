import Link from "next/link";

const MODULES = [
  {
    href: "/compliance",
    title: "Compliance Verifier",
    description: "Spec vs. vendor submittal, deviation-flagged, with source highlighting.",
  },
  {
    href: "/cascade",
    title: "Cascade Simulator",
    description: "Critical-path delay propagation with Monte Carlo handover projections.",
  },
  {
    href: "/sld",
    title: "SLD Redundancy Analyser",
    description: "Computer vision on single-line diagrams to verify 2N redundancy.",
  },
  {
    href: "/graph",
    title: "Knowledge Graph",
    description: "Spec → Equipment → Vendor → Shipment → Task, traced into the real schedule.",
  },
];

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-8 px-6 py-16">
      <div>
        <h1 className="text-3xl font-semibold">EPC Project Intelligence</h1>
        <p className="mt-2 text-neutral-500">
          Data centre EPC project intelligence — compliance, schedule risk, and electrical
          redundancy, verified deterministically.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-1">
        {MODULES.map((m) => (
          <Link
            key={m.href}
            href={m.href}
            className="rounded-lg border border-neutral-200 p-5 transition hover:border-neutral-400 dark:border-neutral-800 dark:hover:border-neutral-600"
          >
            <h2 className="font-medium">{m.title}</h2>
            <p className="mt-1 text-sm text-neutral-500">{m.description}</p>
          </Link>
        ))}
      </div>
    </main>
  );
}
