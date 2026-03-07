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
