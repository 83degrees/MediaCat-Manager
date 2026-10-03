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
- `04_Source/mediacat_manager/` — Home Assistant App package.
- `05_Tests/` — maintained product tests.
- `06_Validation/` — validation guidance and evidence locations.

## Local checks

```text
python -m unittest discover -s 05_Tests -p "test_*.py"
```

The Home Assistant App repository can be added from
`https://github.com/83degrees/MediaCat-Manager` once an accepted release is
available.

Normal catalogue changes are validated by MediaCat before any write. Each
successful replacement first snapshots the current file under App-private
history. A failed MediaCat reload is reported without discarding the new file or
the evidence needed to inspect and restore it.
