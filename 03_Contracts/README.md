# Consumed contracts

MediaCat Manager provides no external product contract.

It consumes the provider-owned MediaCat administration contract:

- product: `83degrees/MediaCat`
- authority: `03_Contracts/MEDIACAT_ADMIN_INTERFACE.md`
- current compatible version: `1.0.0` (`admin_interface_version: 1`)

This repository does not duplicate that contract. The dependency and local use
are recorded in `00_Governance/PROJECT_PROFILE.md` and
`01_Architecture/MEDIACAT_MANAGER_ARCHITECTURE.md`.
