#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

String SERVER_BASE_URL = "http://192.168.1.100:8000";

const char* MQTT_HOST = "192.168.1.100";
const int MQTT_PORT = 1883;

String CLAIM_CODE = "PUT_CLAIM_CODE_HERE";
String DEVICE_TYPE = "esp32_cam";
String DEVICE_ID = "esp32_cam_01";
String DEVICE_TOKEN = "";
String MQTT_TOPIC = "";

WebServer server(80);
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

unsigned long lastHeartbeatAt = 0;
const unsigned long HEARTBEAT_INTERVAL = 30000;

#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

String deviceIp() {
  return WiFi.localIP().toString();
}

String macAddress() {
  return WiFi.macAddress();
}

bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 12;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 14;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  return err == ESP_OK;
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("WiFi connected. IP: ");
  Serial.println(deviceIp());
  Serial.print("MAC: ");
  Serial.println(macAddress());
}

void handleRoot() {
  DynamicJsonDocument doc(512);
  doc["device_id"] = DEVICE_ID;
  doc["device_type"] = DEVICE_TYPE;
  doc["ip"] = deviceIp();
  doc["mac_address"] = macAddress();
  doc["capture_url"] = "http://" + deviceIp() + "/capture";
  doc["stream_url"] = "http://" + deviceIp() + "/stream";
  doc["mqtt_topic"] = MQTT_TOPIC;
  doc["status"] = "online";

  String body;
  serializeJson(doc, body);

  server.send(200, "application/json", body);
}

void handleCapture() {
  camera_fb_t* fb = esp_camera_fb_get();

  if (!fb) {
    server.send(500, "text/plain", "Camera capture failed");
    return;
  }

  WiFiClient client = server.client();

  server.sendHeader("Content-Type", "image/jpeg");
  server.sendHeader("Content-Length", String(fb->len));
  server.send(200);

  client.write(fb->buf, fb->len);
  esp_camera_fb_return(fb);
}

void handleStream() {
  WiFiClient client = server.client();

  String response = "HTTP/1.1 200 OK\r\n";
  response += "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n";
  client.print(response);

  while (client.connected()) {
    camera_fb_t* fb = esp_camera_fb_get();

    if (!fb) {
      delay(100);
      continue;
    }

    client.print("--frame\r\n");
    client.print("Content-Type: image/jpeg\r\n");
    client.print("Content-Length: ");
    client.print(fb->len);
    client.print("\r\n\r\n");
    client.write(fb->buf, fb->len);
    client.print("\r\n");

    esp_camera_fb_return(fb);
    delay(80);
  }
}

void startHttpServer() {
  server.on("/", HTTP_GET, handleRoot);
  server.on("/health", HTTP_GET, handleRoot);
  server.on("/capture", HTTP_GET, handleCapture);
  server.on("/stream", HTTP_GET, handleStream);
  server.begin();

  Serial.println("HTTP camera server started");
  Serial.print("Capture: http://");
  Serial.print(deviceIp());
  Serial.println("/capture");
  Serial.print("Stream: http://");
  Serial.print(deviceIp());
  Serial.println("/stream");
}

void parseClaimResponse(String response) {
  DynamicJsonDocument doc(2048);
  DeserializationError error = deserializeJson(doc, response);

  if (error) {
    Serial.println("Could not parse claim response");
    return;
  }

  if (doc["device_id"].is<const char*>()) {
    DEVICE_ID = doc["device_id"].as<String>();
  }

  if (doc["device_token"].is<const char*>()) {
    DEVICE_TOKEN = doc["device_token"].as<String>();
  }

  if (doc["mqtt_topic"].is<const char*>()) {
    MQTT_TOPIC = doc["mqtt_topic"].as<String>();
  }

  if (doc["device"]["device_id"].is<const char*>()) {
    DEVICE_ID = doc["device"]["device_id"].as<String>();
  }

  if (doc["device"]["device_token"].is<const char*>()) {
    DEVICE_TOKEN = doc["device"]["device_token"].as<String>();
  }

  if (doc["device"]["mqtt_topic"].is<const char*>()) {
    MQTT_TOPIC = doc["device"]["mqtt_topic"].as<String>();
  }
}

