# Codestra Tempo Corporate Features

## Mission

Tempo is the distributed tracing authority for Codestra. It connects browser/API activity, edge/gateway processing, Middleware commands, workers, databases and downstream provider calls into one incident path.

## Required path coverage

Target traces include frontend/API entry, Caddy, Kong, Middleware, Odoo, n8n, provider adapters, asynchronous workers, PostgreSQL, Redis and other material dependencies. Async work must preserve trace/correlation context where technically possible.

## Corporate trace contract

Every trace must carry safe resource attributes for service, version, environment, Codestra business, region and deployment. `correlation_id` remains a first-class application field alongside W3C trace context.

## Enterprise features

- OTLP ingestion;
- service graphs;
- span-metric generation support;
- Grafana trace-to-log and trace-to-metric links;
- tail sampling that retains errors and high-latency traces;
- environment-specific trace retention;
- deployment/version correlation;
- dependency latency analysis;
- provider failure tracing;
- asynchronous queue/worker trace continuity;
- incident trace search by safe business/service attributes.

## Privacy

Never collect Authorization headers, API keys, passwords, private keys, session tokens, raw PII or full sensitive request/response bodies. Instrumentation should record operation names, safe status/error information and timing instead of payloads.

## Beyvra trading rule

Beyvra traces may show the safe order/request lifecycle, market-data/provider latency, reconciliation and dependency errors. They must never record broker/exchange credentials, signing material, account secrets, raw order payloads or authoritative balances/positions/executions.

## Release rule

`temp.codestra.media` remains private/internal. Codestra configuration stays outside `upstream/`; merge does not authorize deployment or network exposure.
