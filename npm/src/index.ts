/**
 * Hallucination Guard — Node.js / TypeScript SDK
 *
 * Detect hallucinations in AI-generated text from any JS/TS project.
 *
 * Usage:
 *   import { detect, score, explain } from 'hallucination-guard';
 *
 *   const result = await detect("The Eiffel Tower is in Berlin.");
 *   console.log(result.hallucinated);  // true
 *   console.log(result.confidence);    // 0.91
 */

import { execFile } from "child_process";
import { promisify } from "util";

const execFileAsync = promisify(execFile);

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface FlaggedClaim {
  claim: string;
  confidence: number;
  evidence: string;
  source: string | null;
}

export interface Explanation {
  claim: string;
  hallucinated: boolean;
  confidence: number;
  explanation: string;
  severity: "low" | "medium" | "high";
  source: string | null;
}

export interface DetectionResult {
  hallucinated: boolean;
  hallucination_risk: number;
  confidence: number;
  total_claims: number;
  supported_claims: number;
  unsupported_claims: number;
  average_similarity: number;
  flagged_claims: FlaggedClaim[];
  explanations: Explanation[];
  highlighted_text: string;
  explanation: string;
}

export interface ScoreResult {
  risk: number;
}

export interface ExplainResult {
  hallucinated: boolean;
  confidence: number;
  explanation: string;
  claims: Explanation[];
}

export interface GuardOptions {
  /** URL of a running Hallucination Guard API server */
  apiUrl?: string;
  /** Use CLI mode instead of API (no server needed) */
  mode?: "api" | "cli";
}

// ---------------------------------------------------------------------------
// CLI mode — calls the Python CLI with --json
// ---------------------------------------------------------------------------

async function runCli(text: string): Promise<DetectionResult> {
  try {
    const { stdout } = await execFileAsync(
      "hallucination-guard",
      ["check", text, "--json"],
      { maxBuffer: 10 * 1024 * 1024, timeout: 120_000 }
    );
    return JSON.parse(stdout.trim());
  } catch (err: any) {
    if (err.code === "ENOENT") {
      throw new Error(
        "hallucination-guard CLI not found. Install it:\n" +
          "  pip install hallucination-guard\n" +
          "  python -m spacy download en_core_web_sm"
      );
    }
    throw new Error(`hallucination-guard CLI failed: ${err.message}`);
  }
}

// ---------------------------------------------------------------------------
// API mode — calls the REST API
// ---------------------------------------------------------------------------

async function runApi(
  text: string,
  baseUrl: string
): Promise<DetectionResult> {
  const url = `${baseUrl}/detect`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }

  return (await res.json()) as DetectionResult;
}

// ---------------------------------------------------------------------------
// Resolver — picks CLI or API based on options
// ---------------------------------------------------------------------------

const DEFAULT_API_URL = "http://localhost:8000";

async function run(
  text: string,
  opts?: GuardOptions
): Promise<DetectionResult> {
  const mode = opts?.mode ?? "cli";
  if (mode === "api") {
    return runApi(text, opts?.apiUrl ?? DEFAULT_API_URL);
  }
  return runCli(text);
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Run full hallucination detection on a text string.
 *
 * @example
 * ```ts
 * const result = await detect("Paris is the capital of Germany.");
 * console.log(result.hallucinated);       // true
 * console.log(result.hallucination_risk); // 0.72
 * console.log(result.flagged_claims);     // [...]
 * ```
 */
export async function detect(
  text: string,
  opts?: GuardOptions
): Promise<DetectionResult> {
  return run(text, opts);
}

/**
 * Get just the hallucination risk score (0.0 – 1.0).
 *
 * @example
 * ```ts
 * const risk = await score("The moon is made of cheese.");
 * console.log(risk); // 0.68
 * ```
 */
export async function score(
  text: string,
  opts?: GuardOptions
): Promise<number> {
  const result = await run(text, opts);
  return result.hallucination_risk;
}

/**
 * Get a structured explanation with per-claim details.
 *
 * @example
 * ```ts
 * const info = await explain("Mars is the largest planet.");
 * console.log(info.hallucinated); // true
 * console.log(info.claims);       // [{claim: "...", severity: "high", ...}]
 * ```
 */
export async function explain(
  text: string,
  opts?: GuardOptions
): Promise<ExplainResult> {
  const result = await run(text, opts);
  return {
    hallucinated: result.hallucinated,
    confidence: result.confidence,
    explanation: result.explanation,
    claims: result.explanations,
  };
}

/**
 * Check if the Hallucination Guard CLI is installed and accessible.
 */
export async function isInstalled(): Promise<boolean> {
  try {
    await execFileAsync("hallucination-guard", ["version"], { timeout: 5000 });
    return true;
  } catch {
    return false;
  }
}

export default { detect, score, explain, isInstalled };
