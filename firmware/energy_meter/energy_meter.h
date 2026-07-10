#pragma once

#include <Arduino.h>

// ======================================================
// SMART ENERGY METER
// Energy Processing Layer
// ======================================================

// ------------------------------------------------------
// Runtime Variables
// ------------------------------------------------------

static float totalEnergyKwh = 0.0f;

static float lastVoltage = 220.0f;
static float lastCurrent = 1.0f;
static float lastPower = 220.0f;

// ------------------------------------------------------
// Fake Sensor Generator
// سيتم استبداله لاحقاً بالحساسات الحقيقية
// ------------------------------------------------------

inline float fakeVoltage()
{
    float value =
        220.0 +
        random(-25, 26) / 10.0;

    lastVoltage = value;

    return value;
}

inline float fakeCurrent()
{
    float value =
        0.80 +
        random(0, 80) / 100.0;

    lastCurrent = value;

    return value;
}

// ------------------------------------------------------
// لاحقاً فقط سنغير هاتين الدالتين
// ------------------------------------------------------

inline float readVoltageSensor()
{
    return fakeVoltage();
}

inline float readCurrentSensor()
{
    return fakeCurrent();
}

// ------------------------------------------------------
// Power
// ------------------------------------------------------

inline float calculatePower(
    float voltage,
    float current)
{
    lastPower = voltage * current;

    return lastPower;
}

// ------------------------------------------------------
// Energy
// ------------------------------------------------------

inline float calculateEnergy(
    float power,
    float elapsedSeconds)
{
    float kwh =
        power *
        elapsedSeconds /
        3600000.0;

    totalEnergyKwh += kwh;

    return totalEnergyKwh;
}

// ------------------------------------------------------
// Getters
// ------------------------------------------------------

inline float getVoltage()
{
    return lastVoltage;
}

inline float getCurrent()
{
    return lastCurrent;
}

inline float getPower()
{
    return lastPower;
}

inline float getEnergy()
{
    return totalEnergyKwh;
}

// ------------------------------------------------------
// Pretty Serial Output
// ------------------------------------------------------

inline void printMeasurements()
{
    Serial.println();
    Serial.println("==========================================");
    Serial.println("SMART ENERGY METER");
    Serial.println("------------------------------------------");

    Serial.print("Voltage : ");
    Serial.print(lastVoltage, 2);
    Serial.println(" V");

    Serial.print("Current : ");
    Serial.print(lastCurrent, 2);
    Serial.println(" A");

    Serial.print("Power   : ");
    Serial.print(lastPower, 2);
    Serial.println(" W");

    Serial.print("Energy  : ");
    Serial.print(totalEnergyKwh, 6);
    Serial.println(" kWh");

    Serial.println("==========================================");
}