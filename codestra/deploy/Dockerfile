# syntax=docker/dockerfile:1.7

ARG GO_BUILDER_IMAGE
ARG TEMPO_BASE_IMAGE

FROM ${GO_BUILDER_IMAGE} AS healthcheck-builder
WORKDIR /src
COPY codestra/deploy/healthcheck.go ./healthcheck.go
RUN CGO_ENABLED=0 GOOS=linux go build \
      -trimpath \
      -ldflags='-s -w -buildid=' \
      -o /out/tempo-healthcheck \
      ./healthcheck.go \
    && /out/tempo-healthcheck 2>&1 | grep -q 'readiness request failed'

FROM ${TEMPO_BASE_IMAGE}
LABEL org.opencontainers.image.title="Codestra Corporate Tempo"
LABEL org.opencontainers.image.description="Private multi-tenant tracing authority for Codestra-managed businesses"
LABEL org.opencontainers.image.vendor="Codestra"

COPY --from=healthcheck-builder --chown=10001:10001 --chmod=0555 /out/tempo-healthcheck /tempo-healthcheck
COPY --chown=10001:10001 --chmod=0444 codestra/config/tempo.yaml /etc/tempo/tempo.yaml
COPY --chown=10001:10001 --chmod=0444 codestra/config/overrides.yaml /etc/tempo/overrides.yaml

USER 10001:10001
