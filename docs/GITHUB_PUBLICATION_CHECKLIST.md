# GitHub Publication Checklist

Before making the repository public:

- [ ] repository name is `intelligence-os`
- [ ] default branch is `main`
- [ ] README renders correctly
- [ ] no real API keys / tokens / OAuth files / databases are present
- [ ] `python scripts/public_repo_audit.py` passes
- [ ] `python scripts/build_release.py` passes
- [ ] GitHub Actions CI passes on Python 3.11 and 3.12
- [ ] CodeQL is enabled and completes successfully
- [ ] Private Vulnerability Reporting is enabled if available
- [ ] repository description states `Developer Alpha`
- [ ] repository topics do not imply production medical safety
- [ ] no open-source license is implied until one is deliberately selected
- [ ] first Release is marked **pre-release** (`v0.7.2-alpha`)
- [ ] release notes link to `KNOWN_LIMITATIONS.md` and `SECURITY.md`

Recommended GitHub description:

> Experimental local-first Personal Cognitive Infrastructure: memory, verification, outcome learning, bounded automation, and safety-limited AI authority. Developer Alpha.

Recommended topics:

`ai`, `local-first`, `human-ai-collaboration`, `context-engineering`, `evals`, `ai-safety`, `personal-ai`, `verification`, `agentic-systems`
