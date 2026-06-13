# Phase 11: Legacy Endpoint Dependency Investigation

## 1. append.py Analysis

- **Imported Anywhere?** No.
- **Executed Anywhere?** No references found in shell scripts, python scripts, or package configs.
- **Referenced by main.py?** No.
- **Referenced by router/service/test?** No.
- **Status:** Confirmed DEAD CODE. It is an isolated file (likely a scratchpad or old generator script) and has no impact on runtime.

## 2 & 3. Endpoint Classification Table

### Endpoint(s): /api/dashboard/security-logs-data-old
- **Function:** `api_dashboard_security_logs_data` (Lines 1050-1055)
- **Category:** **SAFE_TO_DELETE**
- **Confidence:** High (Only referenced by isolated `append.py`)
- **References:**
  - `edge/append.py:125`

### Endpoint(s): /api/dashboard/final-devices/normalize-demo-status-old
- **Function:** `_d7m16_normalize_demo_device_status` (Lines 2124-2145)
- **Category:** **SAFE_TO_DELETE**
- **Confidence:** High (Only referenced by isolated `append.py`)
- **References:**
  - `edge/append.py:129`

### Endpoint(s): /api/dashboard/final-devices-v3/{device_key}/actions/{action}-old
- **Function:** `_d7m16_final_device_action_v3` (Lines 2263-2352)
- **Category:** **SAFE_TO_DELETE**
- **Confidence:** High (Only referenced by isolated `append.py`)
- **References:**
  - `edge/append.py:130`

### Endpoint(s): /api/dashboard/homes-v3/{home_key}/delete-old
- **Function:** `_d7m16_delete_home_v3` (Lines 2354-2405)
- **Category:** **SAFE_TO_DELETE**
- **Confidence:** High (Only referenced by isolated `append.py`)
- **References:**
  - `edge/append.py:131`

### Endpoint(s): /api/dashboard/final-devices-v4/{device_key}/actions/{action}-old
- **Function:** `_d7m16_final_device_action_v4` (Lines 2555-2642)
- **Category:** **SAFE_TO_DELETE**
- **Confidence:** High (Only referenced by isolated `append.py`)
- **References:**
  - `edge/append.py:132`

### Endpoint(s): /api/dashboard/homes-v4/{home_key}/delete-old
- **Function:** `_d7m16_delete_home_v4` (Lines 2644-2726)
- **Category:** **SAFE_TO_DELETE**
- **Confidence:** High (Only referenced by isolated `append.py`)
- **References:**
  - `edge/append.py:133`

### Endpoint(s): /api/dashboard/final-devices-v5/{device_key}/remove-old
- **Function:** `_d7m16_delete_device_v5` (Lines 2759-2812)
- **Category:** **SAFE_TO_DELETE**
- **Confidence:** High (Only referenced by isolated `append.py`)
- **References:**
  - `edge/append.py:134`

### Endpoint(s): /api/dashboard/final-qa/homes-lite-old
- **Function:** `_d7m16_final_homes_lite` (Lines 3596-3617)
- **Category:** **SAFE_TO_DELETE**
- **Confidence:** High (Only referenced by isolated `append.py`)
- **References:**
  - `edge/append.py:136`

### Endpoint(s): /api/dashboard/d7r2-device-action/{device_key}/{action}-old
- **Function:** `_d7m16_r2_device_action` (Lines 4022-4141)
- **Category:** **SAFE_TO_DELETE**
- **Confidence:** High (Only referenced by isolated `append.py`)
- **References:**
  - `edge/append.py:138`

### Endpoint(s): /api/dashboard/energy-page-data-v2-old
- **Function:** `_d7m16_energy_page_data_v2` (Lines 4444-4542)
- **Category:** **SAFE_TO_DELETE**
- **Confidence:** High (Only referenced by isolated `append.py`)
- **References:**
  - `edge/append.py:139`

### Endpoint(s): /api/dashboard/logs/{log_id}-old
- **Function:** `d7real_delete_dashboard_log` (Lines 7519-7527)
- **Category:** **SAFE_TO_DELETE**
- **Confidence:** High (Only referenced by isolated `append.py`)
- **References:**
  - `edge/append.py:140`

### Endpoint(s): /api/dashboard/logs/bulk-old
- **Function:** `d7real_delete_dashboard_logs_bulk` (Lines 7529-7560)
- **Category:** **SAFE_TO_DELETE**
- **Confidence:** High (Only referenced by isolated `append.py`)
- **References:**
  - `edge/append.py:141`

