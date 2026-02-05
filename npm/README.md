# 🛡 Hallucination Guard — Node.js / TypeScript SDK

Detect hallucinations in AI-generated text from any JavaScript or TypeScript project.

## Install

```bash
npm install hallucination-guard
# or
yarn add hallucination-guard
# or
pnpm add hallucination-guard
```

**Prerequisite:** The Python engine must be installed:

```bash
pip install hallucination-guard
python -m spacy download en_core_web_sm
```

## CLI Usage

```bash
npx hallucination-guard check "The Eiffel Tower is in Berlin."
npx hallucination-guard check "Some text" --json
npx hallucination-guard file article.txt
npx hallucination-guard batch inputs.json
```

## SDK Usage (TypeScript / JavaScript)

```typescript
import { detect, score, explain } from 'hallucination-guard';

// Full detection
const result = await detect("The Eiffel Tower is in Berlin.");
console.log(result.hallucinated);       // true
console.log(result.hallucination_risk); // 0.72
console.log(result.flagged_claims);     // [{claim: "...", confidence: 0.18}]
console.log(result.highlighted_text);   // "⚠[The Eiffel Tower …]⚠"

// Quick risk score
const risk = await score("The moon is made of cheese.");
console.log(risk); // 0.68

// Structured explanation
const info = await explain("Mars is the largest planet.");
console.log(info.hallucinated); // true
console.log(info.claims);       // [{claim: "...", severity: "high"}]
```

### API Mode

If you have the API server running, you can use API mode instead of CLI mode:

```bash
# Start the server
hallucination-guard api --port 8000
```

```typescript
import { detect } from 'hallucination-guard';

const result = await detect("Some text", {
  mode: "api",
  apiUrl: "http://localhost:8000",
});
```

## Types

Full TypeScript types are included:

```typescript
interface DetectionResult {
  hallucinated: boolean;
  hallucination_risk: number;
  confidence: number;
  total_claims: number;
  supported_claims: number;
  unsupported_claims: number;
  flagged_claims: FlaggedClaim[];
  explanations: Explanation[];
  highlighted_text: string;
  explanation: string;
}
```

## License

MIT
