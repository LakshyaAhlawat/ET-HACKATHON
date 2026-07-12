// Copies the pdf.js worker into public/ as a plain static asset so Next.js's
// webpack build never tries to bundle/minify it (Terser chokes on the
// worker's own `import.meta` usage — see react-pdf's SSR/build docs).
// Runs on `npm install` via the "postinstall" script so it always matches
// the installed pdfjs-dist version.
import { copyFileSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

const require = createRequire(import.meta.url);
const workerPath = require.resolve("pdfjs-dist/build/pdf.worker.min.mjs");
const destPath = path.join(process.cwd(), "public", "pdf.worker.min.mjs");

copyFileSync(workerPath, destPath);
console.log(`Copied pdf.worker.min.mjs -> ${destPath}`);
