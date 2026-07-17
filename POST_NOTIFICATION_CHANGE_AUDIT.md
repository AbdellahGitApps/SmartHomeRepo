# POST-NOTIFICATION CHANGE AUDIT

This report provides a strict read-only forensic audit of all project changes made starting from the implementation of the LAN-only Android background notification feature. The goal is to provide a safe, surgical rollback plan to the exact state immediately before the notification work began, while fully preserving older unrelated work (such as the offline font migration and dashboard status updates).

## STEP 4 — FILE-BY-FILE REPORT

### 1. `smart_home_app/lib/main.dart`
* **STATUS:** Modified
* **CATEGORY:** Notification feature / Notification runtime fix
* **EXACT CHANGES:** Wrapped `Permission.notification.request()` and `BackgroundNotificationService.initialize()` in a `Future.microtask()` to prevent blocking `runApp()`.
* **ROLLBACK RECOMMENDATION:** **ROLLBACK**
* **REASON:** These lines were added purely to initialize the background notification feature.

### 2. `smart_home_app/lib/services/background_notification_service.dart`
* **STATUS:** New (Untracked)
* **CATEGORY:** Notification feature
* **EXACT CHANGES:** Created file implementing the Android foreground service, local notifications plugin, and background MQTT subscription.
* **ROLLBACK RECOMMENDATION:** **DELETE**
* **REASON:** Exists exclusively for the background notification system.

### 3. `smart_home_app/android/app/src/main/AndroidManifest.xml`
* **STATUS:** Modified
* **CATEGORY:** Notification feature
* **EXACT CHANGES:** Added permissions (`INTERNET`, `POST_NOTIFICATIONS`, `WAKE_LOCK`, `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_DATA_SYNC`, `RECEIVE_BOOT_COMPLETED`) and declared the `<service android:name="id.flutter.flutter_background_service.BackgroundService" />`.
* **ROLLBACK RECOMMENDATION:** **ROLLBACK**
* **REASON:** All additions satisfy Android 14 requirements for the background notification service.

### 4. `smart_home_app/android/app/build.gradle.kts`
* **STATUS:** Modified
* **CATEGORY:** Notification build fix
* **EXACT CHANGES:** Enabled `isCoreLibraryDesugaringEnabled = true` and added `coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.5")`.
* **ROLLBACK RECOMMENDATION:** **ROLLBACK**
* **REASON:** Added solely to fix a core library desugaring conflict introduced by the `flutter_local_notifications` package.

### 5. `smart_home_app/android/gradle.properties`
* **STATUS:** Modified
* **CATEGORY:** Notification build fix
* **EXACT CHANGES:** Added `kotlin.incremental=false`.
* **ROLLBACK RECOMMENDATION:** **ROLLBACK**
* **REASON:** Added to bypass build caching issues during troubleshooting of the notification feature.

### 6. `edge/services/image_upload_service.py`
* **STATUS:** Modified
* **CATEGORY:** Notification feature
* **EXACT CHANGES:** Added MQTT publish logic (`type: UNKNOWN_PERSON`) to the `home/{home_id}/alerts/critical` topic.
* **ROLLBACK RECOMMENDATION:** **ROLLBACK**
* **REASON:** Added exclusively to trigger the Flutter background notification payload.

### 7. `firmware/esp32_cam/esp32_cam.ino`
* **STATUS:** Modified
* **CATEGORY:** ESP32 capture change after notifications
* **EXACT CHANGES:** Refactored `loop()` to use a state machine (`STATE_IDLE`, `STATE_DETECTING_PRESENCE`, etc.) for presence debouncing instead of periodic capture.
* **ROLLBACK RECOMMENDATION:** **ROLLBACK**
* **REASON:** Modifying this was requested *after* notification work began. Reverting it brings back the original `cooldownFinished` logic.

### 8. `smart_home_app/pubspec.yaml`
* **STATUS:** Modified
* **CATEGORY:** Notification feature / Unrelated older work
* **EXACT CHANGES:** Removed `google_fonts` and added local font assets (older work). Added `mqtt_client`, `flutter_local_notifications`, `flutter_background_service` (notification feature).
* **ROLLBACK RECOMMENDATION:** **MANUAL REVIEW**
* **REASON:** Contains mixed changes. The font changes MUST be kept. Only the three notification packages should be removed.

