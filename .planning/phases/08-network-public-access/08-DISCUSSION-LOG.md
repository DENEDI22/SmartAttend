# Phase 8: Network & Public Access - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-02
**Phase:** 08-network-public-access
**Areas discussed:** Token URL config, Ngrok setup, Mosquitto LAN

---

## Token URL Config

| Option | Description | Selected |
|--------|-------------|----------|
| Replace SERVER_IP with BASE_URL | New env var BASE_URL=https://myapp.ngrok-free.app — replaces SERVER_IP entirely | ✓ |
| Keep SERVER_IP, add BASE_URL | Keep SERVER_IP for internal use, add BASE_URL that overrides for token URLs | |

**User's choice:** Replace SERVER_IP with BASE_URL
**Notes:** Clean replacement — no backward compatibility needed. BASE_URL includes scheme.

---

## Ngrok Setup

### Ngrok domain type

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed domain | Reserved ngrok domain — BASE_URL stays same across restarts | ✓ |
| Random each time | Free tier — random URL on each start | |

**User's choice:** Fixed domain

### Tunnel target

| Option | Description | Selected |
|--------|-------------|----------|
| Direct to :8000 | ngrok tunnels straight to server container on port 8000 | ✓ |
| Via reverse proxy | Add nginx/caddy between ngrok and FastAPI | |

**User's choice:** Direct to :8000
**Notes:** Simplest setup, no additional containers.

---

## Mosquitto LAN

| Option | Description | Selected |
|--------|-------------|----------|
| Standard setup | RPi on WiFi/Ethernet, no special firewall — port 1883 should just work | ✓ |
| Special config needed | Custom network situation | |

**User's choice:** Standard setup
**Notes:** Current docker-compose.yml port mapping (1883:1883) already sufficient.

---

## Claude's Discretion

- Ngrok container command/entrypoint configuration details
- Health checks for ngrok container
- Ngrok config file format vs CLI args

## Deferred Ideas

None.
