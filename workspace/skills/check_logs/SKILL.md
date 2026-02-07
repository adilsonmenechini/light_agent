---
name: check_logs
description: System log analysis for SRE troubleshooting. Covers journalctl, file logs, grep patterns, and common error signatures.
---

# Check Logs Skill

Systematic approach to log analysis for troubleshooting production issues.

## Log Locations by Service Type

### System Logs (Linux)
```bash
# Core system logs
/var/log/syslog          # Debian/Ubuntu full system log
/var/log/messages        # RHEL/CentOS general messages
/var/log/kern.log        # Kernel messages
/var/log/dmesg           # Boot and kernel ring buffer
/var/log/auth.log        # Authentication events

# View with tail for real-time
tail -f /var/log/syslog

# View last N lines
tail -n 100 /var/log/syslog
```

### Application Logs
```bash
# Nginx/Apache
/var/log/nginx/access.log
/var/log/nginx/error.log
/var/log/apache2/access.log
/var/log/httpd/error_log

# Docker/Containers
docker logs <container_name>
docker logs -f <container_name> --tail 100

# Node.js
tail -f /var/log/app/error.log

# Python
tail -f ./logs/app.log
```

### Cloud Services
```bash
# AWS CloudWatch
aws logs describe-log-groups
aws logs get-log-events --log-group-name /aws/lambda/my-function

# GCP Logging
gcloud logging read "resource.type=cloud_run_revision" --limit 50
```

## journalctl (systemd) Patterns

```bash
# View all logs for a service
journalctl -u nginx

# View logs since last boot
journalctl -b

# View logs with time filter
journalctl --since "2024-01-15 10:00:00"
journalctl --since "-2h"                    # Last 2 hours

# Real-time follow
journalctl -u nginx -f

# Priority filter (err, warn, notice, info)
journalctl -u nginx -p err
journalctl -p crit,alert,emerg              # Critical only

# Compact output
journalctl -u nginx --no-pager -o json | head -50

# Show disk usage
journalctl --disk-usage
```

## Grep Patterns for Errors

```bash
# Common error patterns
grep -i "error|fail|critical|exception" /var/log/syslog
grep -iE "timeout|connection refused|broken pipe" /var/log/app.log

# Find stack traces
grep -rA 10 "Traceback (most recent call last)" /var/log/

# HTTP error codes
grep -E "5[0-9]{2}|4[0-9]{2}" /var/log/nginx/access.log

# Count occurrences
grep -c "ERROR" /var/log/app/error.log

# Tail with filter
tail -f /var/log/app.log | grep --line-buffered -i error
```

## Log Analysis Workflow

### 1. Identify the Service
```bash
# Check what's running
systemctl --type=service --state=running
docker ps --format "{{.Names}}: {{.Image}}"

# Check ports in use
netstat -tlnp | grep :80
```

### 2. Check Recent Errors
```bash
# Get last 50 error-level entries
journalctl -u myapp -p err -n 50 --no-pager

# Get logs around a time window
journalctl --since="-30min" -u myapp --no-pager | tail -100
```

### 3. Find Related Entries
```bash
# Search for request ID or correlation ID
grep -r "request-id-123" /var/log/myapp/
```

## Common Error Signatures

| Error Pattern | Likely Cause | Check |
|---------------|--------------|-------|
| `Connection refused` | Service down, wrong port | `systemctl status <service>` |
| `OOMKilled` | Memory exhausted | `dmesg | grep -i oom` |
| `Segmentation fault` | Bug/crash | `journalctl -u <service> -n 20` |
| `Too many open files` | ulimit reached | `ulimit -n` |

## Quick Diagnostic Commands

```bash
# Service health check
systemctl status <service> --no-pager

# Check disk space
df -h
du -sh /var/log/* | sort -h | tail -10

# Monitor for new errors
tail -f /var/log/app.log | grep -i error --line-buffered
```
