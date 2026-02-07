---
name: debugging
description: Systematic SRE debugging approach. Covers troubleshooting methodology, common patterns, and diagnostic techniques.
---

# Debugging Skill

Systematic approach to diagnosing and resolving production issues.

## Debugging Methodology

### 1. Gather Information

Before making any changes, collect data:

```bash
# Service status
systemctl status <service> --no-pager

# Recent logs
journalctl -u <service> -p err --since="-1h" --no-pager | tail -50

# Resource usage
htop
iostat -x 1
netstat -tlnp
ss -s

# Recent changes
git log --oneline -10
journalctl -b | tail -20
```

### 2. Reproduce the Issue

```bash
# Test endpoint
curl -v https://api.example.com/health

# Check connectivity
nc -zv host port
telnet host port

# Test from different locations
curl https://api.example.com/endpoint --resolve "api.example.com:443:IP"
```

### 3. Isolate Variables

```bash
# Check if issue is widespread or isolated
# Test different environments
# Disable/enable features gradually
```

### 4. Identify Root Cause

```bash
# Look for patterns in logs
grep -i "error\|timeout\|failed" /var/log/app.log

# Check for recent deployments
git log --since="1 day ago" --oneline

# Check resource exhaustion -h
free
df -m
ulimit -a
```

### 5. Implement Fix

```bash
# Apply fix incrementally
# Test fix in isolation
# Document changes
```

### 6. Verify Fix

```bash
# Confirm issue resolved
# Monitor for regressions
# Check related metrics
```

## Common Issue Categories

### Performance Issues

```bash
# CPU high
top -bn1 | head -20
ps aux --sort=-%cpu | head -10

# Memory leak
ps aux --sort=-%mem | head -10
pmap <pid> | grep total

# Slow queries
# Check database slow query log
mysql -e "SHOW FULL PROCESSLIST"
```

### Network Issues

```bash
# Connection refused
netstat -tlnp | grep :port
ss -tlnp | grep :port

# DNS resolution
nslookup host
dig host
getent hosts host

# Latency
ping host
mtr host
tracepath host
```

### Disk Issues

```bash
# Space full
df -h
du -sh /var/* | sort -h

# Inodes exhausted
df -i

# I/O wait
iostat -x 1
```

### Application Crashes

```bash
# Core dumps
ls -la /var/lib/<app>/core*
coredumpctl list

# Stack traces
journalctl -u <app> -n 100

# Restart loops
journalctl -u <app> --since="-5min"
```

## Diagnostic Commands

### Quick Health Check
```bash
# One-liner for service health
systemctl is-active <service> && echo "OK" || echo "DOWN"
```

### Network Diagnostics
```bash
# Check port accessibility
nc -zv host port 2>&1

# Check SSL certificate
openssl s_client -connect host:port -servername host

# Check DNS
dig +short host
```

### Log Patterns
```bash
# Find recent errors
journalctl -u <service> -p err -n 20 --no-pager

# Count error types
journalctl -u <app> --since="-1h" --no-pager | grep -i error | wc -l

# Find exceptions
grep -rA 5 "Exception\|Error:" /var/log/app/
```

## Debugging Tools

| Tool | Purpose |
|------|---------|
| `tcpdump` | Packet capture |
| `strace` | System calls |
| `ltrace` | Library calls |
| `htop` | Interactive process viewer |
| `iotop` | I/O usage |
| `netstat` / `ss` | Network connections |
| `lsof` | Open files |

## Escalation Checklist

Before escalating, ensure you have:

- [ ] Error messages and stack traces
- [ ] Relevant logs (timestamped)
- [ ] Service status output
- [ ] Resource usage metrics
- [ ] Recent changes identified
- [ ] Steps to reproduce documented
- [ ] Impact assessment (users affected)

## Post-Mortem Template

```markdown
# Incident: [Title]

## Summary
Brief description of what happened.

## Impact
- Users affected: X
- Duration: Y minutes
- Revenue/latency impact: Z

## Root Cause
Technical explanation of what failed.

## Timeline
- T0: Issue detected
- T1: Investigation started
- T2: Root cause identified
- T3: Fix deployed
- T4: Recovery confirmed

## Resolution
How the issue was fixed.

## Lessons Learned
- What went well
- What could be improved
- Preventive actions
```

## Tips

1. **Check recent changes first**: Most issues are from recent deployments
2. **Use timestamps**: Always note when events occurred
3. **Check dependencies**: Database, cache, API services
4. **Look for patterns**: Same error repeating?
5. **Use bisect**: For regression hunting
6. **Document everything**: For future reference
