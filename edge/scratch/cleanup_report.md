# Phase 10: main.py Cleanup Analysis Report

## Section 1: Safe-To-Delete Endpoints

- **Path:** `GET /api/dashboard/home-overview-data-old`
  - **Function:** `_d7m16_dashboard_home_overview_data` (Line 2078)
  - **Confidence:** High
  - **Reason:** No references found across Python, JS, Dart, HTML, templates, or router files.

- **Path:** `GET /api/dashboard/home-details-data-old`
  - **Function:** `_d7m16_dashboard_home_details_data` (Line 2105)
  - **Confidence:** High
  - **Reason:** No references found across Python, JS, Dart, HTML, templates, or router files.

## Section 2: Potentially Active Legacy Endpoints

- **Path:** `GET /api/dashboard/security-logs-data-old`
  - **Function:** `api_dashboard_security_logs_data`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:125`

- **Path:** `POST /api/dashboard/devices/{device_id}/actions/{action}-old`
  - **Function:** `d7_phase10_dashboard_device_action`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:127`

- **Path:** `POST /api/dashboard/final-devices/normalize-demo-status-old`
  - **Function:** `_d7m16_normalize_demo_device_status`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:129`

- **Path:** `POST /api/dashboard/final-devices-v3/{device_key}/actions/{action}-old`
  - **Function:** `_d7m16_final_device_action_v3`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:130`

- **Path:** `POST /api/dashboard/homes-v3/{home_key}/delete-old`
  - **Function:** `_d7m16_delete_home_v3`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:131`

- **Path:** `POST /api/dashboard/final-devices-v4/{device_key}/actions/{action}-old`
  - **Function:** `_d7m16_final_device_action_v4`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:132`

- **Path:** `POST /api/dashboard/homes-v4/{home_key}/delete-old`
  - **Function:** `_d7m16_delete_home_v4`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:133`

- **Path:** `POST /api/dashboard/final-devices-v5/{device_key}/remove-old`
  - **Function:** `_d7m16_delete_device_v5`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:134`

- **Path:** `POST /api/dashboard/final-devices-v6/{device_key}/actions/{action}-old`
  - **Function:** `_d7m16_final_device_action_v6`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:135`

- **Path:** `POST /api/dashboard/final-devices-v6/{device_key}/actions/{action}-old`
  - **Function:** `_d7m16_final_device_action_v6`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:135`

- **Path:** `GET /api/dashboard/final-qa/homes-lite-old`
  - **Function:** `_d7m16_final_homes_lite`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:136`

- **Path:** `POST /api/dashboard/d7-final-device-action/{device_key}/{action}-old`
  - **Function:** `_d7m16_final_device_action`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:137`

- **Path:** `POST /api/dashboard/d7r2-device-action/{device_key}/{action}-old`
  - **Function:** `_d7m16_r2_device_action`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:138`

- **Path:** `GET /api/dashboard/energy-page-data-v2-old`
  - **Function:** `_d7m16_energy_page_data_v2`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:139`

- **Path:** `DELETE /api/dashboard/logs/{log_id}-old`
  - **Function:** `d7real_delete_dashboard_log`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:140`

- **Path:** `DELETE /api/dashboard/logs/bulk-old`
  - **Function:** `d7real_delete_dashboard_logs_bulk`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:141`

- **Path:** `DELETE /api/dashboard/logs-final/{log_id}-old`
  - **Function:** `d7final_delete_dashboard_log`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:142`

- **Path:** `DELETE /api/dashboard/logs-final/bulk-old`
  - **Function:** `d7final_delete_dashboard_logs_bulk`
  - **Confidence:** Low (Needs manual review)
  - **References Found (2):**
    - `edge\append.py:143`
    - `edge\append.py:146`

- **Path:** `DELETE /api/dashboard/security-logs/{log_id}-old`
  - **Function:** `d7m16_final_delete_dashboard_security_log`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:144`

- **Path:** `POST /api/dashboard/security-logs/delete-filtered-old`
  - **Function:** `d7m16_final_delete_dashboard_security_logs_filtered`
  - **Confidence:** Low (Needs manual review)
  - **References Found (1):**
    - `edge\append.py:145`

- **Path:** `POST /api/dashboard/logs-final/bulk-old`
  - **Function:** `d7m16_post_dashboard_logs_final_bulk`
  - **Confidence:** Low (Needs manual review)
  - **References Found (2):**
    - `edge\append.py:143`
    - `edge\append.py:146`

## Section 3: Dead Helper Functions

- **Function:** `_d7_enabled` (Line 1817)
  - **Called By:** _d7_device_public

- **Function:** `_d7_is_door_device` (Line 1823)
  - **Called By:** _d7_device_public

