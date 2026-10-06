# MediaCat Manager

MediaCat Manager is a private Home Assistant App that provides the local,
Ingress-hosted administration surface for MediaCat catalogue files.

The App provides typed schema-v4 item and category editing, MediaCat-owned
validation and reload orchestration, atomic catalogue replacement, bounded
local history with diff/revert, and a visual read-only picker for the local
`ha-assets` mirror.

## Repository layout

- `00_Governance/` — product context plus centrally projected governance.
- `01_Architecture/` — authoritative product architecture.
- `03_Contracts/` — references to provider-owned consumed contracts.
- `04_Implementation/haos/source/apps/mediacat_manager/` — authoritative Home Assistant App package.
- `05_Tests/` — maintained product tests.
- `06_Validation/` — validation guidance and evidence locations.
- `08_Deployment/` — governed install, update and rollback runbook.

## Local checks

```text
python -m unittest discover -s 05_Tests -p "test_*.py"
```

The stable Home Assistant App repository source is
`https://github.com/83degrees/MediaCat-Manager`. Governed Beta deployment uses
`https://github.com/83degrees/MediaCat-Manager#beta`. Installation, update,
evidence and rollback requirements are documented in
`08_Deployment/HOME_ASSISTANT_APP_DEPLOYMENT_RUNBOOK.md`.

Normal catalogue changes are validated by MediaCat before any write. Each
successful replacement first snapshots the current file under App-private
history. A failed MediaCat reload is reported without discarding the new file or
the evidence needed to inspect and restore it.
