## 1. Complete Call Graph

### Endpoint: _d7m16_dashboard_home_overview_data
- **Lines:** 2078-2102
- **Directly Called Functions:**
  - `_d7_rows` (Lines 1751-1760)
  - `_d7_status_online` (Lines 1813-1815)
  - `_d7_s` (Lines 1768-1769)
  - `_d7_val` (Lines 1762-1766)
  - `_d7_conn` (Lines 4921-4924)
  - `_d7_home_summary` (Lines 1966-1990)
  - `_d7_all_logs` (Lines 1862-1868)
- **Indirectly Called Functions:**
  - `_d7_pairing_code` (Lines 5986-5993)
  - `_d7_members_count` (Lines 1895-1908)
  - `_d7_device_belongs_to_home` (Lines 1831-1851)
  - `_d7_home_name` (Lines 1794-1799)
  - `_d7_apartment` (Lines 1774-1775)
  - `_d7_registered_at` (Lines 1910-1933)
  - `_d7_device_id` (Lines 1801-1802)
  - `_d7_sort_oldest` (Lines 1859-1860)
  - `_d7_log_home_matches` (Lines 1870-1893)
  - `_d7_table_names` (Lines 1715-1719)
  - `_d7_sort_newest` (Lines 1856-1857)
  - `_d7_padded_apt` (Lines 1777-1786)
  - `_d7_home_code` (Lines 5972-5983)
  - `_d7_home_pk` (Lines 1771-1772)
  - `_d7_timestamp` (Lines 1853-1854)

### Endpoint: _d7m16_dashboard_home_details_data
- **Lines:** 2105-2137
- **Directly Called Functions:**
  - `_d7_door_status_from_logs` (Lines 2062-2075)
  - `_d7_rows` (Lines 1751-1760)
  - `_d7_device_belongs_to_home` (Lines 1831-1851)
  - `_d7_device_public` (Lines 1935-1964)
  - `_d7_recent_access_for_home` (Lines 2040-2060)
  - `_d7_home_pk` (Lines 1771-1772)
  - `_d7_conn` (Lines 4921-4924)
  - `_d7_home_summary` (Lines 1966-1990)
  - `_d7_home_code` (Lines 5972-5983)
  - `_d7_all_logs` (Lines 1862-1868)
  - `_d7_latest_energy_for_home` (Lines 1992-2015)
- **Indirectly Called Functions:**
  - `_d7_pairing_code` (Lines 5986-5993)
  - `_d7_members_count` (Lines 1895-1908)
  - `_d7_clean_log_details` (Lines 2017-2038)
  - `_d7_home_name` (Lines 1794-1799)
  - `_d7_device_id` (Lines 1801-1802)
  - `_d7_status_online` (Lines 1813-1815)
  - `_d7_table_names` (Lines 1715-1719)
  - `_d7_apartment` (Lines 1774-1775)
  - `_d7_is_energy_device` (Lines 1827-1829)
  - `_d7_sort_oldest` (Lines 1859-1860)
  - `_d7_is_door_device` (Lines 1823-1825)
  - `_d7_log_home_matches` (Lines 1870-1893)
  - `_d7_s` (Lines 1768-1769)
  - `_d7_val` (Lines 1762-1766)
  - `_d7_sort_newest` (Lines 1856-1857)
  - `_d7_timestamp` (Lines 1853-1854)
  - `_d7_device_name` (Lines 1804-1805)
  - `_d7_registered_at` (Lines 1910-1933)
  - `_d7_device_type` (Lines 1807-1808)
  - `_d7_padded_apt` (Lines 1777-1786)
  - `_d7_enabled` (Lines 1817-1821)

## 2. Helper Functions Verification & 3. Categorization

### `_d7_pairing_code` (Lines 5986-5993)
- **Category:** SAFE_TO_DELETE

### `_d7_members_count` (Lines 1895-1908)
- **Category:** SAFE_TO_DELETE

### `_d7_rows` (Lines 1751-1760)
- **Category:** POSSIBLY_SHARED
- **Referenced By:** main.py -> _d7_rows(), main.py -> _d7_device_home_value()

