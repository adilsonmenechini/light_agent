---
name: github-pr-review
description: "Comprehensive PR review workflow. Analyzes changes, reviews code, and manages review feedback loop."
---

# GitHub PR Review Workflow

Complete workflow for reviewing pull requests effectively.

## Step 1: Get PR Information

```bash
# Get PR details
gh pr view 55 --json title,body,state,author,additions,deletions,changedFiles

# Get PR commits
gh pr view 55 --json commits

# Get changed files
gh pr diff 55 --stat

# Check CI/CD status
gh pr checks 55
```

## Step 2: Checkout and Review Locally

```bash
# Checkout PR to review
gh pr checkout 55

# View changes in IDE
git diff main...HEAD

# Check specific file changes
git diff HEAD -- path/to/file.py
```

## Step 3: Automated Code Analysis

```bash
# List modified files with stats
gh pr diff 55 --stat

# Get file content before changes
gh api repos/owner/repo/pulls/55/files --jq '.[].before_filename'

# View specific file changes in PR
gh api repos/owner/repo/pulls/55/files --jq '.[].filename, .[].patch'
```

## Step 4: Run CI Checks

```bash
# Check all CI statuses
gh pr checks 55 --repo owner/repo

# View failed check details
gh run view RUN_ID --repo owner/repo

# Get check run details
gh api repos/owner/repo/check-runs/CHECK_RUN_ID --jq '.name, .conclusion, .output'
```

## Step 5: Submit Review

### Comment on specific lines
```bash
# Create a review comment via API
gh api repos/owner/repo/pulls/55/comments \
  -X POST \
  -f body="Consider using a constant here" \
  -f commit_id=$(gh api repos/owner/repo/pulls/55 --jq '.head.sha') \
  -f path="src/app.py" \
  -f line=42
```

### Submit review decision
```bash
# Approve PR
gh pr review 55 --approve --body "LGTM, thanks!"

# Request changes
gh pr review 55 --request-changes --body "Please fix the following issues..."

# Comment without decision
gh pr review 55 --comment --body "General feedback..."
```

## Step 6: Track Review Changes

```bash
# List all review comments
gh api repos/owner/repo/pulls/55/comments --jq '.[].body,.[].user.login'

# Check if PR has new commits since review
gh pr view 55 --json commits

# View changes requested in review
gh api repos/owner/repo/issues/55/comments -f "body~=Changes" --jq '.[].body'
```

## Review Checklist

Before approving, verify:

- [ ] **Tests pass**: CI checks are green
- [ ] **Code style**: Follows project conventions
- [ ] **Documentation**: Updated if needed
- [ ] **No secrets**: No API keys or passwords
- [ ] **Error handling**: Proper error cases handled
- [ ] **Security**: No vulnerabilities introduced
- [ ] **Performance**: No obvious regressions
- [ ] **Complexity**: Code is readable and maintainable

## Common Review Comments

```bash
# Suggestion pattern
gh api repos/owner/repo/pulls/55/comments \
  -X POST \
  -f body="💡 Consider using `pathlib` for file operations instead of `os.path`" \
  -f commit_id=SHA \
  -f path="src/utils.py" \
  -f line=15 \
  -f side=RIGHT

# Bug report pattern  
gh api repos/owner/repo/pulls/55/comments \
  -X POST \
  -f body="⚠️ This change may cause a null pointer exception if `config` is None" \
  -f commit_id=SHA \
  -f path="src/main.py" \
  -f line=42 \
  -f side=RIGHT
```

## Review Metrics

```bash
# Get PR size metrics
gh pr view 55 --json additions,deletions,changedFiles

# Calculate review time
gh api repos/owner/repo/pulls/55 --jq '.created_at, .updated_at'

# Count review comments
gh api repos/owner/repo/pulls/55/comments --jq 'length'
```
