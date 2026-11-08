// Форс-1, модуль B (ESP32-WROOM): мотор хода, полозья, телескоп NEMA17 + AS5600 №1, RFID, датчики
// Пины - «Форс-1_компоненты.xls», лист «Распиновка». Протокол - firmware/PROTOCOL.md.
// Библиотеки: AS5600 (RobTillaart), MFRC522, ESP32Servo, Wire, SPI.

#include <Wire.h>
#include <SPI.h>
#include <AS5600.h>
#include <MFRC522.h>
#include <ESP32Servo.h>

// ---------- пины ----------
const int PIN_ENA = 25, PIN_IN1 = 26, PIN_IN2 = 27;          // L298N B - ход
const int PIN_STEP = 32, PIN_DIR = 33, PIN_EN = 4;           // A4988 (EN активен низким)
const int PIN_SDA = 21, PIN_SCL = 22;                        // AS5600 №1 0x36
const int PIN_TOF_RX = 16, PIN_TOF_TX = 17;                  // TOF250
const int PIN_RFID_SCK = 18, PIN_RFID_MISO = 19, PIN_RFID_MOSI = 23, PIN_RFID_SS = 5, PIN_RFID_RST = 13;
const int PIN_ENC = 34;                                      // энкодер LM393
const int PIN_ECHO = 35, PIN_TRIG = 2;                       // HC-SR04 вниз (echo через делитель)
const int PIN_SKID1 = 14, PIN_SKID2 = 15;                    // MG996R полозья B (питание 6 В по жгуту)
// UART0 (1/3) - к Pi через жгут W1

// ---------- параметры ----------
const int PWM_MAX = 204;                                     // 80 %
const int SKID_UP_DEG = 51, SKID_DN_DEG = -42, SKID1_ZERO = 90, SKID2_ZERO = 90;
const float GAUGE_NOMINAL = 760.0;
const float PULLEY_R = 7.5;                                  // шкив Ø15
const float AS_DEG_PER_LSB = 360.0 / 4096;
const int STEP_US = 400;                                     // 1/16 микрошаг, ~0,4 мм/с на 1 Гц? подобрать
const unsigned long TELEMETRY_MS = 100;

AS5600 as5600;
MFRC522 rfid(PIN_RFID_SS, PIN_RFID_RST);
HardwareSerial tof(2);
Servo skid1, skid2;
volatile long enc = 0;
long tofMm = -1, tieMm = -1;
long asZero = 0;                                             // отсчёт AS5600 при колее 760
long asAccum = 0; int asLast = 0;                            // накопленный угол (многооборотный)
String lastRfid = "-";
unsigned long tTel = 0;

void IRAM_ATTR onEnc() { enc++; }

void motor(int pwm) {
  pwm = constrain(pwm, -PWM_MAX, PWM_MAX);
  digitalWrite(PIN_IN1, pwm > 0); digitalWrite(PIN_IN2, pwm < 0);
  ledcWrite(0, abs(pwm));
}

void skids(bool up) {
  int target = up ? SKID_UP_DEG : SKID_DN_DEG;
  static int cur = SKID_UP_DEG;
  int step = (target > cur) ? 2 : -2;
  for (int a = cur; a != target; a += step) { skid1.write(SKID1_ZERO + a); skid2.write(SKID2_ZERO - a); delay(15); }
  skid1.write(SKID1_ZERO + target); skid2.write(SKID2_ZERO - target); cur = target;
}

void updateAngle() {
  int a = as5600.readAngle();
  int d = a - asLast;
  if (d > 2048) d -= 4096; else if (d < -2048) d += 4096;
  asAccum += d; asLast = a;
}
float gaugeMm() { return GAUGE_NOMINAL + (asAccum - asZero) * AS_DEG_PER_LSB * PI / 180.0 * PULLEY_R; }

