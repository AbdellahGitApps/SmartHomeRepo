#include "device_config.h"
#include "secrets.h"

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

#include "wifi_manager.h"
#include "energy_meter.h"

// ======================================================
// Runtime
// ======================================================

unsigned long lastReadingTime = 0;

// ======================================================
// Setup
// ======================================================

void setup()
{
    Serial.begin(115200);

    delay(1000);

    randomSeed(micros());

    Serial.println();
    Serial.println("==========================================");
    Serial.println(" SMART HOME ENERGY METER");
    Serial.println("==========================================");

    connectWiFi();

    Serial.println("System Ready");
}

// ======================================================
// Main Loop
// ======================================================

void loop()
{
    //----------------------------------------------------
    // WiFi Watchdog
    //----------------------------------------------------

    if (WiFi.status() != WL_CONNECTED)
    {
        Serial.println();
        Serial.println("WiFi Lost");

        connectWiFi();
    }

    //----------------------------------------------------
    // Send Interval
    //----------------------------------------------------

    if (millis() - lastReadingTime < READING_INTERVAL)
    {
        return;
    }

    lastReadingTime = millis();

    //----------------------------------------------------
    // Read Sensors
    //----------------------------------------------------

    float voltage = readVoltageSensor();

    float current = readCurrentSensor();

    // إذا كانت الكهرباء مقطوعة
    if (voltage < 100.0f)
    {
        voltage = 0.0f;
        current = 0.0f;

        lastVoltage = 0.0f;
        lastCurrent = 0.0f;
        lastPower = 0.0f;
    }

    float power =
        calculatePower(
            voltage,
            current);

    //----------------------------------------------------
    // Print
    //----------------------------------------------------

    printMeasurements();

    //----------------------------------------------------
    // JSON
    //----------------------------------------------------

    JsonDocument doc;

    // بيانات القياس فقط
    doc["voltage"] = voltage;
    doc["current"] = current;
    doc["watts"] = power;

    // معلومات إضافية
    doc["source"] = "esp32";

    String payload;

    serializeJson(
        doc,
        payload);

    //----------------------------------------------------
    // Send
    //----------------------------------------------------

    Serial.println();
    Serial.println("Uploading...");

    bool ok =
        sendEnergyData(payload);

    if (ok)
    {
        Serial.println("Upload Success");
    }
    else
    {
        Serial.println("Upload Failed");
    }

    Serial.println();
}