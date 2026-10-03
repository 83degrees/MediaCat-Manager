# PROJECT_PROFILE: MediaCat Manager

## Profile conformance

This profile contains the required product-profile subjects for the implemented
MediaCat Manager bootstrap.

## Document status

- Governance state: approved current bootstrap baseline; ASTV-286 editor scope remains deferred
- Design baseline: `ASTV-275`
- Bootstrap implementation completed through Linear: `ASTV-277`

## Product identity

- Product name: MediaCat Manager
- Repository: `83degrees/MediaCat-Manager`
- DDR origin code: `06`

## Linear work routing

- Default Linear team: `ASTV`

## Purpose

MediaCat Manager provides a private, local Home Assistant Ingress application
for safely administering the catalogue files consumed by MediaCat without
requiring repository credentials in Home Assistant.

## Scope

### In scope

- Home Assistant App packaging and Ingress-hosted administration UI.
- Safe access to local MediaCat catalogue files.
- Atomic catalogue replacement and Manager-owned bounded history.
- Read-only browsing of the local `ha-assets` mirror.
- Consumption of MediaCat's supported administration interface.

### Out of scope

- MediaCat schema, validation, runtime loading, reload or capability authority.
- Direct GitHub write-back or private-repository credentials in Home Assistant.
- General Home Assistant YAML administration.
- Import/export, cross-instance synchronisation or secret management.

## Ownership and boundaries

| Boundary or capability | Relationship | Owner | Notes |
| --- | --- | --- | --- |
| Ingress UI and catalogue administration workflow | owned | MediaCat Manager | The ASTV-277 bootstrap provides the shell only; editor workflows remain in ASTV-286. |
| Catalogue write safety and local history | owned | MediaCat Manager | Writes are confined by code to `/config/mediacat/catalogues/`; history is confined to App-private `/data/history/`. |
| Catalogue schema, validation and transactional runtime reload | consumed | MediaCat | Used only through `MEDIACAT_ADMIN_INTERFACE.md`; not duplicated locally. |
| Local `ha-assets` mirror | consumed read-only | ha-assets-sync | Reads are confined by code to `/config/www/ha-assets/`; the Manager never writes the mirror. |
| Home Assistant App/Ingress platform | external | Home Assistant | Hosts the container, persistent App data and authenticated Ingress route. |

## Approved architecture location

- Approved architecture location: `01_Architecture/MEDIACAT_MANAGER_ARCHITECTURE.md`
- Architecture state: approved current bootstrap architecture; ASTV-286 editor scope remains deferred
- Material DDRs: None; ASTV-275 is the accepted design parent for this bootstrap

## Contracts provided

None in the ASTV-277 bootstrap.

## Contracts consumed

| Contract | Status/version | Provider/owner | Authoritative location | Local use |
| --- | --- | --- | --- | --- |
| `MEDIACAT_ADMIN_INTERFACE.md` | current v1.0.0 | MediaCat | `83degrees/MediaCat/03_Contracts/MEDIACAT_ADMIN_INTERFACE.md` | Capability discovery, candidate validation and transactional reload. |

## Product dependencies

| Dependency | Type | Owner | Governed interface/evidence | Required state | Failure boundary |
| --- | --- | --- | --- | --- | --- |
| MediaCat | product/service | MediaCat | `MEDIACAT_ADMIN_INTERFACE.md` | Compatible administration interface available | UI remains reachable and reports the provider unavailable; no catalogue write is attempted. |
| Home Assistant | platform | Home Assistant | App and Ingress runtime | App installed with Ingress and API access | Failure is confined to the App; Home Assistant Core continues operating. |
| Local catalogue directory | data | Home Assistant instance / MediaCat runtime | `/config/mediacat/catalogues/` | Directory available for controlled reads and atomic replacement | Operation fails without accessing another configuration path. |
| Local asset mirror | data | ha-assets-sync | `/config/www/ha-assets/` | Mirror optionally available | Asset browsing is unavailable; the mirror remains unchanged. |

## Implementation namespace / naming identity

- Implementation namespace / naming identity: `mediacat_manager`

| Identity | Classification | Owner | Permitted use | Evidence |
| --- | --- | --- | --- | --- |
| `mediacat_manager` | owned | MediaCat Manager | Repository, App slug and implementation package | This profile and architecture |
| `/data/history/` | owned operational boundary | MediaCat Manager | App-private bounded catalogue snapshots | Architecture and implementation |
| `mediacat` | consumed | MediaCat | Home Assistant action domain and catalogue directory only | Provider-owned admin contract |
| `/config/www/ha-assets/` | consumed read-only | ha-assets-sync | Local asset discovery only | Architecture |

## Production and evidence route

- Production route: private Home Assistant App repository installed through the Home Assistant App store and exposed only through authenticated Ingress.
- Evidence route: exact repository/SHA validation plus runtime evidence from an authorised Home Assistant instance.
- Secrets and mutable-state boundary: no repository credential is stored; catalogue files and App-private history remain on the Home Assistant instance outside governed source.
- Validation evidence route: repository CI and runtime evidence recorded against the governing Linear issue.
- Known limitations: ASTV-277 establishes the shell and safety foundation; editing, history UI/revert and asset-picker features are deferred to ASTV-286.

## Governance and work control

- Linear project/team: `MediaCat Manager 2026.10` / `ASTV`
- Design parent: `ASTV-275`; bootstrap implementation: `ASTV-277` (Done); later editor issue: `ASTV-286`
- Applicable change classes: `Change: Code`, `Change: Architecture`, `Change: Documentation`, `Change: Governance`, `Change: Governance Tooling`
- Repository workflow: WF-01 issue PR targets persistent `beta`; accepted Beta content is promoted unchanged to `main` after validation.
