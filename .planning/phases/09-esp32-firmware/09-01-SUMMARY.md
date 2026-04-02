---
phase: 09-esp32-firmware
plan: 01
subsystem: firmware
tags: [esp32, arduino, mqtt, nfc, ndef, adafruit-pn532, esp32mqttclient]

# Dependency graph
requires:
  - phase: 08-network-public-access
    provides: MQTT broker on LAN, public BASE_URL for token URLs
provides:
  - Complete ESP32 firmware aligned to server MQTT contract
  - Device auto-registration via devices/register topic
  - 30s heartbeat via devices/{id}/status topic
  - NFC tag writing from attendance/device/{id} subscription
  - LED connection indicator on GPIO 13
affects: []

# Tech tracking
tech-stack:
  added: [ESP32MQTTClient, Adafruit_PN532]
  patterns: [millis-based non-blocking loop, NDEF URI prefix codes, multi-block NFC writes]

key-files:
  created: [ESP32THINGS/SmartAttend/SmartAttend.ino]
  modified: []

key-decisions:
  - "Copied NFC write functions verbatim from POC -- hardware-tested code unchanged"
  - "Used #define config block at top of file for easy pre-flash customization"
  - "LED on GPIO 13 reflects MQTT connection state via IDF event handler"

patterns-established:
  - "ESP32 firmware config: all settings as #define at top of .ino file"
  - "MQTT topic contract: devices/register, devices/{id}/status, attendance/device/{id}"

requirements-completed: [FW-01, FW-02, FW-03, FW-04]

# Metrics
duration: 3min
completed: 2026-04-02
---

# Phase 9 Plan 1: ESP32 Firmware Summary

**Production ESP32 firmware with MQTT registration, 30s heartbeat, NFC tag writing from token URLs, and GPIO 13 LED indicator**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-04-02T10:30:00Z
- **Completed:** 2026-04-02T10:33:00Z
- **Tasks:** 2 (1 auto + 1 human-verify checkpoint)
- **Files modified:** 1

## Accomplishments
- Created complete SmartAttend.ino firmware aligned to server MQTT contract
- Device auto-registers on MQTT connect by publishing JSON to devices/register
- Heartbeat publishes "online" to devices/{id}/status every 30 seconds via millis()
- Subscribes to attendance/device/{id} with QoS 1 and writes received URL as NDEF URI to NFC tag
- LED on GPIO 13 toggles with MQTT connection state (on=connected, off=disconnected)
- NFC write functions copied verbatim from tested POC code

## Task Commits

Each task was committed atomically:

1. **Task 1: Create SmartAttend firmware with MQTT contract alignment and NFC write** - `d198606` (feat)
2. **Task 2: Verify firmware compiles and logic is correct** - checkpoint, approved by user

## Files Created/Modified
- `ESP32THINGS/SmartAttend/SmartAttend.ino` - Complete ESP32 firmware for SmartAttend attendance system

## Decisions Made
- Copied NFC write functions (writeNfc, rfField, resetNfc) verbatim from POC -- these are hardware-tested and must not be modified
- Used #define config block at top for WIFI_SSID, WIFI_PASS, MQTT_IP, DEVICE_ID -- easy to edit before flashing
- LED indicator on GPIO 13 driven by ESP-IDF MQTT event handler with IDF version compatibility check

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required. Users edit #define values at top of SmartAttend.ino before flashing.

## Next Phase Readiness
- ESP32 firmware is ready to flash onto physical devices
- Phase 9 is the final phase of v1.1 milestone
- All firmware requirements (FW-01 through FW-04) are implemented

---
*Phase: 09-esp32-firmware*
*Completed: 2026-04-02*

## Self-Check: PASSED
- SmartAttend.ino: FOUND
- Commit d198606: FOUND
