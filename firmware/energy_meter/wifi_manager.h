#pragma once

#include <WiFi.h>
#include <HTTPClient.h>

void connectWiFi() {

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    Serial.print("Connecting to WiFi");

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println();
    Serial.println("WiFi Connected");
    Serial.println(WiFi.localIP());
}

bool sendEnergyData(String json) {

    if (WiFi.status() != WL_CONNECTED)
        return false;

    HTTPClient http;

    String url =
        "http://" +
        String(SERVER_IP) +
        ":" +
        String(SERVER_PORT) +
        ENERGY_API;

    http.begin(url);

    http.addHeader(
        "Content-Type",
        "application/json"
    );

    http.addHeader(
        "device_token",
        DEVICE_TOKEN
    );
    
    int code = http.POST(json);

    Serial.print("HTTP Code : ");
    Serial.println(code);

    if (code > 0) {

        Serial.println(http.getString());

    }

    http.end();

    return code == 200;
}