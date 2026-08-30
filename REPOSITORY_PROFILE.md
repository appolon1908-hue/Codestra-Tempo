# Repository Profile — `Codestra-Tempo`

## Identity

- **Repository:** `appolon1908-hue/Codestra-Tempo`
- **Category:** Observability backend — traces
- **Visibility:** `public`
- **Default branch:** `main`
- **Canonical hostname:** `temp.codestra.media`
- **Exposure:** Internal/private only; no public native API
- **Authority:** Primary distributed-trace ingestion, storage, retention, query, and correlation authority

## Purpose

Stores and serves approved distributed traces for debugging, latency analysis, dependency mapping, exemplars, and correlation from Grafana.

## Owns

- Tempo receivers, storage, retention, compaction, limits, query, and tenant policy
- Trace search and metrics-generator behavior where approved
- Tempo validation, backup/restore, upgrade, and rollback source

## Does not own

- Application instrumentation or trace collection agents
- Log or metrics storage
- Public unauthenticated trace ingestion or query access

## Key integrations

- OpenTelemetry Collector and Alloy
- Grafana
- Prometheus exemplars/metrics where approved
- Object/local storage according to environment design

## Current priorities

1. Finalize storage, retention, compaction, resource limits, and tenancy
2. Enforce bounded trace attributes and sensitive-data redaction upstream
3. Prove ingestion, query, backpressure, outage recovery, exemplars, and correlation
4. Add backup/restore, upgrade, downgrade, and rollback evidence

## Governance and safety

- Promotion model: `feature/docs/fix/security/upgrade -> development -> test -> staging -> production -> main`.
- Native port `3200` and trace receivers must remain private; `temp.codestra.media` must not expose Tempo publicly.
- Never commit storage credentials, private keys, tokens, customer payloads, or secret-bearing trace fixtures.
- New trace sources require attribute, retention, cardinality, and ownership review.
- Merge does not start Tempo, activate receivers, change storage, expose ports, or deploy software.

## Account-wide catalog

See `appolon1908-hue/documentaions/REPOSITORY_CATALOG.md`.
