# MediaCat Manager Architecture

## Status and authority

- State: ASTV-286 implementation candidate pending human acceptance; ASTV-277 is the accepted bootstrap baseline
- Design parent: `ASTV-275`
- Bootstrap issue: `ASTV-277`
- Editor implementation: `ASTV-286`

This document is the semantic architecture authority for MediaCat Manager.
ASTV-277 established the product, App, Ingress and safety boundaries. ASTV-286
implements the typed catalogue editor, local history/revert and read-only asset
picker within those accepted boundaries.

## Product boundary

MediaCat Manager is a separate governed product in a public repository. It owns
the local administration experience and file-safety mechanics. MediaCat remains
the sole authority for catalogue schema meaning, validation, runtime loading,
capability reporting and transactional active-registry reload.

After installation, normal App operation has no dependency on GitHub. Install
and update use the public App repository anonymously, and no repository
credential is present in the Home Assistant App.

## Runtime components

1. Home Assistant Supervisor installs and starts the `mediacat_manager` App.
2. Authenticated Home Assistant Ingress forwards requests to the App's HTTP
   listener on container port `8099`.
3. The Ingress single-page UI discovers catalogues, edits schema-v4 items and
   categories through typed controls, browses history and selects local artwork.
4. The application calls MediaCat only through the provider-owned
   `MEDIACAT_ADMIN_INTERFACE.md` capability, validation and reload actions.
5. Filesystem operations pass through the path-policy boundary before any read
   or write primitive is invoked.
6. The read-only asset browser lists and serves supported image files beneath
   the fixed asset root; no asset mutation endpoint exists.

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
Home Assistant configuration write surface. Each catalogue identity receives a
separate directory and retains the 20 most recent timestamped pre-replacement
snapshots. History supports inspection by unified diff and validated restore.

## Atomic catalogue write strategy

The replacement workflow is:

1. validate the complete candidate through MediaCat;
2. resolve and verify the destination under the catalogue root;
3. preserve the current file to the Manager-owned history boundary;
4. write candidate bytes to a new file in the same directory;
5. flush the file and synchronize it to storage;
6. atomically replace the destination with the same-filesystem temporary file;
7. synchronize the parent directory where supported; and
8. request MediaCat transactional reload through its supported contract.

A reload failure does not make MediaCat Manager the runtime authority: MediaCat
retains its prior in-memory registry, while the Manager reports the failure and
retains filesystem/history evidence.

The save and restore APIs expose this workflow only for a catalogue discovered
by authoritative in-file `catalogue_id`. A filename is retained as storage
location but never promoted to logical identity.

## MediaCat administration dependency

The sole supported provider boundary is:

`83degrees/MediaCat/03_Contracts/MEDIACAT_ADMIN_INTERFACE.md` version `1.0.0`.

The client discovers `admin_interface_version`, supported catalogue
schema versions and the provider's catalogue directory. It must submit complete
candidate YAML to `mediacat.validate_catalogue` and may request
`mediacat.reload_catalogue` only after a successful atomic write. It must ignore
unknown additive response fields and fail closed on an unsupported interface
version.

MediaCat Manager does not copy MediaCat validation logic or infer schema
authority from filenames.

## Ingress and HTTP boundary

The App binds only its internal Ingress port and declares `ingress: true` with
no host port. The application exposes:

- `GET /` plus same-origin static assets — typed editor UI;
- `GET /health` — process liveness/readiness;
- `GET /api/bootstrap` and `/api/capabilities` — non-sensitive product and provider capability state;
- `GET /api/catalogues[/<catalogue_id>]` — safe discovery and typed document retrieval;
- `POST /api/catalogues/<catalogue_id>/save` — provider validation, snapshot, atomic replacement and reload;
- `GET /api/catalogues/<catalogue_id>/history` plus snapshot diff — bounded history inspection;
- `POST /api/catalogues/<catalogue_id>/history/<snapshot>/restore` — validated restore and reload;
- `GET /api/assets` and `/api/asset` — read-only image discovery and delivery beneath the asset root.

All other methods and paths are rejected. Request bodies are size-bounded and
must be JSON where applicable. Responses apply restrictive content
security, framing, MIME-sniffing and referrer headers. Authentication remains
owned by Home Assistant Ingress.

## Failure boundaries

- Missing or incompatible MediaCat capability leaves the shell available and prevents validation/save/reload.
- Missing catalogue or asset roots are reported without falling back to another
  Home Assistant path.
- Traversal, absolute paths and resolved symlink escapes fail before I/O.
- Atomic-write failure leaves the previous destination in place unless the
  underlying platform itself violates atomic replace semantics.
- Validation failure produces no snapshot and no catalogue write.
- Reload failure leaves the new validated file and its pre-write snapshot as
  evidence while MediaCat retains its prior in-memory registry.
- Restore is subject to the same MediaCat validation, snapshot and reload
  sequence as an ordinary save.
- No endpoint can mutate the local asset mirror or an unrelated Home Assistant path.

## Typed editing model

The UI preserves complete document mappings while providing typed controls for
schema-v4 item identity, labels, supported media types and type metadata,
descriptions, tags, artwork, execution methods and categories. Adding, editing
and deleting records occurs in the client working copy; only a complete document
submitted to MediaCat validation may enter the storage transaction. The Manager
does not interpret those controls as schema authority and does not implement a
parallel schema validator.
