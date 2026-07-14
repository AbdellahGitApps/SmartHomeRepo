#pragma once

// ==========================
// Device Information
// ==========================
#define DEVICE_ID "METER-HOME100-001"

#define DEVICE_NAME "Energy Meter"

#define DEVICE_TYPE "energy_meter"

// ==========================
// Server
// ==========================

#define SERVER_PORT 8000

#define ENERGY_API "/api/energy/ingest"

// ==========================
// Reading Interval
// ==========================
#define READING_INTERVAL 5000   // كل 5 ثواني

// ==========================
// ADC Pins
// ==========================

// ZMPT101B
#define VOLTAGE_PIN 35

// SCT013
#define CURRENT_PIN 34

// ==========================
// ADC
// ==========================
#define ADC_MAX 4095.0
#define ADC_REF 3.3

// ==========================
// Calibration
// سيتم تعديلها لاحقاً
// ==========================
#define VOLTAGE_CALIBRATION 220.0
#define CURRENT_CALIBRATION 30.0