### Endpoint(s): /api/dashboard/logs-final/{log_id}-old
- **Function:** `d7final_delete_dashboard_log` (Lines 8736-8745)
- **Category:** **SAFE_TO_DELETE**
- **Confidence:** High (Only referenced by isolated `append.py`)
- **References:**
  - `edge/append.py:142`

### Endpoint(s): /api/dashboard/security-logs/{log_id}-old
- **Function:** `d7m16_final_delete_dashboard_security_log` (Lines 9098-9106)
- **Category:** **SAFE_TO_DELETE**
- **Confidence:** High (Only referenced by isolated `append.py`)
- **References:**
  - `edge/append.py:144`

### Endpoint(s): /api/dashboard/devices/{device_id}/actions/{action}-old
- **Function:** `d7_phase10_dashboard_device_action` (Lines 1465-1554)
- **Category:** **ACTIVE**
- **Confidence:** Low (Needs manual review)
- **References:**
  - `edge/main.py:1559`
  - `edge/main.py:1569`
  - `edge/append.py:127`
  - `edge/main.py:1564`

### Endpoint(s): /api/dashboard/final-devices-v6/{device_key}/actions/{action}-old, /api/dashboard/final-devices-v6/{device_key}/actions/{action}-old
- **Function:** `_d7m16_final_device_action_v6` (Lines 3236-3348)
- **Category:** **ACTIVE**
- **Confidence:** Low (Needs manual review)
- **References:**
  - `edge/append.py:135`
  - `edge/main.py:2962`
  - `edge/main.py:2961`

### Endpoint(s): /api/dashboard/d7-final-device-action/{device_key}/{action}-old
- **Function:** `_d7m16_final_device_action` (Lines 3619-3731)
- **Category:** **ACTIVE**
- **Confidence:** Low (Needs manual review)
- **References:**
  - `edge/main.py:2034`
  - `edge/append.py:137`

### Endpoint(s): /api/dashboard/logs-final/bulk-old
- **Function:** `d7final_delete_dashboard_logs_bulk` (Lines 8747-8754)
- **Category:** **ACTIVE**
- **Confidence:** Low (Needs manual review)
- **References:**
  - `edge/append.py:146`
  - `edge/main.py:9185`
  - `edge/append.py:143`

### Endpoint(s): /api/dashboard/security-logs/delete-filtered-old
- **Function:** `d7m16_final_delete_dashboard_security_logs_filtered` (Lines 9108-9115)
- **Category:** **ACTIVE**
- **Confidence:** Low (Needs manual review)
- **References:**
  - `edge/main.py:9187`
  - `edge/append.py:145`

### Endpoint(s): /api/dashboard/logs-final/bulk-old
- **Function:** `d7m16_post_dashboard_logs_final_bulk` (Lines 9185-9187)
- **Category:** **ACTIVE**
- **Confidence:** Low (Needs manual review)
- **References:**
  - `edge/main.py:8747`
  - `edge/append.py:146`
  - `edge/append.py:143`

## 4. Search Scope Verification

- All `.py`, `.dart`, `.html`, `.js`, and `.j2` files across the entire project root were scanned.
- Includes AI modules, MQTT broker config, Routers, Services, and Flutter UI widgets.

## 5. Estimated Cleanup Impact

- **Endpoints removable:** 14
- **Functions removable:** 14 primary endpoints (plus associated orphaned helpers, which will be calculated in a subsequent helper pass)
- **Estimated lines removable:** ~696 lines (excluding helpers)

## 6. Cleanup Package #2 Candidate List

- `api_dashboard_security_logs_data` (Lines 1050-1055)
- `_d7m16_normalize_demo_device_status` (Lines 2124-2145)
- `_d7m16_final_device_action_v3` (Lines 2263-2352)
- `_d7m16_delete_home_v3` (Lines 2354-2405)
- `_d7m16_final_device_action_v4` (Lines 2555-2642)
- `_d7m16_delete_home_v4` (Lines 2644-2726)
- `_d7m16_delete_device_v5` (Lines 2759-2812)
- `_d7m16_final_homes_lite` (Lines 3596-3617)
- `_d7m16_r2_device_action` (Lines 4022-4141)
- `_d7m16_energy_page_data_v2` (Lines 4444-4542)
- `d7real_delete_dashboard_log` (Lines 7519-7527)
- `d7real_delete_dashboard_logs_bulk` (Lines 7529-7560)
- `d7final_delete_dashboard_log` (Lines 8736-8745)
- `d7m16_final_delete_dashboard_security_log` (Lines 9098-9106)