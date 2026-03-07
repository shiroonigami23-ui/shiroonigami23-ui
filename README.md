# Shiro Nexus

Command center for managing and observing the full Shiro engineering ecosystem.

## What This Repo Does
- Maintains a central registry of active projects.
- Pulls GitHub metadata for each repo (status, last push, visibility, branch, stars, issues).
- Generates a unified portfolio dashboard.
- Acts as the base for future control-plane automation.

## Core Files
- [config/projects.json](./config/projects.json): source-of-truth project registry.
- [scripts/sync_dashboard.py](./scripts/sync_dashboard.py): metadata sync script.
- [generated/STATUS.md](./generated/STATUS.md): generated portfolio health dashboard.
- [generated/SHOWCASE.md](./generated/SHOWCASE.md): visitor-first map of all tracked repositories.
- [DEEP_DIVE_MYTORCH.md](./DEEP_DIVE_MYTORCH.md): technical deep-dive notes.

## Visitor Quick Start
- Start here for full ecosystem understanding: [Project Showcase](./generated/SHOWCASE.md)
- Operational status view: [Status Dashboard](./generated/STATUS.md)

## Current Tracked Projects
- Shiro-Nexus
- nba-os
- project-hub
- Research-Vault
- MyTorch-MNIST-Elite

## Usage
Generate or refresh the portfolio dashboard:

```powershell
python scripts/sync_dashboard.py
```

Optional for higher GitHub API limits:

```powershell
$env:GITHUB_TOKEN="<token>"
python scripts/sync_dashboard.py
```

## Next Expansion (Planned)
- Add per-project local health checks (build/test/dev-server status).
- Add one-command orchestration hooks for each repo.
- Add dependency graph and cross-repo release tracking.
- Add notification hooks for stale/failed critical repos.

---
Classification: Private / Proprietary

<!-- AUTO_PORTFOLIO_START -->
## Live Portfolio Snapshot

| Project | Category | Status | Last Push |
|---|---|---|---|
| [Shiro-Nexus](https://github.com/shiroonigami23-ui/Shiro-Nexus) | Control Plane | ACTIVE | 2026-03-07 06:03 UTC |
| [nba-os](https://github.com/shiroonigami23-ui/nba-os) | Enterprise Software | ACTIVE | 2026-03-07 05:21 UTC |
| [project-hub](https://github.com/shiroonigami23-ui/project-hub) | Education Platform | ACTIVE | 2026-03-06 11:03 UTC |
| [MyTorch-MNIST-Elite](https://github.com/shiroonigami23-ui/MyTorch-MNIST-Elite) | AI Engine | WARM | 2026-01-11 11:45 UTC |
| [Research-Vault](https://github.com/shiroonigami23-ui/Research-Vault) | Research | ACTIVE | 2026-03-07 05:42 UTC |

Generated docs:
- [Status Dashboard](./generated/STATUS.md)
- [Project Showcase](./generated/SHOWCASE.md)
- [Architecture Cards](./generated/ARCHITECTURE_CARDS.md)
<!-- AUTO_PORTFOLIO_END -->
