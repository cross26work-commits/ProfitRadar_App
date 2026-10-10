# Profit Radar: owner decisions and approvals

2026-10-11 update (supersedes Gate A step 1 and the last paragraph below): the owner-approved, target-only STAGED frontend Discard is complete. Patch `{}` and applied services `[]` were verified. The owner has accepted the dev-only npm advisory as a documented risk for **preparation**, not public release; the actual production image must be checked for absence of development dependencies before publication. The next decision is separate approval of the exact commit set in `docs/RAILWAY_RELEASE_CANDIDATE_20261011.md`; commit/push remain prohibited. IaC still pins the prior SHA and its provisional 3-add plan must not be applied or deployed. After a new reviewed SHA exists, update that pin and re-run the read-only plan. Secret variables need a name-only inventory and a no-delete/no-overwrite plan review because Railway reports `variables: managed (default)`. The 60 Docker-gated DB/Auth skips remain a pre-publication verification gate, not a pass.

Updated 2026-10-10. **No action below is authorized by this file.** Never send an API key, password, OAuth code or customer row through chat. Use Railway/Supabase/Google/Stripe secret and admin interfaces. Target identities: Railway `812c77be-b93b-4db6-9338-1bc43f415707` / `production`; Supabase `runxnxvwjqblyzdcegay`; GitHub `cross26work-commits/ProfitRadar_App`.

## Gate A — reconcile and freeze (no production change)

1. Review the single STAGED `frontend` patch in Railway. It points to the expected repo and `/frontend` but has **no branch**; the masked Node version is unverified. The safe default is to supersede **only this unapplied patch** after separate explicit approval, then re-inventory and re-plan; see `docs/RAILWAY_STAGED_RECONCILIATION.md`. Do not press **Deploy Changes** or apply the current 3-add plan while both coexist.
2. Review the local `multidict`/frontend lock fixes and the dev-only, unpatched `braces` advisory. Decide the security exception or wait for an upstream fix. Review the 60 disposable DB/Auth skips separately; Docker Desktop launched normally but Engine remains unavailable on this host.
3. Approve a new reviewed commit/push/artifact if these local changes are to be deployed. Frozen `9099d9a...` is still the GitHub release head and **does not include** today's remediation. The assistant has not committed or pushed.

## Gate B — external configuration (owner in provider dashboards)

1. Choose Railway paid plan and cost cap; create one backend, one frontend, one private worker only after Gate A. Put variables listed in `docs/PRODUCTION_ENVIRONMENT_MATRIX.md` into service-specific sealed settings; no secret in IaC or repository. Verify backend `/ready` only after LIVE billing and DB approval state match.
2. Provide and approve actual seller legal name, support contact, privacy/terms/refund/retention wording, 7-day card-required trial and independent legal sign-off. Set publication flags only after approval; do not turn on public sale to hide missing information.
3. Arrange Google brand/domain/Restricted Gmail scope verification (and independent assessment if required), Stripe LIVE account/¥19,800 JPY inclusive monthly Price/webhook, alert receiver/on-call, and encrypted off-host backup key custody/restore drill. Each is a distinct external gate; test keys do not substitute.

## Gate C — batch of consequential approvals (request only when READY)

The release manager must present the exact plan, project/environment IDs, immutable SHA, expected cost and rollback for **each** of: Railway service apply/deploy, Stripe LIVE DB promotion, Railway custom domains plus お名前.com DNS, controlled provider E2E, and publication. Approval for one is not approval for the others. Until then: no production DB write, LIVE charge, actual Gmail send, DNS change, Google submission, key rotation, commit/push or deploy.

## Current owner decision needed first

Approve or reject the exact **STAGED frontend supersession design** in `docs/RAILWAY_STAGED_RECONCILIATION.md`; this is a future decision, not permission to perform it now. The current read-only plan ignores that staged patch and proposes an additional `frontend` service. A single identity and branch/commit binding must be proven before service creation is authorized.
