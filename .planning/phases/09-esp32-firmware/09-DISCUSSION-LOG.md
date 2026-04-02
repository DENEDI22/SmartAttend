# Phase 9: ESP32 Firmware - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-02
**Phase:** 09-esp32-firmware
**Areas discussed:** MQTT library, Config approach, Firmware location, NFC handling

---

## MQTT Library

| Option | Description | Selected |
|--------|-------------|----------|
| Keep ESP32MQTTClient | Already tested in POC, wraps ESP-IDF MQTT, lambda subscriptions | ✓ |
| Switch to PubSubClient | Most popular Arduino MQTT lib, simpler API, more community support | |

**User's choice:** Keep ESP32MQTTClient
**Notes:** Known working with this hardware, no reason to switch.

---

## Config Approach

| Option | Description | Selected |
|--------|-------------|----------|
| #define in main .ino | Simple, all config at top of file, easy to change before flashing | ✓ |
| Separate config.h | Gitignored header, cleaner separation | |

**User's choice:** #define in main .ino

---

## Firmware Location

| Option | Description | Selected |
|--------|-------------|----------|
| ESP32THINGS/SmartAttend/ | New directory alongside POC-Code, clean separation | ✓ |
| Update POC-Code in place | Rewrite ESP32.ino directly, POC becomes production | |

**User's choice:** ESP32THINGS/SmartAttend/

---

## NFC Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Keep as-is | POC NFC code works — copy with minimal changes | ✓ |
| Adjustments needed | Changes to the NFC flow | |

**User's choice:** Keep as-is

---

## Claude's Discretion

- loop() structure and timing
- millis() vs delay() for heartbeat
- Error handling and reconnection
- Serial debug logging

## Deferred Ideas

None.
