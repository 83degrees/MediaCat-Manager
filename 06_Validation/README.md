# Validation

Validation is recorded against the exact Git commit and governing Linear issue.

Repository validation includes:

- maintained unit tests under `05_Tests/`;
- the centrally projected governance check;
- Home Assistant App package-file checks in product CI;
- container build validation where the available runner supports it; and
- authorised Home Assistant install/start and Ingress reachability evidence for
  the exact Beta candidate.

For ASTV-317, repository validation also confirms that the sole deployable unit
is `haos_app → app_repository`, the authoritative package exists only at
`04_Implementation/haos/source/apps/mediacat_manager/`, root `repository.yaml`
remains the sole platform descriptor, path-sensitive tests and CI use the
canonical location, and the App version and package payload are unchanged by
the structural migration.

For ASTV-286, runtime validation additionally covers catalogue discovery,
provider-owned rejection of an invalid candidate, successful validation/save/
reload, pre-write snapshot retention, diff/restore, and read-only artwork
selection without traversal or mirror mutation.

Repository or CI success alone does not prove deployment/runtime state.
