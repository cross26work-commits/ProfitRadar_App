# Backup and recovery runbook

## Scheduled backup

`backend/scripts/scheduled_backup.py` runs `pg_dump -Fc` through `age`, writes an atomic `.dump.age`, validates decryption with `pg_restore --list`, records SHA-256 and removes only expired artifacts matching its own filename pattern. Credentials are inherited from `/etc/profit-radar/backup.env`; they are absent from argv/logs/manifests. `deploy/profit-radar-backup.*` is disabled until the OWNER selects encrypted off-host storage, age key custody, retention, RPO/RTO and an alert receiver.

At least daily, copy the encrypted artifact and manifest to access-controlled off-host storage. Rotate DB and age credentials under a dual-control procedure; retain the old decryption identity until every retained artifact expires.

## Restore verification

Monthly and before a risky migration, select a retained artifact, verify SHA-256, decrypt only inside an approved disposable environment, restore with `--single-transaction --exit-on-error`, and compare schema/ACL/RLS/functions/indexes and row counts without printing customer rows. Record artifact hash, timestamp, target identity and PASS/FAIL. Destroying a restore target requires a separate reviewed cleanup action.

The repository’s `restore_isolated.py` proves the same backup→fresh-database→fingerprint flow for synthetic local data. It is not evidence that a future Production artifact is readable.

## Migration recovery

An error before migration COMMIT uses transaction rollback. After COMMIT, do not run historical down migrations or delete rows. Stop writers, preserve evidence, deploy a reviewed forward fix or restore the full verified backup into a controlled replacement database. Switching Production to a restored database requires its own approval.