void telescope(long steps) {                                 // + сводит модули (наматывает ремень)
  digitalWrite(PIN_EN, LOW);
  digitalWrite(PIN_DIR, steps > 0);
  for (long i = 0; i < labs(steps); i++) {
    digitalWrite(PIN_STEP, HIGH); delayMicroseconds(5);
    digitalWrite(PIN_STEP, LOW); delayMicroseconds(STEP_US);
    if ((i & 63) == 0) updateAngle();
  }
}

long readSonar() {
  digitalWrite(PIN_TRIG, LOW); delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  long us = pulseIn(PIN_ECHO, HIGH, 20000);
  return us ? us / 58 * 10 : -1;
}

void readTof() {
  while (tof.available()) {
    String s = tof.readStringUntil('\n');
    int p = s.indexOf('=');
    if (p >= 0) tofMm = s.substring(p + 1).toInt();
  }
}

void readRfid() {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) return;
  String id = "";
  for (byte i = 0; i < rfid.uid.size; i++) id += String(rfid.uid.uidByte[i], HEX);
  lastRfid = id;
  Serial.printf("EV B RFID %s\n", id.c_str());
  rfid.PICC_HaltA();
}

void telemetry() {
  Serial.printf("T B enc=%ld tof=%ld tie=%ld gauge=%.1f rfid=%s\n", enc, tofMm, tieMm, gaugeMm(), lastRfid.c_str());
  lastRfid = "-";
}

void handle(String c) {
  c.trim();
  if (c == "PING") Serial.println("PONG B");
  else if (c.startsWith("M ")) { motor(c.substring(2).toInt()); Serial.println("OK"); }
  else if (c == "STOP") { motor(0); digitalWrite(PIN_EN, HIGH); Serial.println("OK"); }
  else if (c == "SKID UP") { skids(true); Serial.println("OK"); }
  else if (c == "SKID DN") { skids(false); Serial.println("OK"); }
  else if (c == "ENC 0") { enc = 0; Serial.println("OK"); }
  else if (c == "TEL FREE") { digitalWrite(PIN_EN, HIGH); Serial.println("OK"); }
  else if (c == "TEL HOLD") { digitalWrite(PIN_EN, LOW); Serial.println("OK"); }
  else if (c == "TEL 0") { updateAngle(); asZero = asAccum; Serial.println("OK"); }
  else if (c.startsWith("TEL ")) { telescope(c.substring(4).toInt()); Serial.println("OK"); }
  else if (c == "Q") telemetry();
  else Serial.println("ERR unknown");
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_IN1, OUTPUT); pinMode(PIN_IN2, OUTPUT);
  ledcSetup(0, 20000, 8); ledcAttachPin(PIN_ENA, 0);
  pinMode(PIN_STEP, OUTPUT); pinMode(PIN_DIR, OUTPUT); pinMode(PIN_EN, OUTPUT); digitalWrite(PIN_EN, HIGH);
  pinMode(PIN_ENC, INPUT); attachInterrupt(digitalPinToInterrupt(PIN_ENC), onEnc, RISING);
  pinMode(PIN_TRIG, OUTPUT); pinMode(PIN_ECHO, INPUT);
  Wire.begin(PIN_SDA, PIN_SCL); as5600.begin(); asLast = as5600.readAngle();
  SPI.begin(PIN_RFID_SCK, PIN_RFID_MISO, PIN_RFID_MOSI, PIN_RFID_SS); rfid.PCD_Init();
  tof.begin(115200, SERIAL_8N1, PIN_TOF_RX, PIN_TOF_TX);
  skid1.setPeriodHertz(50); skid2.setPeriodHertz(50);
  skid1.attach(PIN_SKID1, 500, 2500); skid2.attach(PIN_SKID2, 500, 2500);
  skids(true);
  Serial.println("READY B");
}

void loop() {
  static String line;
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n') { handle(line); line = ""; } else line += ch;
  }
  readTof(); readRfid(); updateAngle();
  if (millis() - tTel > TELEMETRY_MS) { tTel = millis(); tieMm = readSonar(); telemetry(); }
}