### `_d7_device_belongs_to_home` (Lines 1831-1851)
- **Category:** POSSIBLY_SHARED
- **Referenced By:** main.py -> _d7_device_belongs_to_home()

### `_d7_device_public` (Lines 1935-1964)
- **Category:** SAFE_TO_DELETE

### `_d7_conn` (Lines 4921-4924)
- **Category:** POSSIBLY_SHARED
- **Referenced By:** main.py -> _d7_system_owner_credentials_match(), main.py -> d7_toggle_home_owner(), main.py -> d7_users_management_list(), main.py -> _d7_ensure_users_schema(), main.py -> _d7_conn(), main.py -> _d7_log_user_action(), main.py -> d7_update_system_owner()

### `_d7_home_summary` (Lines 1966-1990)
- **Category:** SAFE_TO_DELETE

### `_d7_clean_log_details` (Lines 2017-2038)
- **Category:** SAFE_TO_DELETE

### `_d7_home_code` (Lines 5972-5983)
- **Category:** POSSIBLY_SHARED
- **Referenced By:** main.py -> _d7_home_code(), main.py -> _d7_device_belongs_to_home()

### `_d7_all_logs` (Lines 1862-1868)
- **Category:** SAFE_TO_DELETE

### `_d7_door_status_from_logs` (Lines 2062-2075)
- **Category:** SAFE_TO_DELETE

### `_d7_home_name` (Lines 1794-1799)
- **Category:** SAFE_TO_DELETE

### `_d7_device_id` (Lines 1801-1802)
- **Category:** POSSIBLY_SHARED
- **Referenced By:** main.py -> _d7_device_belongs_to_home(), main.py -> _d7_device_id()

### `_d7_status_online` (Lines 1813-1815)
- **Category:** SAFE_TO_DELETE

### `_d7_table_names` (Lines 1715-1719)
- **Category:** POSSIBLY_SHARED
- **Referenced By:** main.py -> _d7_device_log(), main.py -> _d7_rows(), main.py -> _d7_get_device_row(), main.py -> _d7m16_normalize_demo_device_status(), main.py -> _d7_table_names(), main.py -> _d7_find_db()

### `_d7_apartment` (Lines 1774-1775)
- **Category:** POSSIBLY_SHARED
- **Referenced By:** main.py -> _d7_apartment(), main.py -> _d7_device_belongs_to_home(), main.py -> _d7_padded_apt()

### `_d7_is_energy_device` (Lines 1827-1829)
- **Category:** SAFE_TO_DELETE

### `_d7_sort_oldest` (Lines 1859-1860)
- **Category:** SAFE_TO_DELETE

### `_d7_log_home_matches` (Lines 1870-1893)
- **Category:** SAFE_TO_DELETE

### `_d7_is_door_device` (Lines 1823-1825)
- **Category:** SAFE_TO_DELETE

### `_d7_s` (Lines 1768-1769)
- **Category:** POSSIBLY_SHARED
- **Referenced By:** main.py -> _d7_device_type(), main.py -> _d7_s(), main.py -> _d7_device_belongs_to_home(), main.py -> _d7_device_id()

### `_d7_val` (Lines 1762-1766)
- **Category:** POSSIBLY_SHARED
- **Referenced By:** main.py -> _d7_val(), main.py -> _d7_device_id(), main.py -> _d7_home_pk(), main.py -> _d7_device_type(), main.py -> _d7_home_code(), main.py -> _d7_apartment(), main.py -> _d7_device_belongs_to_home()

### `_d7_sort_newest` (Lines 1856-1857)
- **Category:** SAFE_TO_DELETE

### `_d7_home_pk` (Lines 1771-1772)
- **Category:** POSSIBLY_SHARED
- **Referenced By:** main.py -> _d7_home_pk(), main.py -> _d7_home_code(), main.py -> _d7_device_belongs_to_home(), main.py -> _d7_padded_apt()

### `_d7_timestamp` (Lines 1853-1854)
- **Category:** SAFE_TO_DELETE

