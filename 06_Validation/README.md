# Validation

ASTV-277 validation is recorded against the exact Git commit and Linear issue.

Repository validation includes:

- maintained unit tests under `05_Tests/`;
- the centrally projected governance check;
- Home Assistant App package-file checks in product CI;
- container build validation where the available runner supports it; and
- authorised Home Assistant install/start and Ingress reachability evidence for
  the exact Beta candidate.

Repository or CI success alone does not prove deployment/runtime state.
