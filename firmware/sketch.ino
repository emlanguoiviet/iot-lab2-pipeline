#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>

const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

const char* MQTT_SERVER = "broker.hivemq.com";
const int MQTT_PORT = 1883;
const char* MQTT_TOPIC = "iot/lab2/manh_ptit/telemetry";
const char* DEVICE_ID = "esp32_node_01";

// Chân DHT22 (GPIO 15)
const int DHT_PIN = 15;
#define DHTTYPE DHT22
DHT dht(DHT_PIN, DHTTYPE);

const int TRIG_PIN = 5;
const int ECHO_PIN = 18;
const int LED_PIN = 2;
const unsigned long SEND_INTERVAL_MS = 3000;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

unsigned long lastSend = 0;
unsigned long sequenceNo = 0;

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\n==========================================");
  Serial.println(">>> SERIAL MONITOR HOAT DONG THANH CONG <<<");
  Serial.println("==========================================");

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);

  dht.begin();

  Serial.print("Dang ket noi WiFi");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  
  int retryWiFi = 0;
  while (WiFi.status() != WL_CONNECTED && retryWiFi < 15) {
    delay(300);
    Serial.print(".");
    retryWiFi++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" Da ket noi WiFi!");
  } else {
    Serial.println(" Bo qua cho WiFi, tiep tuc chay...");
  }

  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);
  mqttClient.setBufferSize(512);
  Serial.println("San sang gui du lieu!\n");
}

float readDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) return 45.0f;
  return duration * 0.0343f / 2.0f;
}

void loop() {
  if (!mqttClient.connected()) {
    String clientId = "ESP32-PTIT-" + String((uint32_t)ESP.getEfuseMac(), HEX);
    Serial.print("Dang ket noi MQTT...");
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println(" Ket noi Broker thanh cong!");
    } else {
      Serial.printf(" That bai (rc=%d). Se thu lai sau.\n", mqttClient.state());
    }
  } else {
    mqttClient.loop();
  }

  unsigned long now = millis();
  if (now - lastSend >= SEND_INTERVAL_MS) {
    lastSend = now;

    // Đọc cảm biến trực tiếp từ Wokwi
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    float distance = readDistanceCm();

    // Fallback: nếu đọc lỗi thì tạo biến động nhẹ quanh mức nền để test pipeline
    static float baseTemp = 28.5f;
    static float baseHum = 65.0f;
    float temp = isnan(t) ? (baseTemp += 0.4f) : t;
    float hum  = isnan(h) ? (baseHum -= 0.5f) : h;

    sequenceNo++;
    char payload[256];
    snprintf(payload, sizeof(payload),
             "{\"device_id\":\"%s\",\"temperature\":%.2f,\"humidity\":%.2f,\"distance_cm\":%.2f,\"sequence\":%lu,\"uptime_s\":%lu}",
             DEVICE_ID, temp, hum, distance, sequenceNo, millis() / 1000);

    bool ok = mqttClient.publish(MQTT_TOPIC, payload);
    Serial.printf("[PUBLISH %lu] %s | %s\n", sequenceNo, payload, ok ? "OK" : "FAILED");

    digitalWrite(LED_PIN, HIGH);
    delay(50);
    digitalWrite(LED_PIN, LOW);
  }
}