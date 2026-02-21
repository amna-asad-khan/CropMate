#include <SoftwareSerial.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

/* -------- WIFI -------- */
const char* ssid = "hello";
const char* password = "12345678";

/* -------- FIREBASE -------- */
const char* firebaseURL =
"https://crop-mate-3940d-default-rtdb.firebaseio.com/soil.json";

/* -------- NodeMCU Pin Definitions -------- */
#define RO_PIN D5   // GPIO14
#define DI_PIN D6   
#define DE_PIN D1   
#define RE_PIN D2   

SoftwareSerial modbus(RO_PIN, DI_PIN);  // RX, TX

/* -------- Modbus Request -------- */
const byte request[] = {
  0x01, 0x03,
  0x00, 0x00,
  0x00, 0x07,
  0x04, 0x08
};

byte values[20];

void setup() {
  Serial.begin(9600);
  modbus.begin(4800);

  pinMode(DE_PIN, OUTPUT);
  pinMode(RE_PIN, OUTPUT);

  digitalWrite(DE_PIN, LOW);
  digitalWrite(RE_PIN, LOW);

  /* -------- WIFI CONNECT -------- */
  WiFi.begin(ssid, password);
  Serial.print("Connecting WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi Connected");
  Serial.println("ESP8266 7-in-1 Soil Sensor Ready");
  delay(1000);
}

/* -------- SEND TO FIREBASE (ADDED) -------- */
void sendToFirebase(float moisture, float temp, int ec, float ph,
                    int n, int p, int k) {

  if (WiFi.status() != WL_CONNECTED) return;

  WiFiClientSecure client;
  client.setInsecure();  // required for HTTPS

  HTTPClient http;
  http.begin(client, firebaseURL);
  http.addHeader("Content-Type", "application/json");

  String json = "{";
  json += "\"moisture\":" + String(moisture) + ",";
  json += "\"temperature\":" + String(temp) + ",";
  json += "\"ec\":" + String(ec) + ",";
  json += "\"ph\":" + String(ph) + ",";
  json += "\"nitrogen\":" + String(n) + ",";
  json += "\"phosphorus\":" + String(p) + ",";
  json += "\"potassium\":" + String(k);
  json += "}";

  int code = http.PUT(json);
  Serial.print("Firebase HTTP Code: ");
  Serial.println(code);

  http.end();
}

void loop() {

  /* -------- Send Request -------- */
  digitalWrite(DE_PIN, HIGH);
  digitalWrite(RE_PIN, HIGH);
  delay(2);

  modbus.write(request, sizeof(request));
  modbus.flush();

  digitalWrite(DE_PIN, LOW);
  digitalWrite(RE_PIN, LOW);

  /* -------- Wait for Response -------- */
  delay(500);

  /* -------- Read Response -------- */
  if (modbus.available() >= 19) {

    for (int i = 0; i < 19; i++) {
      values[i] = modbus.read();
    }

    int moisture     = (values[3]  << 8) | values[4];
    int temperature  = (values[5]  << 8) | values[6];
    int ec           = (values[7]  << 8) | values[8];
    int ph           = (values[9]  << 8) | values[10];
    int nitrogen     = (values[11] << 8) | values[12];
    int phosphorus   = (values[13] << 8) | values[14];
    int potassium    = (values[15] << 8) | values[16];

    float m = moisture * 0.1;
    float t = temperature * 0.1;
    float pH = ph * 0.1;

    Serial.println("====== SOIL DATA ======");
    Serial.print("Moisture: "); Serial.print(m); Serial.println(" %");
    Serial.print("Temp:     "); Serial.print(t); Serial.println(" C");
    Serial.print("EC:       "); Serial.print(ec); Serial.println(" us/cm");
    Serial.print("pH:       "); Serial.print(pH); Serial.println();
    Serial.print("Nitrogen: "); Serial.print(nitrogen); Serial.println(" mg/kg");
    Serial.print("Phosphor: "); Serial.print(phosphorus); Serial.println(" mg/kg");
    Serial.print("Potassium:"); Serial.print(potassium); Serial.println(" mg/kg");
    Serial.println("=======================");

    /* -------- SEND TO FIREBASE (ADDED) -------- */
    sendToFirebase(m, t, ec, pH, nitrogen, phosphorus, potassium);

  } else {
    Serial.print("Waiting / Partial Data: ");
    while (modbus.available()) {
      Serial.print(modbus.read(), HEX);
      Serial.print(" ");
    }
    Serial.println();
  }

  delay(3000);
}