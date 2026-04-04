// SmartAttend ESP32 Firmware
// NFC-based attendance check-in device
// Registers with server via MQTT, receives token URLs, writes them as NDEF URIs to NFC tags.

#include "WiFi.h"
#include <Wire.h>
#include <Adafruit_PN532.h>
#include "ESP32MQTTClient.h"

// ---------------------------------------------------------------------------
// Configuration — edit these before flashing
// ---------------------------------------------------------------------------
#define WIFI_SSID          "YOUR_SSID"
#define WIFI_PASS          "YOUR_PASSWORD"
#define MQTT_IP            "192.168.1.100"
#define MQTT_PORT          1883
#define DEVICE_ID          "esp32-001"
#define NFC_RESET_PIN      15
#define LED_PIN            13
#define HEARTBEAT_INTERVAL_MS 30000  // 30 seconds

// Derived topics (compile-time string concatenation)
#define MQTT_URI           "mqtt://" MQTT_IP
#define TOPIC_REGISTER     "devices/register"
#define TOPIC_HEARTBEAT    "devices/" DEVICE_ID "/status"
#define TOPIC_ATTENDANCE   "attendance/device/" DEVICE_ID

// ---------------------------------------------------------------------------
// Global objects
// ---------------------------------------------------------------------------
Adafruit_PN532 nfc(16, 17);  // I2C on pins 16 (SDA), 17 (SCL)
ESP32MQTTClient mqttClient;
unsigned long lastHeartbeat = 0;
bool mqttConnected = false;

// ---------------------------------------------------------------------------
// Forward declarations
// ---------------------------------------------------------------------------
void writeNfc(char* link);
void rfField(bool on);
void resetNfc();

// ---------------------------------------------------------------------------
// WiFi initialisation (from POC)
// ---------------------------------------------------------------------------
void initWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to WiFi ..");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print('.');
    delay(1000);
  }
  Serial.println(WiFi.localIP());
}

// ---------------------------------------------------------------------------
// NFC initialisation (from POC, verbatim)
// ---------------------------------------------------------------------------
void initNfc() {
  Wire.begin(16, 17);
  nfc.begin();
  uint32_t versiondata = nfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.println("PN532 nicht gefunden!");
    while (1)
      ;
  }
  nfc.SAMConfig();
}

// ---------------------------------------------------------------------------
// MQTT initialisation
// ---------------------------------------------------------------------------
void initMqtt() {
  mqttClient.setURI(MQTT_URI);
  mqttClient.loopStart();
}

// ---------------------------------------------------------------------------
// MQTT connect callback — register device and subscribe to token topic
// ---------------------------------------------------------------------------
void onMqttConnect(esp_mqtt_client_handle_t client) {
  if (mqttClient.isMyTurn(client)) {
    // FW-01: Publish registration JSON to devices/register
    mqttClient.publish(TOPIC_REGISTER, "{\"device_id\":\"" DEVICE_ID "\"}", 0, false);
    Serial.println("Published registration to " TOPIC_REGISTER);

    // FW-03: Subscribe to attendance token URLs (QoS 1)
    mqttClient.subscribe(TOPIC_ATTENDANCE, [](const std::string& payload) {
      Serial.printf("Token URL received: %s\n", payload.c_str());
      resetNfc();
      char* str = strdup(payload.c_str());
      writeNfc(str);
      free(str);
    }, 1);
    Serial.println("Subscribed to " TOPIC_ATTENDANCE);
  }
}

// ---------------------------------------------------------------------------
// MQTT event handler — LED control on connect/disconnect
// ---------------------------------------------------------------------------
#if ESP_IDF_VERSION < ESP_IDF_VERSION_VAL(5, 0, 0)
esp_err_t handleMQTT(esp_mqtt_event_handle_t event) {
  if (event->event_id == MQTT_EVENT_CONNECTED) {
    mqttConnected = true;
    digitalWrite(LED_PIN, HIGH);
  } else if (event->event_id == MQTT_EVENT_DISCONNECTED) {
    mqttConnected = false;
    digitalWrite(LED_PIN, LOW);
  }
  mqttClient.onEventCallback(event);
  return ESP_OK;
}
#else
void handleMQTT(void* handler_args, esp_event_base_t base, int32_t event_id, void* event_data) {
  auto* event = static_cast<esp_mqtt_event_handle_t>(event_data);
  if (event_id == MQTT_EVENT_CONNECTED) {
    mqttConnected = true;
    digitalWrite(LED_PIN, HIGH);
  } else if (event_id == MQTT_EVENT_DISCONNECTED) {
    mqttConnected = false;
    digitalWrite(LED_PIN, LOW);
  }
  mqttClient.onEventCallback(event);
}
#endif

