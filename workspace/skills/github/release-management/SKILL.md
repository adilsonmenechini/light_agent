---
name: github-release-management
description: "Manage GitHub releases, versions, and changelogs. Supports semantic versioning and automated release notes."
---

# GitHub Release Management

Complete workflow for creating and managing software releases.

## Version Management

### Semantic Versioning Basics
- **Major** (x.0.0): Breaking changes
- **Minor** (0.x.0): New features (backward compatible)
- **Patch** (0.0.x): Bug fixes

### Version Format
```
vMAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
Examples: v1.0.0, v2.1.0-rc1, v3.0.0-alpha+001
```

## Pre-Release Checklist

```bash
# 1. Check all PRs merged since last release
gh pr list --state merged --base main --limit 100

# 2. Verify CI passes on main branch
gh run list --branch main --limit 5

# 3. Check for open critical issues
gh issue list --state open --label critical

# 4. Review recent commits
gh api repos/owner/repo/commits?sha=main&per_page=50

# 5. Check if version tag already exists
gh api repos/owner/repo/git/refs/tags
```

## Creating Releases

### Standard Release
```bash
# Create release from main branch
gh release create v1.0.0 \
  --title "Version 1.0.0" \
  --notes "Release notes here" \
  --draft

# Verify and publish
gh release view v1.0.0 --repo owner/repo
gh release edit v1.0.0 --draft=false
```

### Auto-Generate Release Notes
```bash
# Generate comprehensive release notes
gh release create v1.0.0 --generate-notes

# Generate with specific target
gh release create v1.0.0 --generate-notes --target main

# Include PRs since specific version
gh release create v1.0.0 \
  --notes-start-tag v0.9.0 \
  --generate-notes
```

### Pre-Release (RC, Beta, Alpha)
```bash
# Release candidate
gh release create v1.0.0-rc1 \
  --title "Release Candidate 1" \
  --prerelease \
  --notes "RC for v1.0.0"

# Beta release
gh release create v2.0.0-beta.1 \
  --title "Beta 1" \
  --prerelease

# Alpha release
gh release create v3.0.0-alpha \
  --prerelease \
  --notes "Early preview"
```

## Release Notes Best Practices

### Structure
```markdown
## Version X.Y.Z (DATE)

### Added
- New feature A
- New feature B

### Changed
- Updated behavior of X
- Performance improvement Y

### Deprecated
- Feature Z is deprecated, use W

### Removed
- Removed legacy API

### Fixed
- Bug fix A
- Bug fix B

### Security
- Vulnerability patched in X
```

### Generate with API
```bash
# Get merged PRs since last release
gh api repos/owner/repo/pulls \
  --state merged \
  --jq '.[] | "\(.merged_at) - \(.title) #\(.number)"'

# Get closed issues
gh api repos/owner/repo/issues \
  --state closed \
  --jq '.[] | "\(.closed_at) - \(.title) #\(.number)"'
```

## Managing Release Assets

### Upload Assets
```bash
# Upload binary files
gh release upload v1.0.0 ./bin/app-linux-amd64
gh release upload v1.0.0 ./bin/app-macos-arm64
gh release upload v1.0.0 ./bin/app-windows.exe

# Upload archives
gh release upload v1.0.0 ./dist/*.zip --clobber
gh release upload v1.0.0 ./dist/*.tar.gz --clobber

# Pattern-based upload
gh release upload v1.0.0 --pattern "dist/*.{zip,tar.gz}"
```

### Download Assets
```bash
# Download all assets
gh release download v1.0.0

# Download specific pattern
gh release download v1.0.0 --pattern "*.deb"

# Download to specific directory
gh release download v1.0.0 -D ./downloads
```

## Release Verification

```bash
# View release details
gh release view v1.0.0 --json body,assets,prerelease

# Verify asset checksums
gh release view v1.0.0 --json assets --jq '.[].name'

# Check release was published
gh api repos/owner/repo/releases/tags/v1.0.0 \
  --jq '.published_at, .draft, .prerelease'

# Verify Git tag exists
git ls-remote --tags origin | grep v1.0.0
```

## Hotfix Release Workflow

```bash
# 1. Create hotfix branch from tag
git checkout v1.0.0
git checkout -b hotfix/v1.0.1

# 2. Make fix
echo "fix" >> file.txt
git add .
git commit -m "Fix critical bug"
git push origin hotfix/v1.0.1

# 3. Create PR to main
gh pr create \
  --title "Hotfix v1.0.1" \
  --body "Critical fix" \
  --base main

# 4. After merge, create release
gh release create v1.0.1 \
  --notes "Fix critical bug #123"
```

## Rollback Release

```bash
# Create new release with revert notes
gh release create v1.0.1 \
  --title "Rollback v1.0.0" \
  --notes "Rolling back due to critical bug"

# Or delete release (keeps tag)
gh release delete v1.0.0 --yes

# Delete release and tag
gh release delete v1.0.0 --delete-tag --yes
```

## Release Metrics

```bash
# Get release count
gh api repos/owner/repo/releases --jq 'length'

# Get download statistics
gh api repos/owner/repo/releases/tags/v1.0.0 \
  --jq '.assets[].download_count'

# Get release by tag
gh api repos/owner/repo/releases/tags/v1.0.0

# List all releases
gh release list --limit 50
```

## GitHub Actions Integration

### Automatic Release on Tag
```yaml
# .github/workflows/release.yml
name: Release
on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Create Release
        run: |
          gh release create ${{ github.ref_name }} \
            --title ${{ github.ref_name }} \
            --generate-notes
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Draft Release with Artifacts
```yaml
- name: Upload Release Asset
  uses: actions/upload-release-asset@v1
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  with:
    upload_url: ${{ steps.create_release.outputs.upload_url }}
    asset_path: ./dist/app
    asset_name: app
    asset_content_type: application/octet-stream
```