### 9. `smart_home_app/pubspec.lock`
* **STATUS:** Modified
* **CATEGORY:** Notification feature / Unrelated older work
* **EXACT CHANGES:** Contains transitive dependencies for fonts and notifications.
* **ROLLBACK RECOMMENDATION:** **MANUAL REVIEW**
* **REASON:** Do not revert directly. Run `flutter pub get` after carefully editing `pubspec.yaml`.

### 10. `firmware/energy_meter/secrets.h` & `firmware/esp32_cam/secrets.h`
* **STATUS:** Modified
* **CATEGORY:** Uncertain
* **EXACT CHANGES:** Changed Wi-Fi SSID (`BOLBA(235)`), Server IP (`172.17.235.4`), and device tokens.
* **ROLLBACK RECOMMENDATION:** **MANUAL REVIEW**
* **REASON:** These are environment network updates. Blindly rolling them back will likely break ESP32 connectivity to the current LAN.

---

## STEP 5 — DEPENDENCY AUDIT

The following configurations were introduced specifically for the notification implementation and should be removed to restore the pre-notification baseline:

* **Flutter Packages:**
  * `mqtt_client`
  * `flutter_local_notifications`
  * `flutter_background_service`
* **Android Gradle Dependencies:**
  * `coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.5")`
* **Android Permissions:**
  * `POST_NOTIFICATIONS`
  * `WAKE_LOCK`
  * `FOREGROUND_SERVICE`
  * `FOREGROUND_SERVICE_DATA_SYNC`
  * `RECEIVE_BOOT_COMPLETED`
  * `INTERNET` (in app manifest)
* **Android Services:**
  * `id.flutter.flutter_background_service.BackgroundService`
* **Gradle Properties:**
  * `kotlin.incremental=false`

---

## STEP 6 — ESP32 FIRMWARE AUDIT

* **Exact files changed:** `firmware/esp32_cam/esp32_cam.ino`
* **Previous behavior:** Periodic "blind" image capture every 10 seconds (`COOLDOWN_MS = 10000`) as long as someone was closer than `DETECTION_DISTANCE`.
* **Current behavior:** State-based trigger that captures once per confirmed presence event (`PRESENCE_DEBOUNCE_MS`), and waits for the person to leave the zone (`LEAVE_DEBOUNCE_MS`) before resetting.
* **Exact code sections introduced:** `enum SystemState` definition, state tracking variables (`currentState`, `stateChangeTime`), and the `switch (currentState)` block replacing the `if (objectDetected && cooldownFinished)` logic in `loop()`.
* **Reverting result:** Yes, reverting those specific sections perfectly restores the previous periodic capture behavior.

---

## STEP 7 — SAFE ROLLBACK PLAN (PROPOSED)

**DO NOT run `git reset --hard` or `git checkout .`. Doing so will destroy the offline dashboard font and phosphor icon work, as well as the new live Dashboard System Status implementation.**

### GROUP A — SAFE TO ROLLBACK
Execute `git checkout` or `git restore` on these files ONLY:
1. `smart_home_app/android/app/src/main/AndroidManifest.xml`
2. `smart_home_app/android/app/build.gradle.kts`
3. `smart_home_app/android/gradle.properties`
4. `smart_home_app/lib/main.dart`
5. `edge/services/image_upload_service.py`
6. `firmware/esp32_cam/esp32_cam.ino`

### GROUP B — SAFE TO DELETE
Delete these new files:
1. `smart_home_app/lib/services/background_notification_service.dart`

### GROUP C — KEEP (DO NOT TOUCH)
These files contain older important offline and dashboard work:
1. `edge/dashboard/static/css/style.css`
2. `edge/dashboard/templates/base.html`
3. `edge/dashboard/templates/status.html`
4. `edge/main.py`
5. `edge/mqtt/mqtt_client.py`
6. `smart_home_app/lib/screens/splash_screen.dart`
7. `smart_home_app/lib/theme/app_theme.dart`
8. All untracked font and icon files (`/static/fonts/`, `/static/vendor/`, `/assets/fonts/`).

### GROUP D — MANUAL REVIEW
1. **`smart_home_app/pubspec.yaml`**: Open this file and manually delete `mqtt_client`, `flutter_local_notifications`, and `flutter_background_service`. Leave the `fonts:` declarations intact. Run `flutter pub get` afterward.
2. **`firmware/energy_meter/secrets.h` & `firmware/esp32_cam/secrets.h`**: Ensure the IPs and Wi-Fi SSIDs match the network currently being used. Do not revert blindly.
