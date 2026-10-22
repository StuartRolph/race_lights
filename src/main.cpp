#include <Arduino.h>

// Wireless light link over HC-12. Build the `sender` env for the board with
// the two inputs and the `receiver` env for the board with the two outputs.
// The HC-12 sits on the hardware serial port (D0/D1), so unplug its TXD/RXD
// wires while uploading.
//
// Debug mode: ground DEBUG_PIN on the sender and it toggles LIGHT_A every
// second instead of reading the inputs, so the link can be tested with no extra
// hardware. The sender's onboard LED shows the LIGHT_A state it sends, and the
// receiver's onboard LED always follows LIGHT_A.

#if !defined(ROLE_SENDER) && !defined(ROLE_RECEIVER)
#error "Define ROLE_SENDER or ROLE_RECEIVER (use the sender / receiver PlatformIO env)"
#endif

constexpr uint8_t HC12_SET_PIN = 2; // LOW = AT command mode
constexpr uint8_t LIGHT_A_PIN = 6;
constexpr uint8_t LIGHT_B_PIN = 7;
constexpr uint8_t DEBUG_PIN = A0; // sender only, LOW = debug mode

constexpr unsigned long HC12_BAUD = 38400;
constexpr unsigned long HC12_SUPPORTED_BAUDS[] = {1200,  2400,  4800,  9600,
                                                  19200, 38400, 57600, 115200};

// Frame: one byte, high nibble is a marker, bit 0 = pin 6 active, bit 1 = pin 7 active
constexpr uint8_t FRAME_MARKER = 0xA0;
constexpr uint8_t FRAME_MARKER_MASK = 0xF0;

constexpr unsigned long HEARTBEAT_MS = 20;
constexpr unsigned long LINK_TIMEOUT_MS = 250;
constexpr unsigned long DEBUG_TOGGLE_MS = 1000;

static void drainSerial() {
  while (Serial.available()) Serial.read();
}

// Sends an AT command and waits for the reply; returns true if it contained "OK".
static bool sendAt(const char *cmd, unsigned long waitMs = 100) {
  drainSerial();
  Serial.print(cmd);
  Serial.flush();

  bool sawO = false;
  bool ok = false;
  unsigned long start = millis();
  while (millis() - start < waitMs) {
    if (!Serial.available()) continue;
    char c = Serial.read();
    if (sawO && c == 'K') ok = true;
    sawO = (c == 'O');
  }
  return ok;
}

static void failBlink() {
  pinMode(LED_BUILTIN, OUTPUT);
  for (;;) {
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
    delay(80);
  }
}

// Puts the module at HC12_BAUD, FU3, channel 1, max power. Works whether the
// module is fresh (9600) or was configured to any other supported baud before.
static void configureHc12() {
  pinMode(HC12_SET_PIN, OUTPUT);
  digitalWrite(HC12_SET_PIN, LOW);
  delay(100);

  // Try the target baud first, then every other supported rate.
  unsigned long foundBaud = 0;
  Serial.begin(HC12_BAUD);
  if (sendAt("AT")) {
    foundBaud = HC12_BAUD;
  } else {
    for (unsigned long baud : HC12_SUPPORTED_BAUDS) {
      if (baud == HC12_BAUD) continue;
      Serial.end();
      Serial.begin(baud);
      if (sendAt("AT")) {
        foundBaud = baud;
        break;
      }
    }
  }
  if (foundBaud == 0) failBlink();

  if (foundBaud != HC12_BAUD) {
    char cmd[16];
    snprintf(cmd, sizeof(cmd), "AT+B%lu", HC12_BAUD);
    sendAt(cmd);
    Serial.end();
    Serial.begin(HC12_BAUD);
  }

  sendAt("AT+FU3");
  sendAt("AT+C001");
  sendAt("AT+P8");

  digitalWrite(HC12_SET_PIN, HIGH);
  delay(100);
  drainSerial();
}

#if defined(ROLE_SENDER)

uint8_t lastFrame = 0xFF;
unsigned long lastSend = 0;
bool debugA = false;
unsigned long lastToggle = 0;

void setup() {
  pinMode(LIGHT_A_PIN, INPUT_PULLUP);
  pinMode(LIGHT_B_PIN, INPUT_PULLUP);
  pinMode(DEBUG_PIN, INPUT_PULLUP);
  pinMode(LED_BUILTIN, OUTPUT);
  configureHc12();
}

void loop() {
  unsigned long now = millis();

  uint8_t frame = FRAME_MARKER;
  if (digitalRead(DEBUG_PIN) == LOW) {
    if (now - lastToggle >= DEBUG_TOGGLE_MS) {
      lastToggle = now;
      debugA = !debugA;
    }
    if (debugA) frame |= 0x01;
    frame |= 0x02;
  } else if (digitalRead(LIGHT_A_PIN) == LOW) {
    frame |= 0x01;
  }
  if (digitalRead(LIGHT_B_PIN) == LOW) frame |= 0x02;
  digitalWrite(LED_BUILTIN, frame & 0x01);

  if (frame != lastFrame || now - lastSend >= HEARTBEAT_MS) {
    Serial.write(frame);
    lastFrame = frame;
    lastSend = now;
  }
}

#else // ROLE_RECEIVER

unsigned long lastRx = 0;
bool linkUp = false;

static void setLights(bool a, bool b) {
  digitalWrite(LIGHT_A_PIN, a);
  digitalWrite(LIGHT_B_PIN, b);
  digitalWrite(LED_BUILTIN, a);
}

void setup() {
  pinMode(LIGHT_A_PIN, OUTPUT);
  pinMode(LIGHT_B_PIN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  setLights(false, false);
  configureHc12();
}

void loop() {
  while (Serial.available()) {
    uint8_t frame = Serial.read();
    if ((frame & FRAME_MARKER_MASK) != FRAME_MARKER) continue;
    setLights(frame & 0x01, frame & 0x02);
    lastRx = millis();
    linkUp = true;
  }

  if (linkUp && millis() - lastRx >= LINK_TIMEOUT_MS) {
    setLights(false, false);
    linkUp = false;
  }
}

#endif
