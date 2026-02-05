#!/usr/bin/env node

/**
 * Hallucination Guard CLI (Node.js wrapper)
 *
 * This forwards commands to the Python CLI.
 * Requires: pip install hallucination-guard
 *
 * Usage:
 *   npx hallucination-guard check "The Eiffel Tower is in Berlin."
 *   npx hallucination-guard check "text" --json
 */

const { execFileSync, execSync } = require("child_process");

const args = process.argv.slice(2);

if (args.length === 0 || args[0] === "--help" || args[0] === "-h") {
  console.log(`
🛡  Hallucination Guard

Detect hallucinations in AI-generated text.

Commands:
  check <text>           Check text for hallucinations
  check <text> --json    Output as JSON
  file <path>            Check a text file
  batch <path.json>      Batch-check texts from JSON
  api [--port 8000]      Start REST API server
  version                Show version

Options:
  --json, -j      Output as JSON
  --verbose, -v   Verbose logging

Examples:
  npx hallucination-guard check "The Eiffel Tower is in Berlin."
  npx hallucination-guard file article.txt
  npx hallucination-guard check "Some text" --json

Requirements:
  pip install hallucination-guard
  python -m spacy download en_core_web_sm
`);
  process.exit(0);
}

// Check if Python CLI is installed
try {
  execFileSync("hallucination-guard", ["version"], {
    stdio: "pipe",
    timeout: 5000,
  });
} catch (err) {
  console.error("❌ hallucination-guard Python package not found.\n");
  console.error("Install it:");
  console.error("  pip install hallucination-guard");
  console.error("  python -m spacy download en_core_web_sm\n");
  process.exit(1);
}

// Forward all arguments to the Python CLI
try {
  execFileSync("hallucination-guard", args, {
    stdio: "inherit",
    timeout: 120_000,
  });
} catch (err) {
  if (err.status) {
    process.exit(err.status);
  }
  process.exit(1);
}
