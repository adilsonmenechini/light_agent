# CodeSearch Skill

Production-ready code patterns from open source repositories.

## Overview

Use `grep_app_searchGitHub` to find real-world examples of:
- Framework patterns and best practices
- Common implementation approaches
- Anti-patterns to avoid
- Edge case handling

## Usage Guidelines

### When to Use

| Scenario | Action |
|----------|--------|
| Implementing unfamiliar API | Search for usage patterns |
| Understanding framework idioms | Search for established repos |
| Best practices verification | Compare multiple implementations |
| Error handling approaches | Find production-grade error handling |

### Query Best Practices

**DO:**
- Use literal code patterns: `useState(`, `app.use(`
- Filter by language: `language: ["TypeScript"]`
- Target specific paths: `path: "src/components"`
- Use regex for complex patterns with `(?s)` prefix

**DON'T:**
- Search for concepts ("auth patterns")
- Use generic queries without filters
- Skip version/language context

## Code Pattern Library

### React Hooks

```typescript
// useState with types
grep_app_searchGitHub({
  language: ["TypeScript", "TSX"],
  query: "useState<$$$>"
})

// useEffect cleanup
grep_app_searchGitHub({
  language: ["TypeScript", "TSX"],
  query: "(?s)useEffect\\(\\(\\) => {.*return.*}"
})

// Custom hooks
grep_app_searchGitHub({
  language: ["TypeScript", "TSX"],
  query: "function use[A-Z]"
})
```

### Express/Fastify Middleware

```typescript
// Auth middleware
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "app.use($$$auth$$$)"
})

// Error handling middleware
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "app.use\\(err,"
})

// Request validation
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "zod|joi|yup"
})
```

### Database Patterns

```typescript
// Prisma transaction
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "prisma\\.$transaction"
})

// Connection pooling
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "Pool|pg\\.Pool"
})

// Drizzle queries
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "drizzle\\."
})
```

### Authentication

```typescript
// JWT verification
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "jwt\\.verify|jsonwebtoken"
})

// Session management
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "getServerSession"
})

// OAuth flow
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "OAuth2Client|google.auth"
})
```

### Testing Patterns

```typescript
// Vitest setup
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "vi\\.mock|vi\\.fn"
})

// React Testing Library
grep_app_searchGitHub({
  language: ["TypeScript", "TSX"],
  query: "render\\(<.*/>\\)"
})

// MSW handlers
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "rest\\.|http\\."
})
```

### TypeScript Patterns

```typescript
// Generic constraints
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "extends \\w+"
})

// Discriminated unions
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "kind: 'success'|'error'"
})

// Utility types
grep_app_searchGitHub({
  language: ["TypeScript"],
  query: "Partial<|Required<|Omit<"
})
```

## Pattern Analysis Framework

When analyzing results:

1. **Frequency** - How common is this pattern?
2. **Repository Quality** - Star count, maintenance activity
3. **Edge Cases** - Error handling, null checks
4. **Type Safety** - TypeScript usage, type annotations
5. **Performance** - Memoization, lazy loading
6. **Security** - Input validation, sanitization

## Output Format

For each pattern found, document:

```markdown
## Pattern: [Name]

**Purpose:** What problem does this solve?

**Found in:**
- [Repo 1](url) - [stars] stars
- [Repo 2](url) - [stars] stars

**Typical Implementation:**
```typescript
// Example code
```

**Key Characteristics:**
- Characteristic 1
- Characteristic 2

**Considerations:**
- Warning or caveat
- Alternative approaches
```
