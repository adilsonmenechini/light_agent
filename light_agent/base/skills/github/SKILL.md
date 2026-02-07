---
name: github
description: "Comprehensive GitHub operations using the `gh` CLI. Supports issues, PRs, releases, security advisories, and API queries."
---

# GitHub Skill

Use the `gh` CLI to interact with GitHub repositories. Always specify `--repo owner/repo` when not in a git directory, or use URLs directly.

## Authentication

```bash
# Authenticate with GitHub
gh auth login

# Check authentication status
gh auth status

# Refresh authentication token
gh auth refresh
```

## Pull Requests

### Viewing PRs
```bash
# List open PRs in current repo
gh pr list

# List PRs with specific state
gh pr list --state all
gh pr list --state closed

# View PR details
gh pr view 55

# View PR diff
gh pr diff 55

# View PR checks (CI status)
gh pr checks 55 --repo owner/repo
```

### Creating PRs
```bash
# Create PR from current branch
gh pr create --title "Fix authentication bug" --body "Description here"

# Create PR with specific base branch
gh pr create --base main --head my-branch

# Create PR and assign reviewers
gh pr create --reviewer user1,user2

# Create draft PR
gh pr create --draft

# Create PR from commit
gh pr create --title "Update" --body "From commit" --head SHA
```

### Managing PRs
```bash
# Checkout PR locally
gh pr checkout 55

# Add reviewers to PR
gh pr edit 55 --add-reviewer user3

# Set PR labels
gh pr edit 55 --label bug,priority-high

# Set PR milestone
gh pr edit 55 --milestone "v1.0"

# Merge PR
gh pr merge 55 --squash --delete-branch

# Close PR
gh pr close 55

# Reopen PR
gh pr reopen 55
```

### PR Reviews
```bash
# Submit PR review
gh pr review 55 --approve
gh pr review 55 --comment --body "Great work!"
gh pr review 55 --request-changes --body "Needs fixes"

# Check PR review status
gh pr view 55 --json reviewDecision
```

## Issues

### Viewing Issues
```bash
# List open issues
gh issue list

# List issues with filters
gh issue list --state closed
gh issue list --label bug
gh issue list --assignee user1

# View issue details
gh issue view 123

# List issue comments
gh issue view 123 --comments
```

### Creating Issues
```bash
# Create issue
gh issue create --title "Bug in login" --body "Description"

# Create issue with labels
gh issue create --label bug,priority-high

# Create issue and assign
gh issue create --assignee user1,user2

# Create issue from file
gh issue create --title "Bug" --body-file bug_report.md

# Create issue with milestone
gh issue create --milestone "v1.0"
```

### Managing Issues
```bash
# Edit issue
gh issue edit 123 --title "New title" --body "New description"

# Add/remove labels
gh issue edit 123 --add-label enhancement
gh issue edit 123 --remove-label bug

# Add/remove assignees
gh issue edit 123 --add-assignee user2
gh issue edit 123 --remove-assignee user1

# Close/reopen issue
gh issue close 123
gh issue reopen 123

# Add comment
gh issue comment 123 --body "Fixed in PR #456"
```

## Releases

### Viewing Releases
```bash
# List releases
gh release list

# View release details
gh release view v1.0.0

# Download release assets
gh release download v1.0.0 --pattern "*.zip"
```

### Creating Releases
```bash
# Create release from tag
gh release create v1.0.0 --notes "Release notes"

# Generate release notes automatically
gh release create v1.0.0 --generate-notes

# Create pre-release
gh release create v1.0.0-rc1 --prerelease

# Create draft release
gh release create v1.0.0 --draft

# Create release with assets
gh release create v1.0.0 --assets ./bin/*.zip
```

### Managing Releases
```bash
# Edit release
gh release edit v1.0.0 --title "Version 1.0.0" --notes "Updated notes"

# Delete release (keep tag)
gh release delete v1.0.0

# Delete release and tag
gh release delete v1.0.0 --yes
```

## GitHub Actions

### Workflow Runs
```bash
# List recent workflow runs
gh run list --limit 10

# View run details
gh run view 12345

# View run logs
gh run view 12345 --log

# Download run artifacts
gh run download 12345

# Rerun workflow
gh run rerun 12345

# Cancel workflow
gh run cancel 12345

# Watch running workflow
gh run watch 12345
```

