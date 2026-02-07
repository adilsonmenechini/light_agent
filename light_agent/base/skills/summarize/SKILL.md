---
name: summarize
description: Summarize or extract text/transcripts from URLs, podcasts, and local files.
---

# Summarize

Fast CLI to summarize URLs, local files, and YouTube links.

## Quick start

```bash
summarize "https://example.com"
summarize "/path/to/file.pdf"
summarize "https://youtu.be/dQw4w9WgXcQ" --youtube auto
```

## Useful flags
- `--length short|medium|long`
- `--extract-only` (URLs only)
- `--json` (machine readable)
