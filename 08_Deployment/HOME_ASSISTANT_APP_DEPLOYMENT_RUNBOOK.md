# MediaCat Manager Home Assistant App Deployment Runbook

This runbook applies the approved
`HOME_ASSISTANT_APP_DEPLOYMENT_STANDARD.md` to MediaCat Manager. It is an
operator aid and does not grant publication, deployment, rollback or promotion
authority.

## 1. Operation identity

- Governing Linear issue: `<ISSUE-ID>`
- Target Home Assistant environment: `<environment>`
- Operation: `<Beta install | Beta update | stable install | stable update | rollback>`
- Repository source: `<https://github.com/83degrees/MediaCat-Manager[#branch]>`
- Selected branch: `<beta | main>`
- Git candidate SHA: `<full SHA>`
- App slug/version: `mediacat_manager / <version>`
- Prior working source/SHA/version: `<source / SHA / version>`
- Operator: `<person or authorised agent>`

Beta uses `https://github.com/83degrees/MediaCat-Manager#beta`. Stable
installation or update uses accepted `main` content from
`https://github.com/83degrees/MediaCat-Manager`.

## 2. Required authority

- [ ] The issue is at the applicable governed deployment gate.
- [ ] Human acceptance and required validation remain valid for the exact candidate.
- [ ] Explicit deployment authority identifies the repository, candidate, environment and purpose.
- [ ] The operation does not change repository visibility; any future visibility-model change requires separately governed authority.
- Authorisation reference and time: `<Linear comment/reference and timestamp>`

## 3. Repository and deployment preflight

- [ ] Root `repository.yaml` validates and is the sole root platform descriptor.
- [ ] The only App package is `04_Implementation/haos/source/apps/mediacat_manager/` and its `config.yaml` validates.
- [ ] No duplicate App implementation exists under `04_Source/` or at repository root.
- [ ] Repository source and selected branch resolve to the recorded SHA.
- [ ] App version and build inputs correspond to the candidate and are obtainable by Supervisor.
- [ ] `83degrees/MediaCat-Manager` is publicly readable and Supervisor can obtain it anonymously without repository credentials.
- [ ] The candidate and reachable repository content are suitable for the established public distribution model.
- [ ] The intended target is the authorised Home Assistant environment.
- [ ] App configuration and App-private `/data/history/` have a usable backup or verified preservation route.
- [ ] Catalogue files under `/homeassistant/mediacat/catalogues/` are preserved independently of the App package update.
- [ ] The prior working source, candidate and App version are known and usable for rollback.
- Preflight evidence: `<references>`

## 4. Repository visibility

The established deployment model uses the public
`83degrees/MediaCat-Manager` repository. Deployment does not open or close a
visibility window and must not change repository visibility as an incidental
installation or recovery step.

- [ ] Public visibility was observed before deployment.
- [ ] Anonymous access resolves the recorded repository source, branch and candidate.
- Public visibility verified at: `<timestamp and evidence>`

If the repository is unexpectedly private or anonymous access fails, stop the
deployment and record the mismatch. Do not change visibility under this runbook;
use separately governed authority to change the deployment model or repository
visibility.

## 5. Install or update

1. Add, repair or refresh only the recorded repository source in the intended Home Assistant environment.
2. Refresh the App store and verify the selected source and `mediacat_manager` App.
3. Install or update only the recorded App version/candidate.
4. Start or restart the App as required.
5. Verify installed version, running state, authenticated Ingress reachability and sufficient deployed content to bind the result to the recorded Git candidate.
6. Exercise the issue-specific runtime checks without modifying unrelated catalogue or asset state.

- Repository identity/source observed: `<value>`
- Installed App slug/version observed: `<value>`
- Candidate/deployed-content verification: `<evidence>`
- Runtime checks: `<evidence>`
- Result: `<passed | failed>`

## 6. Post-deployment visibility verification

- [ ] The repository remains publicly readable as expected.
- [ ] No repository-visibility change was performed during deployment.
- Public visibility verified at: `<timestamp and evidence>`

Do not report the operation complete while the observed visibility differs from
the recorded public deployment model.

## 7. Failure and rollback

If clone, refresh, install, update, startup or candidate verification fails:

1. retain non-secret diagnostic evidence;
2. preserve Supervisor repository/App identity, App configuration, catalogue files and App-private history;
3. restore the recorded prior working source, candidate and App version with required authority;
4. verify installed version, running state, Ingress reachability, data preservation and expected public visibility; and
5. record the failure and rollback result against the governing Linear issue.

Do not change repository visibility as an ad hoc recovery action.

Do not remove and re-add the repository or reinstall the App as the default
rollback when that could detach the App or discard App-private data.

- Failure evidence: `<reference or N/A>`
- Rollback authority: `<reference or N/A>`
- Rollback result and verification: `<reference or N/A>`

## 8. Closure evidence

- [ ] Issue, environment, repository source, branch, App slug/version and Git SHA are recorded.
- [ ] Preflight and install/update results are recorded.
- [ ] Running state, Ingress and deployed-candidate identity are verified.
- [ ] Expected public visibility and anonymous repository access are recorded.
- [ ] Data preservation and any rollback result are recorded.
- [ ] No secret material is retained in the evidence.
- [ ] State-changing actions after validation received proportionate revalidation.

Closure record: `<Linear comment/link>`