### `_d7_device_name` (Lines 1804-1805)
- **Category:** SAFE_TO_DELETE

### `_d7_registered_at` (Lines 1910-1933)
- **Category:** SAFE_TO_DELETE

### `_d7_device_type` (Lines 1807-1808)
- **Category:** POSSIBLY_SHARED
- **Referenced By:** main.py -> _d7_device_type(), main.py -> _d7_device_type_l()

### `_d7_recent_access_for_home` (Lines 2040-2060)
- **Category:** SAFE_TO_DELETE

### `_d7_padded_apt` (Lines 1777-1786)
- **Category:** POSSIBLY_SHARED
- **Referenced By:** main.py -> _d7_device_belongs_to_home(), main.py -> _d7_padded_apt()

### `_d7_enabled` (Lines 1817-1821)
- **Category:** SAFE_TO_DELETE

### `_d7_latest_energy_for_home` (Lines 1992-2015)
- **Category:** SAFE_TO_DELETE

## 4. Deletion Package

### `_d7_pairing_code`
- **Start Line:** 5986
- **End Line:** 5993
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_members_count`
- **Start Line:** 1895
- **End Line:** 1908
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_device_public`
- **Start Line:** 1935
- **End Line:** 1964
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_home_summary`
- **Start Line:** 1966
- **End Line:** 1990
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_clean_log_details`
- **Start Line:** 2017
- **End Line:** 2038
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_all_logs`
- **Start Line:** 1862
- **End Line:** 1868
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_door_status_from_logs`
- **Start Line:** 2062
- **End Line:** 2075
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_home_name`
- **Start Line:** 1794
- **End Line:** 1799
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_status_online`
- **Start Line:** 1813
- **End Line:** 1815
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_is_energy_device`
- **Start Line:** 1827
- **End Line:** 1829
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_sort_oldest`
- **Start Line:** 1859
- **End Line:** 1860
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_log_home_matches`
- **Start Line:** 1870
- **End Line:** 1893
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_is_door_device`
- **Start Line:** 1823
- **End Line:** 1825
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_sort_newest`
- **Start Line:** 1856
- **End Line:** 1857
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_timestamp`
- **Start Line:** 1853
- **End Line:** 1854
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_device_name`
- **Start Line:** 1804
- **End Line:** 1805
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_registered_at`
- **Start Line:** 1910
- **End Line:** 1933
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_recent_access_for_home`
- **Start Line:** 2040
- **End Line:** 2060
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_enabled`
- **Start Line:** 1817
- **End Line:** 1821
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7_latest_energy_for_home`
- **Start Line:** 1992
- **End Line:** 2015
- **Reason:** Only referenced by target safe-to-delete endpoints or other dead helpers.

### `_d7m16_dashboard_home_overview_data`
- **Start Line:** 2078
- **End Line:** 2102
- **Reason:** Primary legacy endpoint. No active references across codebase.

### `_d7m16_dashboard_home_details_data`
- **Start Line:** 2105
- **End Line:** 2137
- **Reason:** Primary legacy endpoint. No active references across codebase.

## 5. Calculations
- **Total lines removable:** 299
- **Total functions removable:** 22
- **Risk score:** 1/10 (High confidence. Functions are entirely orphaned and self-contained).

## 6. System Impact Verification

The following core systems have been explicitly verified against this deletion package:
- **Face Recognition:** Not affected. (AI modules do not call `_d7` helper paths).
- **MQTT:** Not affected. (MQTT broker connections and packet listeners are separate).
- **Smart Door Unlock:** Not affected. (Active `api_door_unlock` and `mqtt` hardware events don't rely on `_d7m16` legacy dashboard calls).
- **Camera APIs:** Not affected. (RTSP/WebRTC feeds run on separate threads/endpoints).
- **Authentication APIs:** Not affected. (`login`, `token`, `biometric` endpoints do not use legacy `_d7` dashboard formatting helpers).
- **Family Photos APIs:** Not affected. (`add_member`, `enroll_face` routines have standalone logic).