### Workflow Management
```bash
# List workflows
gh workflow list

# View workflow
gh workflow view workflow.yml

# Enable/disable workflow
gh workflow enable workflow.yml
gh workflow disable workflow.yml

# Run workflow manually
gh workflow run workflow.yml --ref branch-name
```

## Repository Management

```bash
# View repository info
gh repo view owner/repo

# Clone repository
gh repo clone owner/repo

# Create repository
gh repo create my-repo --public

# Fork repository
gh repo fork owner/repo

# Sync fork
gh repo sync owner/repo --base-user fork-owner

# Add remote
gh remote add upstream https://github.com/upstream/repo.git
```

## GitHub API (Advanced Queries)

Use `gh api` for data not available through subcommands:

```bash
# Get repository info
gh api repos/owner/repo

# Get PR data
gh api repos/owner/repo/pulls/55 --jq '.title, .state, .user.login'

# Search issues
gh api search/issues?q=repo:owner/repo+type:issue+state:open+bug

# List contributors
gh api repos/owner/repo/contributors --paginate

# Get commit details
gh api repos/owner/repo/commits/SHA

# List branches
gh api repos/owner/repo/branches

# Get latest release
gh api repos/owner/repo/releases/latest --jq '.tag_name'

# Create issue via API
gh api repos/owner/repo/issues -f title="Bug" -f body="Description"

# Update issue via API
gh api repos/owner/repo/issues/123 -X PATCH -f state=closed
```

## Security Advisories

```bash
# List security advisories
gh api repos/owner/repo/security-advisories

# View advisory details
gh api repos/owner/repo/security-advisories/CVE-2024-12345

# Create security advisory (requires admin)
gh api repos/owner/repo/security-advisories \
  -X POST \
  -f cve_id="CVE-2024-12345" \
  -f summary="Security issue" \
  -f description="Details"
```

## Branch Management

```bash
# List branches
gh api repos/owner/repo/branches

# Get branch protection
gh api repos/owner/repo/branches/main/protection

# Create branch
gh api repos/owner/repo/git/refs \
  -X POST \
  -f ref="refs/heads/new-branch" \
  -f sha=$(gh api repos/owner/repo/commits/main --jq '.sha')
```

## Tips

- Always use `--repo owner/repo` when outside a git repository
- Use `--jq '.field'` to extract specific fields from JSON output
- Use `--paginate` for large result sets
- Use `--yes` to skip confirmations
- Combine filters for powerful queries: `gh pr list --state open --label "bug" --limit 50`

## Common Workflows

### PR Review Workflow
```bash
# 1. List PRs needing review
gh pr list --state open --review-requested=@me

# 2. Checkout and review locally
gh pr checkout 55
gh pr diff 55 > pr_diff.txt
gh pr view 55 --comments

# 3. Run CI checks
gh pr checks 55

# 4. Submit review
gh pr review 55 --approve --body "LGTM!"
```

### Bug Report to Fix Workflow
```bash
# 1. Create issue from bug report
gh issue create --title "[Bug] Description" --body @bug_report.md --label bug

# 2. Create fix branch
gh api repos/owner/repo/git/refs -X POST -f ref="refs/heads/fix/issue-123" -f sha=$(gh api repos/owner/repo/commits/main --jq '.sha')

# 3. Create draft PR when ready
gh pr create --title "Fix: Issue #123" --body "Closes #123" --head fix/issue-123 --draft
```

### Release Workflow
```bash
# 1. Check version and commits
gh release view latest
gh api repos/owner/repo/commits/main --jq '.[:10] | .[] | "\(.sha[:7]) \(.commit.message | split("\n")[0])"'

# 2. Create release
gh release create v1.2.0 --notes "## Changes\n- Feature A\n- Fix B" --title "Version 1.2.0"

# 3. Verify release assets
gh release view v1.2.0 --json assets
```

### Sync Fork Workflow
```bash
# 1. Add upstream remote
gh repo fork owner/repo --clone=false
git remote add upstream https://github.com/owner/repo.git

# 2. Sync with upstream
git fetch upstream
gh repo sync --base owner/repo

# 3. Push to your fork
git push origin main
```
