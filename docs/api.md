# HTTP API

`forgefix serve` (or `uvicorn forgefix.server:app`) exposes the same checks over HTTP.
Binds `127.0.0.1:8000` by default; do not expose to untrusted networks.

## `GET /health`

```json
{"status": "ok", "version": "0.1.0"}
```

## `GET /doctor?path=.`

Scans `path` (default: current directory) and returns findings + score.

```json
{
  "path": "/abs/path/to/repo",
  "score": {
    "total": 42,
    "passed": 0, "warned": 5, "failed": 6, "skipped": 0,
    "deductions": 58,
    "breakdown": {"automation": 8, "deps": 5, "docs": 20, "environment": 7,
                   "legal": 6, "polish": 1, "security": 8},
    "top_fixes": [["README present", "Add a README.md ...", 12]]
  },
  "findings": [
    {
      "rule_id": "readme", "category": "docs", "title": "README present",
      "status": "fail", "detail": "no README at the repository root",
      "suggestion": "Add a README.md ...", "weight": 12, "warn_weight": 6,
      "source": "builtin"
    }
  ],
  "plugins": ["example"]
}
```

## `GET /report?path=.`

```json
{"path": "/abs/path/to/repo", "score": 42, "markdown": "# ForgeFix health report\n..."}
```

## Errors

`400` with `{"detail": "not a directory: <path>"}` when `path` cannot be scanned.

```bash
curl "http://127.0.0.1:8000/doctor?path=../some-repo" | jq .score.total
```
