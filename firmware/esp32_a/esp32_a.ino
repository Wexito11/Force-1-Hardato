// Форс-1, модуль A (ESP32-ETH01 или ESP32-WROOM): мотор хода, полозья, ремонтный модуль, датчики
// Пины - по таблице «Форс-1_компоненты.xls», лист «Распиновка» (вариант ETH01).
// Протокол - firmware/PROTOCOL.md. Библиотеки: Adafruit PWM Servo Driver, AS5600 (RobTillaart), Wire.

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include <AS5600.h>

// ---------- пины ----------
const int PIN_ENA = 4, PIN_IN1 = 17, PIN_IN2 = 32;   // L298N A, канал A - ход
const int PIN_SDA = 33, PIN_SCL = 14;                 // I2C: PCA9685 0x40, AS5600 №2 0x36, MPU-9250 0x68
const int PIN_TOF_RX = 39;                            // TOF250 TX -> RX1
const int PIN_ENC = 35;                               // энкодер LM393
const int PIN_ECHO = 36, PIN_TRIG = 12;               // HC-SR04 вниз (echo через делитель 1k/2k)
const int PIN_LIMIT_WR = 2;                           // концевик гайковёрта (к GND, INPUT_PULLUP). На WROOM - 33

// ---------- PCA9685 ----------
const int CH_CAM = 0, CH_MAG_ARM = 1, CH_WR_ARM = 2;  // MG90S
const int CH_SKID1 = 3, CH_SKID2 = 4;                 // MG996R полозья A
const int CH_TOKEN = 5;                               // MG90S сброс фишек (если помпы нет)
const int CH_WR_EN = 8, CH_WR_IN3 = 9, CH_WR_IN4 = 10; // L298N A канал B - мотор гайковёрта
const int CH_PUMP = 11, CH_MAG = 12;                  // LR7843 №1 помпа, №2 магнит

// ---------- углы серво (подобрать на сборке) ----------
const int SKID_UP_DEG = 51, SKID_DN_DEG = -42;        // из габаритной схемы: +50,8 / -42,5
const int SKID1_ZERO = 90, SKID2_ZERO = 90;           // положение серво при звене горизонтально
const int CAM_UP = 0, CAM_RAIL = 90;
const int MAG_UP = 20, MAG_DN = 110, WR_UP = 20, WR_DN = 100;

const int PWM_MAX = 204;                              // 80 % от 255 - моторы от VBAT до 16,8 В
const unsigned long TELEMETRY_MS = 100;

Adafruit_PWMServoDriver pca(0x40);
AS5600 as5600;
HardwareSerial tof(1);
volatile long enc = 0;
long tofMm = -1, tieMm = -1;
unsigned long tTel = 0;

void IRAM_ATTR onEnc() { enc++; }

// серво: угол 0..180 -> импульс 500..2500 мкс при 50 Гц (4096 тиков на 20 мс)
void servo(int ch, int deg) {
  deg = constrain(deg, 0, 180);
  int us = 500 + deg * 2000 / 180;
  pca.setPWM(ch, 0, us * 4096L / 20000);
}
void key(int ch, int percent) { pca.setPWM(ch, 0, constrain(percent, 0, 100) * 4095L / 100); }

void motor(int pwm) {
  pwm = constrain(pwm, -PWM_MAX, PWM_MAX);
  digitalWrite(PIN_IN1, pwm > 0); digitalWrite(PIN_IN2, pwm < 0);
  ledcWrite(0, abs(pwm));
}

// плавный ход серво полозьев; оба серво вращаются навстречу
void skids(bool up) {
  int target = up ? SKID_UP_DEG : SKID_DN_DEG;
  static int cur = SKID_UP_DEG;
  int step = (target > cur) ? 2 : -2;
  for (int a = cur; a != target; a += step) {
    servo(CH_SKID1, SKID1_ZERO + a); servo(CH_SKID2, SKID2_ZERO - a);
    delay(15);
  }
  servo(CH_SKID1, SKID1_ZERO + target); servo(CH_SKID2, SKID2_ZERO - target);
  cur = target;
}

long readSonar() {
  digitalWrite(PIN_TRIG, LOW); delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  long us = pulseIn(PIN_ECHO, HIGH, 20000);
  return us ? us / 58 * 10 : -1;   // мм
}

// TOF250: строка "d=123mm" или бинарный кадр - зависит от версии; здесь текстовый разбор
void readTof() {
  while (tof.available()) {
    String s = tof.readStringUntil('\n');
    int p = s.indexOf('=');
    if (p >= 0) tofMm = s.substring(p + 1).toInt();
  }
}