// ---------------------------------------------------------------------------
// setup()
// ---------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  pinMode(NFC_RESET_PIN, OUTPUT);
  digitalWrite(NFC_RESET_PIN, HIGH);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);  // LED off until MQTT connects
  initWiFi();
  initNfc();
  initMqtt();
  Serial.println("SmartAttend firmware ready. Waiting for NFC tags...");
}

// ---------------------------------------------------------------------------
// loop() — millis-based heartbeat (non-blocking)
// ---------------------------------------------------------------------------
void loop() {
  unsigned long now = millis();
  if (mqttConnected && (now - lastHeartbeat >= HEARTBEAT_INTERVAL_MS)) {
    lastHeartbeat = now;
    mqttClient.publish(TOPIC_HEARTBEAT, "online", 0, false);
    Serial.println("Heartbeat sent");
  }
}

// ---------------------------------------------------------------------------
// NFC write — NDEF URI record (from POC, verbatim)
// ---------------------------------------------------------------------------
void writeNfc(char* link) {
  uint8_t uid[7];
  uint8_t uidLength;

  if (!nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength, 1000)) {
    rfField(false);
    return;
  }

  Serial.println("Karte erkannt!");

  uint8_t keyNdef[6] = { 0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7 };
  if (!nfc.mifareclassic_AuthenticateBlock(uid, uidLength, 4, 0, keyNdef)) {
    Serial.println("Auth fehlgeschlagen!");
    rfField(false);
    return;
  }

  struct {
    const char* prefix;
    uint8_t code;
  } prefixes[] = {
    { "https://www.", 0x02 },
    { "http://www.", 0x01 },
    { "https://", 0x04 },
    { "http://", 0x03 },
  };

  uint8_t prefixCode = 0x00;
  const char* rest = link;

  for (auto& p : prefixes) {
    if (strncmp(link, p.prefix, strlen(p.prefix)) == 0) {
      prefixCode = p.code;
      rest = link + strlen(p.prefix);
      break;
    }
  }

  uint16_t restLen = strlen(rest);
  uint16_t uriPayload = 1 + restLen;      // Präfix-Byte + URI-Rest
  uint16_t ndefLen = 4 + uriPayload;      // D1 01 <len> 55 + payload
  uint16_t totalBytes = 2 + ndefLen + 1;  // 03 <ndefLen> ... FE

  // Gesamten NDEF-Datenstrom aufbauen
  uint16_t bufSize = ((totalBytes + 15) / 16) * 16;  // auf Blockgröße aufrunden
  uint8_t* buf = (uint8_t*)calloc(bufSize, 1);
  if (!buf) {
    Serial.println("Speicherfehler!");
    rfField(false);
    return;
  }

  uint16_t i = 0;
  buf[i++] = 0x03;  // NDEF TLV Tag
  buf[i++] = (uint8_t)ndefLen;
  buf[i++] = 0xD1;                 // NDEF Record Header (MB, ME, SR, TNF=0x01)
  buf[i++] = 0x01;                 // Type Length = 1
  buf[i++] = (uint8_t)uriPayload;  // Payload Length
  buf[i++] = 0x55;                 // Type: 'U' (URI)
  buf[i++] = prefixCode;           // URI-Präfix-Code
  memcpy(&buf[i], rest, restLen);
  i += restLen;
  buf[i++] = 0xFE;  // Terminator TLV

  uint8_t totalBlocks = bufSize / 16;
  uint8_t blockNum = 4;
  for (uint8_t b = 0; b < totalBlocks; b++) {
    // Skip trailer blocks (block % 4 == 3)
    if (blockNum % 4 == 3) {
      blockNum++;
    }
    if (blockNum % 4 == 0) {
      if (!nfc.mifareclassic_AuthenticateBlock(uid, uidLength, blockNum, 0, keyNdef)) {
        Serial.print("Auth fehlgeschlagen für Block ");
        Serial.println(blockNum);
        free(buf);
        rfField(false);
        return;
      }
    }

    nfc.mifareclassic_WriteDataBlock(blockNum, &buf[b * 16]);
    blockNum++;
  }

  free(buf);
  Serial.println("Geschrieben!");
  delay(500);
  rfField(false);
}

// ---------------------------------------------------------------------------
// RF field toggle (from POC, verbatim)
// ---------------------------------------------------------------------------
void rfField(bool on) {
  uint8_t cmd[3] = { PN532_COMMAND_RFCONFIGURATION, 0x01, (uint8_t)(on ? 0x01 : 0x00) };
  nfc.sendCommandCheckAck(cmd, 3);
  delay(20);
}

// ---------------------------------------------------------------------------
// NFC hardware reset (from POC, verbatim)
// ---------------------------------------------------------------------------
void resetNfc() {
  digitalWrite(NFC_RESET_PIN, LOW);
  delay(10);
  digitalWrite(NFC_RESET_PIN, HIGH);
  initNfc();
}
