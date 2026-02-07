# Contributing to Light Agent

Thank you for your interest in contributing! This guide will help you get started.

## Why Contribute?

Light Agent is an active, evolving project with regular updates:

- **Recent Activity**: Features added weekly (short-term memory, GitHub tools, subagents)
- **Growing Use Cases**: From SRE tasks to general AI agent workflows
- **Community Driven**: Your ideas shape the roadmap

## How to Contribute

### 1. Report Issues

Found a bug? Have a feature request?

- Search existing issues first
- Use issue templates when available
- Include reproduction steps for bugs
- Explain the use case for feature requests

### 2. Submit Pull Requests

We welcome code contributions! Here's how:

```bash
# 1. Fork the repository
gh repo fork adilsonmenechini/light-agent

# 2. Create a feature branch
git checkout -b feature/your-feature

# 3. Make your changes
# Follow the Development Guide: docs/development_guide.md

# 4. Test your changes
pytest light_agent/

# 5. Push and create PR
git push -u origin feature/your-feature
gh pr create --title "feat: Your feature" --body "Description..."
```

### 3. Improve Documentation

Documentation improvements are highly valued:

- Fix typos and clarify explanations
- Add examples and tutorials
- Translate to other languages
- Improve getting-started experience

### 4. Share Your Use Case

How are you using Light Agent? Share your experience:

- Write a blog post
- Record a demo video
- Add your use case to docs

## Areas Where Help is Needed

| Priority | Area | Description |
|----------|------|-------------|
| 🟢 | **Examples & Tutorials** | Real-world use case guides |
| 🟢 | **Plugin Ecosystem** | MCP server integrations |
| 🟡 | **Testing** | Increase test coverage |
| 🟡 | **Performance** | Optimize for speed |
| 🔵 | **UI/CLI** | Enhanced terminal experience |

## Communication

- **Discussions**: [GitHub Discussions](https://github.com/adilsonmenechini/light-agent/discussions)
- **Issues**: [GitHub Issues](https://github.com/adilsonmenechini/light-agent/issues)
- **Updates**: Watch the repo for releases

## Recognition

Contributors are acknowledged in:

- Release notes
- Documentation credits
- Community highlights

---

**Ready to contribute?** Start with [good first issues](https://github.com/adilsonmenechini/light-agent/labels/good%20first%20issue)!
