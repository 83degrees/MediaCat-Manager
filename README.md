# MediaCat Manager

MediaCat Manager is a private Home Assistant App that provides the local,
Ingress-hosted administration surface for MediaCat catalogue files.

This bootstrap intentionally contains only the governed App shell, filesystem
safety primitives, architecture and tests. The typed catalogue editor, history
browser/revert workflow and visual asset picker remain in `ASTV-286`.

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
