# Phase 9: ESP32 Firmware - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Rewrite ESP32 firmware to align with the server's MQTT contract. The firmware must: register on connect, heartbeat every 30s, subscribe to token URLs and write them as NDEF URIs to NFC tags, and indicate MQTT connection status via an LED on GPIO 13. Lux sensor is explicitly excluded.

</domain>

<decisions>
## Implementation Decisions

### MQTT Library
- **D-01:** Keep `ESP32MQTTClient` library from the POC. Already tested and working with this hardware.
- **D-02:** Rewrite MQTT logic to match server contract:
  - On connect: publish `{"device_id": "{DEVICE_ID}"}` to `devices/register`
  - Every 30s: publish `"online"` to `devices/{DEVICE_ID}/status`
  - Subscribe to `attendance/device/{DEVICE_ID}` (QoS 1) for token URLs
- **D-03:** No lux sensor publishing — excluded from this milestone.

### Configuration
- **D-04:** Use `#define` directives at top of main `.ino` file for all config: `WIFI_SSID`, `WIFI_PASS`, `MQTT_IP`, `MQTT_PORT`, `DEVICE_ID`.
- **D-05:** Keep it simple — no separate config header, no runtime configuration.

### Firmware Location
- **D-06:** Create new directory `ESP32THINGS/SmartAttend/` for production firmware.
- **D-07:** File named `SmartAttend.ino` (Arduino convention: filename matches directory name).
- **D-08:** POC code at `ESP32THINGS/POC-Code/ESP32.ino` is preserved as reference, not modified.

### NFC Handling
- **D-09:** Copy NFC write flow from POC as-is: reset module, detect card, authenticate with NDEF key, build NDEF URI record, write blocks.
- **D-10:** NDEF URI prefix codes for http:// and https:// preserved from POC.
- **D-11:** `rfField()` toggle and `resetNfc()` reused from POC.

### LED Indicator
- **D-12:** GPIO 13 as output pin for MQTT connection indicator.
- **D-13:** LED on when MQTT connected, off when disconnected.
- **D-14:** Update LED state in MQTT connect/disconnect callbacks.

### Claude's Discretion
- Exact loop() structure (polling interval, NFC detection timing)
- Whether to use millis()-based or delay()-based timing for heartbeat
- Error handling and reconnection strategy details
- Serial debug logging verbosity

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Server MQTT contract (firmware must match these exactly)
- `app/services/mqtt.py` — Server-side MQTT handlers: `_handle_register` (expects JSON `{"device_id": "..."}` on `devices/register`), `_handle_heartbeat` (expects any payload on `devices/{id}/status`), token publish on `attendance/device/{id}`
- `dummy_client/main.py` — Python implementation of the same contract (reference for topic names, QoS levels, message formats)

### POC firmware (source material for NFC and WiFi code)
- `ESP32THINGS/POC-Code/ESP32.ino` — Tested NFC write flow, WiFi init, ESP32MQTTClient usage patterns. NFC code to be copied; MQTT code to be rewritten.

### Hardware
- `ESP32MQTTClient` library — ESP-IDF MQTT wrapper with lambda-based subscriptions
- `Adafruit_PN532` library — I2C NFC reader/writer (pins 16, 17 for SDA/SCL)
- GPIO 13 — LED indicator pin
- GPIO 15 — NFC module RESET pin

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ESP32.ino:writeNfc()` — Complete NDEF URI write implementation with prefix detection, multi-block writes, NDEF TLV construction. Copy directly.
- `ESP32.ino:rfField()` — RF field toggle for power management. Copy directly.
- `ESP32.ino:resetNfc()` — Hardware reset via GPIO 15 + re-init. Copy directly.
- `ESP32.ino:initWiFi()` — WiFi STA mode connection with retry loop. Copy directly.
- `ESP32.ino:initNfc()` — PN532 I2C init with firmware check. Copy directly.

### Established Patterns
- ESP32MQTTClient: `mqttClient.setURI()`, `mqttClient.loopStart()`, lambda subscriptions in `onMqttConnect`
- NFC: I2C on pins 16/17, RESET on pin 15, NDEF key `{0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7}`

### Integration Points
- MQTT broker at `<RPi-IP>:1883` (exposed by Phase 8)
- Token URLs arrive as plain text payload on `attendance/device/{DEVICE_ID}` topic
- Server expects `{"device_id": "..."}` JSON on `devices/register` topic
- Server expects any payload on `devices/{id}/status` for heartbeat

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 09-esp32-firmware*
*Context gathered: 2026-04-02*
