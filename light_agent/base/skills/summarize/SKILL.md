---
name: summarize
description: Summarize or extract text/transcripts from URLs, podcasts, local files, and YouTube videos.
---

# Summarize Skill

Fast CLI tool to extract and summarize content from various sources.

## Quick Start

```bash
# Summarize a webpage
summarize "https://example.com/article"

# Summarize local file (PDF, TXT, MD)
summarize "/path/to/document.pdf"
summarize "/path/to/readme.md"

# Summarize YouTube video
summarize "https://youtu.be/dQw4w9WgXcQ"

# Extract transcript only (podcasts, YouTube)
summarize "https://youtu.be/video-id" --extract-only
```

## Output Length Control

```bash
# Short summary (1-2 paragraphs)
summarize "https://example.com" --length short

# Medium summary (3-5 paragraphs)
summarize "https://example.com" --length medium

# Long summary (detailed, multiple pages)
summarize "https://example.com" --length long
```

## Output Formats

```bash
# Human-readable text (default)
summarize "https://example.com"

# Machine-readable JSON
summarize "https://example.com" --json
# Output: {"summary": "...", "key_points": [...], "source": "..."}

# Extract-only (no summarization)
summarize "https://example.com" --extract-only
```

## Common Use Cases

### Research / Documentation
```bash
# Summarize technical documentation
summarize "https://docs.example.com/api-guide" --length medium

# Extract key points from blog posts
summarize "https://engineering.example.com/post" --length short
```

### Meeting Notes / Transcripts
```bash
# Summarize podcast episode
summarize "https://podcast.example.com/ep123" --length long

# Extract action items from meeting transcript
summarize "/notes/meeting.txt" --length short
```

### Code Review / Specs
```bash
# Summarize RFC/ADR document
summarize "/docs/ADR-001.md" --length medium

# Extract key decisions from design doc
summarize "https://github.com/org/repo/pull/123" --extract-only
```

## Best Practices

1. **Use `--extract-only`** for sources you want to parse yourself
2. **Use `--json`** when feeding into other tools
3. **Use `--length long`** for technical documentation you need to understand deeply
4. **Use `--length short`** for news/blog posts where you just want the gist

## Limitations

- May not work with paywalled content
- PDF extraction quality varies by source
- YouTube summaries work best with auto-generated transcripts
