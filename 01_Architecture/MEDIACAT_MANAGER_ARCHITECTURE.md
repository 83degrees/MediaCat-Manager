# MediaCat Manager Architecture

## Status and authority

- State: approved target pending ASTV-277 acceptance
- Design parent: `ASTV-275`
- Bootstrap issue: `ASTV-277`
- Later editor implementation: `ASTV-286`

This document is the semantic architecture authority for MediaCat Manager. The
bootstrap deliberately proves the product, App, Ingress and safety boundaries
without implementing the catalogue editor assigned to ASTV-286.

## Product boundary

MediaCat Manager is a separate governed product and private repository. It owns
the local administration experience and file-safety mechanics. MediaCat remains
the sole authority for catalogue schema meaning, validation, runtime loading,
capability reporting and transactional active-registry reload.

Normal operation has no dependency on GitHub and no private-repository
credential is present in the Home Assistant App.

## Runtime components

1. Home Assistant Supervisor installs and starts the `mediacat_manager` App.
2. Authenticated Home Assistant Ingress forwards requests to the App's HTTP
   listener on container port `8099`.
3. The bootstrap web shell reports readiness and boundary information. It has no
   edit, save, restore or asset-selection controls.
4. Future editor work may call MediaCat only through the provider-owned
   `MEDIACAT_ADMIN_INTERFACE.md` actions.
5. Filesystem operations pass through the path-policy boundary before any read
   or write primitive is invoked.

## Filesystem and privilege model

| Host purpose | Container path | Access policy | Owner |
| --- | --- | --- | --- |
| MediaCat catalogues | `/homeassistant/mediacat/catalogues/` | Read and controlled atomic replacement only | Local HA instance / MediaCat runtime |
| Local asset mirror | `/homeassistant/www/ha-assets/` | Read only | ha-assets-sync |
| Manager history | `/data/history/` | Read/write; bounded snapshots keyed by `catalogue_id` | MediaCat Manager |

Home Assistant currently exposes its configuration mapping at directory scope.
The Manager therefore applies a deny-by-default application boundary: all
catalogue and asset paths must be resolved beneath their fixed roots, symlink
escapes and traversal are rejected, assets have no write API, and the atomic
writer accepts destinations only from the catalogue policy. No general-purpose
file endpoint or caller-supplied absolute path exists.

App-private `/data/history/` is used for history so snapshots do not broaden the
Home Assistant configuration write surface. ASTV-286 may implement retention
and user-facing history/revert on this fixed boundary but must not change the
boundary silently.

## Atomic catalogue write strategy

The approved replacement primitive is:

1. resolve and verify the destination under the catalogue root;
2. write candidate bytes to a new file in the same directory;
3. flush the file and synchronize it to storage;
4. preserve the current file to the Manager-owned history boundary when the
   editor workflow is implemented;
5. atomically replace the destination with the same-filesystem temporary file;
6. synchronize the parent directory where supported; and
7. request MediaCat transactional reload through its supported contract.

Validation must occur through MediaCat before step 2 once editor/save behaviour
is introduced. A reload failure does not make MediaCat Manager the runtime
authority: MediaCat retains its prior in-memory registry, while the Manager
reports the failure and retains filesystem/history evidence.

ASTV-277 supplies and tests the path-confined atomic replacement primitive but
does not expose it through the Ingress shell.

## MediaCat administration dependency

The sole supported provider boundary is:

`83degrees/MediaCat/03_Contracts/MEDIACAT_ADMIN_INTERFACE.md` version `1.0.0`.

The future client must discover `admin_interface_version`, supported catalogue
schema versions and the provider's catalogue directory. It must submit complete
candidate YAML to `mediacat.validate_catalogue` and may request
`mediacat.reload_catalogue` only after a successful atomic write. It must ignore
unknown additive response fields and fail closed on an unsupported interface
version.

MediaCat Manager does not copy MediaCat validation logic or infer schema
authority from filenames.

## Ingress and HTTP boundary

The App binds only its internal Ingress port and declares `ingress: true` with
no host port. The bootstrap exposes:

- `GET /` — static shell explaining bootstrap scope;
- `GET /health` — process liveness/readiness;
- `GET /api/bootstrap` — non-sensitive product and boundary metadata.

All other methods and paths are rejected. Responses apply restrictive content
security, framing, MIME-sniffing and referrer headers. Authentication remains
owned by Home Assistant Ingress.

## Failure boundaries

- Missing MediaCat capability leaves the shell available and prevents editing.
- Missing catalogue or asset roots are reported without falling back to another
  Home Assistant path.
- Traversal, absolute paths and resolved symlink escapes fail before I/O.
- Atomic-write failure leaves the previous destination in place unless the
  underlying platform itself violates atomic replace semantics.
- No bootstrap endpoint can mutate catalogue, history or asset state.

## Deferred ASTV-286 scope

ASTV-286 owns catalogue discovery/selection, typed editing, validation UX,
save/reload orchestration, bounded snapshot retention, history/diff/revert and
the visual read-only asset picker. Those features are intentionally absent from
this bootstrap.
