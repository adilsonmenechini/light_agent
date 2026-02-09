---
name: github-security-advisories
description: "Manage GitHub Security Advisories, vulnerabilities, and security disclosures."
---

# GitHub Security Advisories

Manage security vulnerabilities and coordinated disclosures through GitHub's Security Advisories feature.

## Prerequisites

- Repository admin or security manager role
- GitHub Advanced Security license (for private repos)
- Admin permissions to create/edit advisories

## Viewing Security Advisories

### List Repository Advisories
```bash
# List all security advisories
gh api repos/owner/repo/security-advisories

# View specific advisory
gh api repos/owner/repo/security-advisories/CVE-2024-12345

# Get advisory with CVE details
gh api repos/owner/repo/security-advisories/GHSA-xxxx \
  --jq '.cve_id, .summary, .severity, .published_at'
```

### Advisory States
- **Open**: Active vulnerability being researched
- **Resolved**: Fix has been released
- **Closed**: Advisory was closed without resolution

## Creating Security Advisories

### Step 1: Gather Information
```bash
# Get affected file versions
gh api repos/owner/repo/commits?path=affected_file.py&per_page=10

# Check vulnerable code patterns
git log --all --oneline --grep="security" --since="6 months ago"

# Identify affected versions
gh api repos/owner/repo/releases --jq '.[].tag_name'
```

### Step 2: Create Draft Advisory
```bash
gh api repos/owner/repo/security-advisories \
  -X POST \
  -f cve_id="CVE-2024-XXXXX" \
  -f summary="SQL Injection vulnerability in user authentication" \
  -f description="A SQL injection vulnerability exists in the authentication module..." \
  -f severity="critical" \
  -f affected_packages=[{"package":{"ecosystem":"pypi","name":"myapp"},"vulnerable_version_range":"< 1.5.0"}] \
  -f vulnerable_versions=["< 1.5.0"] \
  -f fixed_versions=["1.5.0"]
```

### Advisory Fields

| Field | Description |
|-------|-------------|
| `cve_id` | CVE identifier (if assigned) |
| `summary` | Brief title (max 1024 chars) |
| `description` | Detailed description |
| `severity` | critical, high, medium, low |
| `affected_packages` | Package name and ecosystem |
| `vulnerable_version_range` | Range of affected versions |
| `fixed_versions` | Versions with fix |

## Managing CVEs

### Request CVE Assignment
```bash
# Create advisory and request CVE
gh api repos/owner/repo/security-advisories \
  -X POST \
  -f cve_request_public=true \
  -f summary="Authentication bypass" \
  -f description="..." \
  -f severity="critical"
```

### Publish CVE
```bash
# After moderation approval, publish
gh api repos/owner/repo/security-advisories/GHSA-xxxx \
  -X PATCH \
  -f published=true
```

## Coordinating Security Updates

### Private Fork Workflow
```bash
# Create private fork for fix development
gh api repos/owner/repo/forks \
  -X POST \
  -f organization=security-team-org

# Clone the private fork
gh repo clone security-team-org/repo

# Develop fix in isolation
git checkout -b fix/vulnerability
# ... develop fix ...
git push origin fix/vulnerability

# Create PR to main repo
gh pr create \
  --title "Security: Fix SQL injection vulnerability" \
  --body "This PR fixes a security vulnerability..." \
  --head security-team-org:fix/vulnerability
```

### Security Pull Requests
```bash
# Create security PR (automatically adds security team)
gh pr create \
  --title "Fix CVE-2024-XXXXX" \
  --body "This PR addresses a security vulnerability" \
  --label security

# Add security team as reviewer
gh pr edit PR_NUMBER --add-reviewer @org/security-team
```

## Dependabot Alerts Integration

### View Vulnerability Alerts
```bash
# List Dependabot alerts
gh api repos/owner/repo/dependabot/alerts?state=open

# Get specific alert
gh api repos/owner/repo/dependabot/alerts/ALERT_ID \
  --jq '.security_advisory, .vulnerable_package, .severity'

# Get alert with fix details
gh api repos/owner/repo/dependabot/alerts/ALERT_ID \
  --jq '.security_advisory, .fix_available'
```

### Create Advisory from Dependabot
```bash
# If Dependabot found vulnerability, create advisory
gh api repos/owner/repo/security-advisories \
  -X POST \
  -f summary="Dependabot: $PACKAGE vulnerability" \
  -f description="$DESCRIPTION" \
  -f severity="$SEVERITY" \
  -f affected_packages=[{"package":{"ecosystem":"$ECOSYSTEM","name":"$PACKAGE"}}] \
  -f vulnerable_versions="$VERSION_RANGE"
```

## Vulnerability Disclosure

### Creating Disclosure Message
```markdown
# Security Vulnerability Disclosure

## Summary
[Brief description of vulnerability]

## Affected Versions
- All versions prior to X.Y.Z

## Impact
[What an attacker could accomplish]

## Proof of Concept
[Optional: Example attack]

## Remediation
Upgrade to version X.Y.Z or later.

## Timeline
- [Date]: Vulnerability discovered
- [Date]: CVE requested
- [Date]: Fix developed
- [Date]: Patched version released

## Credit
Thank you to [reporter] for responsible disclosure.
```

### Publish Disclosure
```bash
# After fix release, publish advisory
gh api repos/owner/repo/security-advisories/GHSA-xxxx \
  -X PATCH \
  -f published=true
```

## Security Best Practices

### Version Range Patterns
```bash
# Less than a version
"< 1.5.0"

# Range of versions
">= 1.0.0, < 2.0.0"

# All versions before and including
"<= 1.4.0"

# Multiple ranges
">= 1.0.0, < 1.5.0 || >= 2.0.0, < 2.3.0"
```

### Severity Levels
| Level | Description |
|-------|-------------|
| `critical` | Immediate threat to systems |
| `high` | Significant vulnerability |
| `medium` | Moderate impact |
| `low` | Minimal impact |

## Auditing Security Advisories

### Get Advisory History
```bash
# Get all advisories with details
gh api repos/owner/repo/security-advisories \
  --jq '.[] | {cve: .cve_id, severity: .severity, state: .state}'

# Check resolution time
gh api repos/owner/repo/security-advisories \
  --jq '.[] | {created: .created_at, published: .published_at}'
```

### Generate Security Report
```bash
# Count advisories by severity
gh api repos/owner/repo/security-advisories \
  --jq '[.[] | .severity] | unique | map({"severity": ., "count": (reduce .[] as $item (0; . + 1))})'

# Get recent resolved advisories
gh api repos/owner/repo/security-advisories?state=resolved \
  --jq '.[] | {cve: .cve_id, fixed: .fixed_versions, resolved: .updated_at}'
```

## GitHub Actions for Security

### Notify on New Advisory
```yaml
# .github/workflows/security-advisory.yml
name: Security Advisory Watch
on:
  schedule:
    - cron: '0 8 * * *'  # Daily at 8am

jobs:
  check-advisories:
    runs-on: ubuntu-latest
    steps:
      - name: Check new advisories
        run: |
          gh api repos/${{ github.repository }}/security-advisories \
            --jq '.[] | select(.published_at | startswith("$(date +%Y-%m-%d)"))' \
            >> new_advisories.json
```

### Auto-create Issue for Vulnerability
```yaml
- name: Create issue for critical alert
  if: ${{ steps.alert.outputs.severity == 'critical' }}
  run: |
    gh issue create \
      --title "Security: ${{ env.VULNERABILITY }}" \
      --body "Critical vulnerability detected..." \
      --label security,critical
```
