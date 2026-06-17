#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include "secrets.h"

// ================= WIFI =================


// ================= DEVICE =================

const char* device_id =
"DOOR-HOME110-001";

// ================= MQTT =================

const char* mqtt_server =
"10.0.0.17";

const int mqtt_port = 1883;

// ================= SERVO =================

#define SERVO_PIN 12

// ================= ULTRASONIC =================

#define TRIG_PIN 13

#define ECHO_PIN 14

const int DETECTION_DISTANCE = 100;
const unsigned long COOLDOWN_MS = 10000;

unsigned long lastUploadTime = 0;

// ================= CAMERA PINS (AI THINKER) =================

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

// =========================================
// CAMERA
// =========================================

bool setupCamera() {

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

  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;

  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  if (psramFound()) {

    Serial.println("PSRAM FOUND");

    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;

  } else {

    Serial.println("PSRAM NOT FOUND");

    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);

  if (err != ESP_OK) {

    Serial.printf(
      "Camera init failed: 0x%x\n",
      err
    );

    return false;
  }

  Serial.println("Camera Ready");

  return true;
}

// =========================================
// ULTRASONIC
// =========================================

float getDistanceCM() {

  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);

  digitalWrite(TRIG_PIN, LOW);

  long duration =
      pulseIn(
          ECHO_PIN,
          HIGH,
          30000
      );

  if (duration == 0)
    return -1;

  float distance =
      duration * 0.0343 / 2.0;

  if (
      distance < 2 ||
      distance > 400
  ) {
    return -1;
  }

  return distance;
}

// =========================================
// WIFI
// =========================================

void connectWiFi() {

  WiFi.mode(WIFI_STA);

 WiFi.begin(
    WIFI_SSID,
    WIFI_PASSWORD
);

  Serial.print(
      "Connecting WiFi"
  );

  int retries = 0;

  while (
      WiFi.status() != WL_CONNECTED
  ) {

    delay(500);

    Serial.print(".");

    retries++;

    if (retries > 60) {

      Serial.println(
          "\nRestarting..."
      );

      ESP.restart();
    }
  }

  WiFi.setSleep(false);

  Serial.println();
  Serial.println(
      "WiFi Connected"
  );

  Serial.print(
      "IP: "
  );

  Serial.println(
      WiFi.localIP()
  );
}

// =========================================
// UPLOAD IMAGE
// =========================================

void captureAndUpload() {

  Serial.println(
      "Capturing..."
  );

  camera_fb_t *fb =
      esp_camera_fb_get();

  if (!fb) {

    Serial.println(
        "Capture Failed"
    );

    return;
  }

  WiFiClient client;
  HTTPClient http;

  http.setTimeout(20000);

http.begin(
    client,
    SERVER_URL
);


  http.addHeader(
      "Content-Type",
      "image/jpeg"
  );

http.addHeader(
    "device_token",
    DEVICE_TOKEN
);

  Serial.println(
      "Uploading..."
  );

  int httpCode =
      http.POST(
          fb->buf,
          fb->len
      );

  Serial.print(
      "HTTP Code: "
  );

  Serial.println(
      httpCode
  );

  String response =
      http.getString();

  Serial.println(
      "Server Response:"
  );

  Serial.println(
      response
  );

  http.end();

  esp_camera_fb_return(fb);
}

// =========================================
// SETUP
// =========================================

void setup() {

  Serial.begin(115200);

  delay(2000);

  pinMode(
      TRIG_PIN,
      OUTPUT
  );

  pinMode(
      ECHO_PIN,
      INPUT
  );

  connectWiFi();

  if (!setupCamera()) {

    Serial.println(
        "Camera Error"
    );

    while (true) {
      delay(1000);
    }
  }

  Serial.println(
      "System Ready"
  );
}

// =========================================
// LOOP
// =========================================

void loop() {

  if (
      WiFi.status() != WL_CONNECTED
  ) {

    Serial.println(
        "WiFi Lost"
    );

    connectWiFi();
  }

  float distance =
      getDistanceCM();

  Serial.print(
      "Distance: "
  );

  Serial.println(
      distance
  );

  bool objectDetected =
      distance > 0 &&
      distance < DETECTION_DISTANCE;

  bool cooldownFinished =
      millis() -
          lastUploadTime >
      COOLDOWN_MS;

  if (
      objectDetected &&
      cooldownFinished
  ) {

    Serial.println(
        "OBJECT DETECTED"
    );

    delay(300);

    captureAndUpload();

    lastUploadTime =
        millis();
  }

  delay(300);
}