void sendClaim() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  HTTPClient http;
  String url = SERVER_BASE_URL + "/api/devices/claim";

  DynamicJsonDocument doc(512);
  doc["claim_code"] = CLAIM_CODE;
  doc["device_type"] = DEVICE_TYPE;
  doc["device_ip"] = deviceIp();
  doc["mac_address"] = macAddress();

  String body;
  serializeJson(doc, body);

  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  int statusCode = http.POST(body);
  String response = http.getString();

  Serial.print("Claim status: ");
  Serial.println(statusCode);
  Serial.println(response);

  if (statusCode >= 200 && statusCode < 300) {
    parseClaimResponse(response);
  }

  http.end();
}

void sendHeartbeat() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  HTTPClient http;
  String url = SERVER_BASE_URL + "/api/devices/heartbeat";

  DynamicJsonDocument doc(768);
  doc["device_id"] = DEVICE_ID;
  doc["device_token"] = DEVICE_TOKEN;
  doc["device_ip"] = deviceIp();
  doc["mac_address"] = macAddress();
  doc["status"] = "online";
  doc["capture_url"] = "http://" + deviceIp() + "/capture";
  doc["stream_url"] = "http://" + deviceIp() + "/stream";

  String body;
  serializeJson(doc, body);

  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  int statusCode = http.POST(body);
  String response = http.getString();

  Serial.print("Heartbeat status: ");
  Serial.println(statusCode);
  Serial.println(response);

  http.end();
}

void publishStatus(String statusText) {
  if (!mqttClient.connected()) {
    return;
  }

  DynamicJsonDocument doc(512);
  doc["device_id"] = DEVICE_ID;
  doc["device_token"] = DEVICE_TOKEN;
  doc["device_ip"] = deviceIp();
  doc["mac_address"] = macAddress();
  doc["status"] = statusText;

  String payload;
  serializeJson(doc, payload);

  String topic = "device/" + DEVICE_ID + "/status";
  mqttClient.publish(topic.c_str(), payload.c_str());
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";

  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }

  Serial.print("MQTT command on ");
  Serial.print(topic);
  Serial.print(": ");
  Serial.println(message);

  if (message.indexOf("restart") >= 0) {
    publishStatus("restarting");
    delay(500);
    ESP.restart();
  }

  if (message.indexOf("status") >= 0) {
    publishStatus("online");
  }
}

void connectMqtt() {
  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);

  while (!mqttClient.connected()) {
    String clientId = "esp32_cam_" + macAddress();
    clientId.replace(":", "");

    Serial.print("Connecting to MQTT...");

    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("connected");

      String fallbackCommandTopic = "device/" + DEVICE_ID + "/cmd";
      mqttClient.subscribe(fallbackCommandTopic.c_str());

      if (MQTT_TOPIC.length() > 0) {
        String generatedCommandTopic = MQTT_TOPIC + "/cmd";
        mqttClient.subscribe(generatedCommandTopic.c_str());
      }

      publishStatus("online");
    } else {
      Serial.print("failed, rc=");
      Serial.println(mqttClient.state());
      delay(3000);
    }
  }
}

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

  Serial.begin(115200);
  Serial.println();

  connectWiFi();

  if (!initCamera()) {
    Serial.println("Camera init failed");
    return;
  }

  Serial.println("Camera initialized");

  startHttpServer();

  sendClaim();
  sendHeartbeat();

  connectMqtt();

  lastHeartbeatAt = millis();
}

void loop() {
  server.handleClient();

  if (!mqttClient.connected()) {
    connectMqtt();
  }

  mqttClient.loop();

  if (millis() - lastHeartbeatAt >= HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    publishStatus("online");
    lastHeartbeatAt = millis();
  }
}
