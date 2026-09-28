# One-shot final gate: exact oracle integrated / validation pending

## Latest 2026-09-17

The authoritative JSON is now valid and byte SHA256 matches
1819D3032106DF74FC7709CC0C88EE6D0C0992F941BF74A16617A65515E751E9.
The final SQL embeds those exact JSONB values and compares every capture section:
constraints, indexes, event trigger, 25 functions, 11 SECURITY DEFINER entries,
views/triggers, 31 table states, global sync metadata/count, profile counts and
billing config absence. Any mismatch makes FINAL STOP. Legacy onboarding exact
baseline is KNOWN_REMEDIABLE, never represented as hardened. Policy and effective
ACL checks remain separate and unchanged in intent.

Current final SQL SHA256: BB10D080796F4792F31D48843E60E934355848332FE51BBFD114BF28780893C6.
The fixed v2 and preflight hashes below are still unchanged.

Latest attempted local regression: 48 passed / 28 setup errors / 0 skipped.
Docker Engine named pipe was unavailable. Errors are not passes. The prior test
counts below are historical and do not validate the new oracle integration.

New test_final_gate_oracle.py supplies independently captured metadata to the
observed-oracle CTE while leaving SQL comparison logic and local DB ownership,
column, policy and ACL checks intact. This is a metadata-fixture test, NOT proof
of a fully remote-equivalent PostgreSQL catalog. Capture supplies function MD5s,
not all reconstructable function bodies. The existing real-catalog tests continue
to reject the different repository baseline. Do not claim a remote DB PASS.

Resume locally with Docker available:

```powershell
$env:FINAL_GATE_LOCAL_TEST = 'allow-disposable-fixtures'
.\venv\Scripts\python.exe -m pytest tests/test_final_gate_oracle.py tests/test_final_gate.py tests/test_oracle_capture.py tests/test_remote_forward.py tests/test_sql_parse.py -q --tb=short
```

No remote connection/execution or commit/push. The following section describes
the previous, superseded missing-oracle checkpoint.

## Historical checkpoint

2026-09-16. No remote access/execution; no changes to migration/runtime/existing preflight.

## Delivered

supabase/remote_schema_forward_final_gate.sql has one SELECT statement with WITH CTEs and one result set: gate/status/detail and one final FINAL row. No source function bodies, credentials, customer values or identifiers are returned. Body pins are hex-encoded data literals sourced from the preflight, not executable calls.

The existing preflight SHA256 remains EDE597B72EE224447FFC8D6DE835C3AF90BFC8F439374CF2BDB34920D730D8D5.
The v2 SHA256 remains B5152C99E1368989FB35203686DB3D29CB395362C1E8282D6F1F9BBB8EDC86F0.
Tests independently verify both files, policy oracle and canonical capture.

## Missing approval input — do not use as an APPLY READY assertion

The authoritative preflight reports, but does not pin, the exact approved:

- ensure_rls / rls_auto_enable event-trigger/function metadata and body digest.
- Legacy constraints/indexes.
- Remaining nine existing function contracts, body digests and effective privileges (two onboarding functions are pinned).
- Views, ordinary triggers and SECURITY DEFINER inventory.

The user's preceding PASS summary does not supply these definitions. Repository fixture output cannot replace a remote oracle. These gates deliberately return STOP, so expected baseline FINAL PASS is NOT delivered. Provide the saved read-only metadata snapshots with exact definitions/digests to finish the approval comparisons. Do not paste secrets or customer rows.

Existing billing_runtime_config conservatively returns STOP: this version supports the approved absent state, not an automatically approved existing configuration. Its exact approved structure/state still needs completion. These are unfinished checks, not external operational failures or PASS.

The source uses direct profiles/gmail_sync_runs aggregate queries: those two legacy tables must exist to execute the query. It also deparses defaults under the caller's search_path, like the authoritative preflight; if auth is visible, uid() differs from the approved auth.uid() and STOP is expected. This script intentionally contains no session configuration statements.

## Local execution evidence

Command from backend (Docker CLI on PATH):

```powershell
$env:FINAL_GATE_LOCAL_TEST = 'allow-disposable-fixtures'
.\venv\Scripts\python.exe -m pytest tests/test_final_gate.py tests/test_remote_forward.py tests/test_sql_parse.py -q --tb=short
```

47 passed, 0 skipped. Ten new tests include AST SelectStmt / forbidden executable token checks, immutable source pins, fresh disposable baseline, default drift, unknown policy, nonzero global runs, unknown grantee, canonical whitespace, compatible/incompatible checkout.

Test fixture reuses the explicit Docker project/endpoint identity guards and NEW synthetic DB builder. It stops before migration. Each mutation is rolled back and schema fingerprint compared. Fixture transactions configure search_path to the approved deparsing context; the gate itself does not configure it.

The baseline test asserts supported individual gates PASS and FINAL STOP because approval inputs are absent. This is NOT the user-requested expected-baseline FINAL PASS test and must not be counted as completion of that requirement.

No real Auth, remote SQL Editor, remote migration, Gmail, Stripe, commit or push was performed.
