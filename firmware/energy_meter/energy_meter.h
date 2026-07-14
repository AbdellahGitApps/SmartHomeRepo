#pragma once

#include <Arduino.h>
#include <math.h>

#define NOISE_THRESHOLD 2.0

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
const int SAMPLE_COUNT = 1000;

const float ADC_CENTER = 2048.0f;

float voltageCalibration = 0.445f;
float currentCalibration = 0.0042f;

// ------------------------------------------------------
// Fake Sensor Generator
// سيتم استبداله لاحقاً بالحساسات الحقيقية
// ------------------------------------------------------


// ------------------------------------------------------
// لاحقاً فقط سنغير هاتين الدالتين
// ------------------------------------------------------

inline float readVoltageSensor()
{
    double sum = 0;
    double offset = 0;

    for (int i = 0; i < SAMPLE_COUNT; i++)
    {
        offset += analogRead(VOLTAGE_PIN);
    }

    offset /= SAMPLE_COUNT;

    for (int i = 0; i < SAMPLE_COUNT; i++)
    {
        float sample = analogRead(VOLTAGE_PIN) - offset;
        sum += sample * sample;
    }

    float rms = sqrt(sum / SAMPLE_COUNT);

    if (rms < NOISE_THRESHOLD)
    {
        lastVoltage = 0;
        return lastVoltage;
    }

    lastVoltage = rms * voltageCalibration;

    return lastVoltage;
}

inline float readCurrentSensor()
{
    double sum = 0;
    double offset = 0;

    for (int i = 0; i < SAMPLE_COUNT; i++)
    {
        offset += analogRead(CURRENT_PIN);
    }

    offset /= SAMPLE_COUNT;

    for (int i = 0; i < SAMPLE_COUNT; i++)
    {
        float sample = analogRead(CURRENT_PIN) - offset;
        sum += sample * sample;
    }

    float rms = sqrt(sum / SAMPLE_COUNT);

    Serial.print("Current RMS ADC : ");
    Serial.println(rms);

    if (rms < NOISE_THRESHOLD)
    {
        lastCurrent = 0;
        return lastCurrent;
    }

    lastCurrent = rms * currentCalibration;

    return lastCurrent;
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