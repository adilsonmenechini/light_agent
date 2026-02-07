# Librarian and External Resources Tools

Light Agent provides powerful tools for researching external documentation, code examples, and patterns from open source repositories.

## Overview

| Tool | Purpose | Best For |
|------|---------|----------|
| `codesearch` | Code examples & patterns | Production code patterns, real-world usage |
| `context7_resolve-library-id` | Library identification | Find Context7 ID for official docs |
| `context7_query-docs` | Official documentation | API references, framework docs |
| `librarian` (via delegate_task) | Multi-repository research | Complex research across sources |

---

## 1. CodeSearch - Real-World Code Examples

Search millions of open source repositories for production-ready code patterns.

### Usage

```typescript
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "getServerSession auth Next.js App Router"
})
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Literal code pattern (e.g., `useState(`, `export function`) |
| `language` | string[] | Filter by language (e.g., `["TypeScript", "TSX"]`) |
| `repo` | string | Filter by repository (e.g., `"facebook/react"`) |
| `path` | string | Filter by file path |
| `useRegexp` | boolean | Enable regex patterns |
| `matchCase` | boolean | Case-sensitive search |
| `matchWholeWords` | boolean | Match whole words only |

### Examples

```typescript
// React hooks patterns
grep_app_searchGitHub({
  language: ["TypeScript", "TSX"],
  query: "useState($$$)"
})

// Error boundary patterns
grep_app_searchGitHub({
  language: ["TSX"],
  query: "ErrorBoundary"
})

// Express middleware
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "app.use($$$)"
})

// Async/await error handling
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "(?s)try {.*await",
  useRegexp: true
})
```

### Best Practices

- Use **literal code** in queries, not keywords
- Filter by `language` to reduce noise
- Use `path` to target specific directories
- For multi-line patterns, enable `useRegexp: true` with `(?s)` prefix

---

## 2. Context7 - Official Documentation

Get up-to-date documentation and code examples from official library/framework sources.

### Step 1: Resolve Library ID

```typescript
context7_resolve-library-id({
  libraryName: "react",
  query: "How to use React hooks in TypeScript"
})
```

Returns a Context7-compatible library ID like `/facebook/react` or `/vercel/next.js`.

### Step 2: Query Documentation

```typescript
context7_query-docs({
  libraryId: "/facebook/react",
  query: "React useEffect hook examples with TypeScript"
})
```

### Parameters

| Tool | Parameter | Description |
|------|-----------|-------------|
| `resolve-library-id` | `libraryName` | Package/library name to search |
| `resolve-library-id` | `query` | What you're trying to accomplish |
| `query-docs` | `libraryId` | Exact ID from step 1 |
| `query-docs` | `query` | Specific question or task |

### Examples

```typescript
// React
context7_resolve-library-id({
  libraryName: "react",
  query: "React useState hook patterns"
})
// Returns: /facebook/react

context7_query-docs({
  libraryId: "/facebook/react",
  query: "How to use useEffect cleanup function"
})

// Next.js
context7_resolve-library-id({
  libraryName: "next.js",
  query: "App Router authentication patterns"
})

context7_query-docs({
  libraryId: "/vercel/next.js",
  query: "Server Actions with TypeScript"
})

// Supabase
context7_resolve-library-id({
  libraryName: "supabase",
  query: "Client initialization and auth"
})
```

### Supported Libraries

Popular frameworks and libraries are indexed:
- React, Next.js, Vue, Angular
- Express, Fastify, NestJS
- Prisma, Drizzle, SQLAlchemy
- TensorFlow, PyTorch
- And hundreds more...

---

## 3. Librarian Agent - Specialized Research

The `librarian` agent handles complex, multi-source research tasks.

### Usage

```typescript
delegate_task({
  subagent_type: "librarian",
  description: "Find auth patterns",
  prompt: "Find official Next.js documentation and examples for implementing authentication. I need to understand the App Router auth patterns.",
  load_skills: [],
  run_in_background: false
})
```

### When to Use

| Scenario | Action |
|----------|--------|
| Unfamiliar library | Librarian FIRST |
| Need examples from multiple repos | Librarian |
| Compare approaches across libraries | Librarian |
| Implementation strategies | Librarian + Context7 |
| Simple API lookup | Context7 only |

### Librarian vs Context7

| Aspect | Librarian | Context7 |
|--------|-----------|----------|
| Scope | Multi-repository | Single official docs |
| Depth | Broad research | Focused API lookup |
| Speed | Slower | Fast |
| Cost | Higher | Lower |
| Best for | Strategy, patterns | Specific API usage |

### Example Prompts

```typescript
// Implementation strategy
delegate_task({
  subagent_type: "librarian",
  description: "JWT auth best practices",
  prompt: "I'm implementing JWT-based authentication in an Express API. Find production-quality patterns for token expiration, refresh strategies, and common vulnerabilities to avoid. Include examples of middleware structure.",
  load_skills: [],
  run_in_background: false
})

// Framework comparison
delegate_task({
  subagent_type: "librarian",
  description: "Compare auth solutions",
  prompt: "Compare authentication solutions for a Next.js 14 app: NextAuth.js, Clerk, and Supabase Auth. What are the tradeoffs, pricing, and migration patterns?",
  load_skills: [],
  run_in_background: false
})
```

---

## Decision Tree

```
Need external documentation?
│
├─► Simple API question?
│   └─► Context7 (resolve → query)
│
├─► Real code examples?
│   └─► codesearch
│
├─► Multi-source research?
│   └─► librarian (delegate_task)
│
└─► Security/performance concerns?
    └─► Librarian + Oracle consultation
```

---

## Quick Reference

### For Documentation
```typescript
// 1. Find library ID
context7_resolve-library-id({ libraryName: "express", query: "middleware auth" })
// 2. Query docs
context7_query-docs({ libraryId: "/expressjs/express", query: "Custom middleware examples" })
```

### For Code Patterns
```typescript
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "express middleware auth"
})
```

### For Complex Research
```typescript
delegate_task({
  subagent_type: "librarian",
  description: "Research topic",
  prompt: "Research [topic] across official docs and GitHub examples. Summarize best practices and common patterns.",
  load_skills: [],
  run_in_background: false
})
```
