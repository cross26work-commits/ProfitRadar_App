# Monitoring and incident response

## Signals

- `runtime_probe`: public frontend, backend `/health`, backend `/ready`, and worker `/health` plus `/ready`. Local/systemd uses loopback; Railway uses the explicitly gated private-only `*.railway.internal` endpoint and no public worker domain.
- `sync_worker`: structured batch success/failure and consecutive failure count; no URL/header/body/tenant value.
- `maintenance`: unresolved/unknown sends, pending deletions, reserved AI, stale Gmail locks, recent/stuck Gmail runs and recent failed/fallback AI runs. Counts only.
- Reverse-proxy/API monitoring must alert on non-2xx `/billing/webhook`; do not include request bodies or `Stripe-Signature`.
- `deploy/monitoring-alerts.yaml` is the vendor-neutral severity/condition contract. The OWNER selects an HTTPS receiver and an external missed-heartbeat monitor; a process cannot alert when its whole host is down.

## Response

1. Critical health/readiness or credential exposure: stop public traffic and workers, preserve redacted logs, start an incident ticket and invoke application-artifact rollback.
2. Stale Gmail/company work: do not unlock based only on elapsed time. Inspect provider/DB state and use the operator recovery procedure with workers stopped.
3. Unknown send/payment/provider outcome: never automatically repeat the side effect. Reconcile the provider object, record the ticket, then use the reviewed recovery operation.
4. DB readiness: stop writers; verify provider health and connection configuration. Do not replay v2, run blind `db push`, or delete data.

Alert payloads contain only fixed event names, severity and integer counts/status labels. Tokens, email, customer IDs, URLs, provider bodies and exception text are prohibited.