// гайковёрт: крутить, пока AS5600 №2 видит вращение; стоп, если угол не меняется 150 мс
void wrenchRun() {
  pca.setPWM(CH_WR_IN3, 4096, 0); pca.setPWM(CH_WR_IN4, 0, 4096);
  key(CH_WR_EN, 50);                         // ШИМ ~50 % для JGA25-370 (для JGA 77 об/мин - 100 %)
  unsigned long t0 = millis(), tLast = millis();
  int last = as5600.readAngle();
  while (millis() - t0 < 4000) {
    int a = as5600.readAngle();
    if (abs(a - last) > 8) { last = a; tLast = millis(); }
    if (millis() - tLast > 150 && millis() - t0 > 400) { key(CH_WR_EN, 0); Serial.printf("WR DONE %lu\n", millis() - t0); return; }
    delay(10);
  }
  key(CH_WR_EN, 0); Serial.println("WR TIMEOUT");
}

void handle(String c) {
  c.trim();
  if (c == "PING") Serial.println("PONG A");
  else if (c.startsWith("M ")) { motor(c.substring(2).toInt()); Serial.println("OK"); }
  else if (c == "STOP") { motor(0); key(CH_WR_EN, 0); key(CH_MAG, 0); Serial.println("OK"); }
  else if (c == "SKID UP") { skids(true); Serial.println("OK"); }
  else if (c == "SKID DN") { skids(false); Serial.println("OK"); }
  else if (c == "ENC 0") { enc = 0; Serial.println("OK"); }
  else if (c.startsWith("CAM ")) { servo(CH_CAM, c.substring(4).toInt()); Serial.println("OK"); }
  else if (c == "MAG DN") { servo(CH_MAG_ARM, MAG_DN); Serial.println("OK"); }
  else if (c == "MAG UP") { servo(CH_MAG_ARM, MAG_UP); Serial.println("OK"); }
  else if (c == "MAG ON") { key(CH_MAG, 70); Serial.println("OK"); }     // ШИМ ≤ 70 %: катушка 12 В от 16,8 В
  else if (c == "MAG OFF") { key(CH_MAG, 0); Serial.println("OK"); }
  else if (c == "WR DN") { servo(CH_WR_ARM, WR_DN); Serial.println("OK"); }
  else if (c == "WR UP") { servo(CH_WR_ARM, WR_UP); Serial.println("OK"); }
  else if (c == "WR RUN") wrenchRun();
  else if (c == "WR OFF") { key(CH_WR_EN, 0); Serial.println("OK"); }
  else if (c.startsWith("PUMP ")) { key(CH_PUMP, 100); delay(constrain(c.substring(5).toInt(), 20, 500)); key(CH_PUMP, 0); Serial.println("OK"); }
  else if (c == "TOKEN") { servo(CH_TOKEN, 120); delay(300); servo(CH_TOKEN, 30); Serial.println("OK"); }
  else if (c == "Q") telemetry();
  else Serial.println("ERR unknown");
}

void telemetry() {
  Serial.printf("T A enc=%ld tof=%ld tie=%ld limit=%d\n", enc, tofMm, tieMm, digitalRead(PIN_LIMIT_WR) == LOW);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_IN1, OUTPUT); pinMode(PIN_IN2, OUTPUT);
  ledcSetup(0, 20000, 8); ledcAttachPin(PIN_ENA, 0);
  pinMode(PIN_ENC, INPUT); attachInterrupt(digitalPinToInterrupt(PIN_ENC), onEnc, RISING);
  pinMode(PIN_TRIG, OUTPUT); pinMode(PIN_ECHO, INPUT); pinMode(PIN_LIMIT_WR, INPUT_PULLUP);
  Wire.begin(PIN_SDA, PIN_SCL);
  pca.begin(); pca.setPWMFreq(50);
  as5600.begin();
  tof.begin(115200, SERIAL_8N1, PIN_TOF_RX, -1);
  servo(CH_CAM, CAM_RAIL); servo(CH_MAG_ARM, MAG_UP); servo(CH_WR_ARM, WR_UP);
  skids(true);
  Serial.println("READY A");
}

void loop() {
  static String line;
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n') { handle(line); line = ""; } else line += ch;
  }
  readTof();
  if (millis() - tTel > TELEMETRY_MS) {
    tTel = millis();
    tieMm = readSonar();
    telemetry();
    static bool lastLimit = false;
    bool lim = digitalRead(PIN_LIMIT_WR) == LOW;
    if (lim && !lastLimit) Serial.println("EV A LIMIT_WR");
    lastLimit = lim;
  }
}