- **Function:** `_d7_all_logs` (Line 1862)
  - **Called By:** _d7m16_dashboard_home_overview_data, _d7m16_dashboard_home_details_data, _d7_recent_access_for_home

- **Function:** `_d7_members_count` (Line 1895)
  - **Called By:** _d7_home_summary

- **Function:** `_d7_status_online` (Line 1813)
  - **Called By:** _d7_device_public, _d7m16_dashboard_home_overview_data, _d7_home_summary

- **Function:** `_d7_padded_apt` (Line 1777)
  - **Called By:** _d7_home_code, _d7_device_belongs_to_home

- **Function:** `_d7_log_home_matches` (Line 1870)
  - **Called By:** _d7_latest_energy_for_home, _d7_registered_at, _d7_recent_access_for_home

- **Function:** `_d7_apartment` (Line 1774)
  - **Called By:** _d7_home_summary, _d7_members_count, _d7_padded_apt, _d7_home_name, _d7_log_home_matches, _d7_device_belongs_to_home

- **Function:** `_d7_home_summary` (Line 1966)
  - **Called By:** _d7m16_dashboard_home_overview_data, _d7m16_dashboard_home_details_data

- **Function:** `_d7_home_pk` (Line 1771)
  - **Called By:** _d7_device_belongs_to_home, _d7_members_count, _d7_home_code, _d7_padded_apt, _d7_log_home_matches, _d7m16_dashboard_home_details_data, _d7_home_summary

- **Function:** `_d7_registered_at` (Line 1910)
  - **Called By:** _d7_home_summary

- **Function:** `_d7_home_name` (Line 1794)
  - **Called By:** _d7_home_summary

- **Function:** `_d7_clean_log_details` (Line 2017)
  - **Called By:** _d7_recent_access_for_home

- **Function:** `_d7_device_belongs_to_home` (Line 1831)
  - **Called By:** _d7_home_summary, _d7_registered_at, _d7m16_dashboard_home_details_data

- **Function:** `_d7_is_energy_device` (Line 1827)
  - **Called By:** _d7_latest_energy_for_home, _d7_device_public

- **Function:** `_d7_home_code` (Line 5972)
  - **Called By:** _d7_home_summary, _d7m16_dashboard_home_details_data, _d7_home_name, _d7_log_home_matches, _d7_pairing_code, _d7_device_belongs_to_home

- **Function:** `_d7_sort_newest` (Line 1856)
  - **Called By:** _d7_latest_energy_for_home, _d7_all_logs

- **Function:** `_d7_device_name` (Line 1804)
  - **Called By:** _d7_device_public, _d7_is_energy_device, _d7_is_door_device

- **Function:** `_d7_device_id` (Line 1801)
  - **Called By:** _d7_device_public, _d7_device_belongs_to_home, _d7_is_door_device, _d7_latest_energy_for_home, _d7_is_energy_device

- **Function:** `_d7_timestamp` (Line 1853)
  - **Called By:** _d7_latest_energy_for_home, _d7_sort_newest, _d7_registered_at, _d7_sort_oldest, _d7_recent_access_for_home

- **Function:** `_d7_pairing_code` (Line 5986)
  - **Called By:** _d7_home_summary

- **Function:** `_d7_device_public` (Line 1935)
  - **Called By:** _d7m16_dashboard_home_details_data

- **Function:** `_d7_door_status_from_logs` (Line 2062)
  - **Called By:** _d7m16_dashboard_home_details_data

- **Function:** `_d7_latest_energy_for_home` (Line 1992)
  - **Called By:** _d7m16_dashboard_home_details_data

- **Function:** `_d7_sort_oldest` (Line 1859)
  - **Called By:** _d7_registered_at

- **Function:** `_d7_recent_access_for_home` (Line 2040)
  - **Called By:** _d7m16_dashboard_home_details_data

## Section 4: Estimated Cleanup Impact

- **Endpoints removable:** 2
- **Functions removable:** 28 (Endpoints + Helpers)
- **Lines removable:** ~348
- **Risk level:** Low (Assuming complete deletion of Safe-To-Delete and Dead Helpers)

## Section 5: Recommended Removal Order

1. **Remove Safe-To-Delete Endpoints:** Begin by deleting the endpoint functions listed in Section 1 one by one.
2. **Remove Orphaned Helpers:** Delete the helper functions listed in Section 3.
3. **Verify App Stability:** Run FastAPI server and ensure no startup errors (`PRAGMA integrity_check = ok`).
4. **Manual Review of Potentially Active Endpoints:** Check the references in Section 2 to see if they are commented out or dead code in the frontend before deleting.