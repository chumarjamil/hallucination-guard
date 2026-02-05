# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public issue
2. Email: [security@hallucination-guard.dev](mailto:security@hallucination-guard.dev)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and provide a fix timeline.

## Security Considerations

- **API Key Auth**: Set `HALLUCINATION_GUARD_API_KEY` env var to enable API authentication
- **Rate Limiting**: Default 60 requests/minute per IP (configurable via `HALLUCINATION_GUARD_RATE_LIMIT`)
- **No data persistence**: The API server does not store or log input texts by default
- **Local processing**: All NLP models run locally — no data sent to external APIs
