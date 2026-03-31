#include <Wire.h>
#include <Adafruit_PN532.h>

Adafruit_PN532 nfc(16, 17);

void setup() {
  Serial.begin(115200);
  Wire.begin(16, 17);
  nfc.begin();

  uint32_t versiondata = nfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.println("PN532 nicht gefunden!");
    while (1);
  }
  nfc.SAMConfig();
  Serial.println("Bereit. Karte anlegen...");
}

void loop() {
  uint8_t uid[7];
  uint8_t uidLength;

  if (nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength, 1000)) {
    Serial.println("Karte erkannt!");

    uint8_t keyNdef[6] = { 0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7 };

    if (!nfc.mifareclassic_AuthenticateBlock(uid, uidLength, 4, 0, keyNdef)) {
      Serial.println("Auth fehlgeschlagen!");
      return;
    }

    // https://github.com
    uint8_t block4[16] = {
      0x03, 0x11,             // NDEF TLV, länge 17
      0xD1, 0x01, 0x0D, 0x55, // URI record
      0x04,                   // prefix https://
      'g','i','t','h','u','b','.','c','o'
    };
    uint8_t block5[16] = {
      'm', 0x00,              // TLV Ende
      0x00,0x00,0x00,0x00,
      0x00,0x00,0x00,0x00,
      0x00,0x00,0x00,0x00,
      0x00,0x00
    };

    nfc.mifareclassic_WriteDataBlock(4, block4);
    nfc.mifareclassic_WriteDataBlock(5, block5);

    Serial.println("Geschrieben!");
    delay(3000);
  }
}
