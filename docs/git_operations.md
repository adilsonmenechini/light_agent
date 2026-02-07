# Git Operations Guide

Comprehensive guide for Git operations using the Light Agent.

## Basic Operations

### Repository Setup

```bash
# Clone a repository
git clone <repository-url>
git clone https://github.com/owner/repo.git

# Clone with specific branch
git clone -b branch-name <repository-url>

# Shallow clone (faster)
git clone --depth 1 <repository-url>

# Add remote
git remote add origin <repository-url>
git remote add upstream <upstream-url>

# View remotes
git remote -v
```

### Branch Management

```bash
# List branches
git branch                  # Local branches
git branch -r              # Remote branches
git branch -a             # All branches

# Create branch
git branch feature/new-feature
git checkout -b feature/new-feature  # Create and switch

# Switch branch
git checkout branch-name
git switch branch-name     # New syntax

# Delete branch
git branch -d branch-name      # Safe delete
git branch -D branch-name      # Force delete

# Rename branch
git branch -m old-name new-name
```

### Making Changes

```bash
# Check status
git status
git status -s            # Short format

# Stage changes
git add filename
git add .               # Stage all
git add -p              # Interactive staging

# Commit changes
git commit -m "Brief description"
git commit -am "Message"  # Stage and commit tracked files

# Amend commit
git commit --amend
git commit --amend --no-edit
```

### Undoing Changes

```bash
# Unstage files
git reset HEAD filename
git reset HEAD .         # Unstage all

# Revert working directory
git checkout -- filename
git checkout -- .        # Discard all changes

# Reset to previous commit
git reset --soft HEAD~1   # Keep changes staged
git reset HEAD~1         # Keep changes unstaged
git reset --hard HEAD~1  # Discard all changes

# Revert a commit (safe for shared history)
git revert <commit-hash>
git revert --no-commit <commit-hash>
```

## Advanced Operations

### Viewing History

```bash
# View commit log
git log
git log --oneline
git log --graph --oneline
git log -p filename       # Show changes for file
git log --stat            # Show statistics

# Search commit messages
git log --grep="keyword"
git log -S "code pattern" # Search for code changes

# View specific commit
git show <commit-hash>
git show --name-only <commit-hash>

# Blame (who changed what)
git blame filename
git blame -L 10,20 filename  # Specific lines

# Difference between commits
git diff commit1..commit2
git diff HEAD~5..HEAD
```

### Stashing

```bash
# Save changes
git stash
git stash save "work in progress"

# List stashes
git stash list

# Apply stash
git stash apply
git stash apply stash@{0}

# Apply and drop stash
git stash pop

# Drop stash
git stash drop stash@{0}
```

### Tagging

```bash
# List tags
git tag
git tag -l "v1.*"

# Create tag
git tag v1.0.0
git tag -a v1.0.0 -m "Version 1.0.0"

# Create tag with annotation
git tag -a v1.0.0 <commit-hash>

# Delete tag
git tag -d v1.0.0

# Push tags
git push origin v1.0.0
git push origin --delete v1.0.0
```

## Collaboration Workflows

### Sync with Remote

```bash
# Fetch changes
git fetch
git fetch origin
git fetch --all

# Pull changes
git pull
git pull --rebase        # Rebase instead of merge

# Push changes
git push
git push origin branch-name
git push -u origin branch-name  # Set upstream

# Update from upstream
git fetch upstream
git merge upstream/main
```

### Pull Requests Workflow

```bash
# Update feature branch with main
git checkout feature-branch
git fetch origin
git merge origin/main
# Resolve conflicts, then:
git add .
git commit -m "Merge main"
git push

# Create PR via gh CLI
gh pr create --title "Feature" --body "Description"
```

### Merging

```bash
# Merge branch
git merge feature-branch

# Merge with strategy
git merge --no-ff feature-branch  # No fast-forward
git merge -X theirs feature-branch  # Prefer their changes

# Abort merge
git merge --abort

# Resolve conflicts
git mergetool
```

### Rebasing

```bash
# Rebase onto another branch
git checkout feature-branch
git rebase main

# Interactive rebase
git rebase -i HEAD~5
# Commands: pick, reword, edit, squash, fixup, drop

# Continue rebase after resolving conflicts
git rebase --continue

# Abort rebase
git rebase --abort
```

## GitHub Integration

### Using gh CLI

```bash
# Clone with gh
gh repo clone owner/repo

# Create PR
gh pr create --title "Title" --body "Description"

# View PR
gh pr view 55
gh pr diff 55

# Checkout PR
gh pr checkout 55

# Merge PR
gh pr merge 55 --squash --delete-branch

# Create issue
gh issue create --title "Bug" --body "Description"
```

### GitHub Actions with Git

```bash
# Check out repository
git checkout ${{ github.ref }}
git fetch-depth 0  # Full history for versioning
```

## Best Practices

### Commit Messages

```
feat: Add new user authentication
fix: Resolve memory leak in cache
docs: Update README with setup instructions
style: Format code with black
refactor: Extract validation logic
test: Add unit tests for auth module
chore: Update dependencies
```

### Branch Naming

| Type | Example |
|------|---------|
| Feature | `feature/user-authentication` |
| Bugfix | `bugfix/login-error` |
| Hotfix | `hotfix/security-patch` |
| Release | `release/v1.0.0` |
| Docs | `docs/update-readme` |

### Git Configuration

```bash
# Set user
git config user.name "Your Name"
git config user.email "email@example.com"

# Set editor
git config core.editor vim

# Set aliases
git config alias.st status
git config alias.co checkout
git config alias.br branch
git config alias.lg "log --oneline --graph"

# Global config
git config --global user.name "Name"
git config --global core.editor "code --wait"
```

## Troubleshooting

### Common Issues

```bash
# Detached HEAD
git checkout main
git branch -D detached-branch-name

# Push rejected (remote has changes)
git pull --rebase
git push

# Forgot to add file
git add forgotten-file
git commit --amend --no-edit

# Wrong branch committed
git branch feature
git reset --soft HEAD~1
git checkout correct-branch
git commit -m "Message"

# Large file in history
git filter-branch --tree-filter 'rm -f filename' HEAD
git filter-repo --invert-paths --path filename  # Better alternative
```

### Recover Lost Data

```bash
# Find lost commits
git reflog
git reflog --all

# Recover deleted branch
git checkout -b branch-name <commit-hash>

# Recover deleted tag
git checkout -b temp <tag-hash>
```

## Security Notes

The Light Agent restricts Git operations to safe commands:

### Allowed Git Commands

- `git status`, `git log`, `git diff`
- `git branch`, `git checkout`, `git switch`
- `git add`, `git commit` (staged changes only)
- `git push`, `git pull`
- `git fetch`, `git merge`, `git rebase`
- `git stash`, `git tag`
- `git remote`

### Blocked Operations

- Direct file operations outside workspace
- Dangerous flags (e.g., `--force` without approval)
- Shell metacharacters in commands

See `light_agent/agent/tools/shell.py` for security configuration.
