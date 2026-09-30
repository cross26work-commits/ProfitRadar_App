# Local migration manifest

The local launcher stages the ordered application migration chain and deliberately excludes only:

- `202609140001_remote_schema_forward.sql`
- `202609150001_remote_schema_forward_v2.sql`

Those files are mutually exclusive, one-shot repairs pinned to captured remote schema identities. They are retained unchanged as production evidence and must not be replayed in a fresh database after the ordinary migrations. V2 has already been applied to Production under its separate gate; V1 is historical and was not applied there.

`scripts/start-profit-radar.ps1` copies every other `*.sql` migration without changing its bytes, rejects unexpected or changed staged files, and starts project `profit-radar-local` only on loopback ports 54421/54422. The `202609060001_reply_logs_gmail_bridge.sql` migration supplies the legacy Gmail identity columns before the first index/function that uses them; existing databases with the exact text/null/default contract are a no-op.
