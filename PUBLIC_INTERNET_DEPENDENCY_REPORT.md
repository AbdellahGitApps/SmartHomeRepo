# Public Internet Dependency Audit

## 1. Executive Summary

Following a comprehensive, direct source-code inspection of the entire Smart Home project (`edge/` and `smart_home_app/`), the system was audited to differentiate between Public Internet requirements and Local Area Network (LAN) requirements.

There are exactly **3 VERIFIED runtime public Internet dependencies** in the entire system. All of these are strictly front-end visual/cosmetic dependencies. The core operational logic, security, automation, and AI are completely offline.

## 2. What Currently Requires Public Internet

1. **`google_fonts` Flutter Package:** Used by the Flutter mobile application to render typography.
2. **Google Fonts CDNs (`fonts.googleapis.com` & `fonts.gstatic.com`):** Used by the Web Dashboard for typography.
3. **Phosphor Icons CDN (`unpkg.com/@phosphor-icons/web`):** Used by the Web Dashboard for UI icons.

## 3. What Does NOT Require Public Internet

The vast majority of the system relies exclusively on the **Local LAN**:

- **FastAPI Backend:** Runs locally without calling any external cloud APIs.
- **Databases:** SQLite databases (`smart_home_edge.db` and `smart_home_models.db`) are fully local.
- **MQTT Broker:** Facilitates local messaging between backend and devices without internet relay.
- **Hardware Integration:** Both ESP32-CAM and ESP32 Energy Meter report directly to local IPs (`10.0.0.23:8000`).
- **Flutter API Calls:** Mobile commands route to the local backend using local HTTP endpoints.

## 4. Flutter Internet Dependencies

- **Dependency:** `google_fonts` package.
- **Usage:** Specifically `GoogleFonts.montserrat(...)` found in `E:\SmartHomeMobileApp\smart_home_app\lib\screens\splash_screen.dart`.
- **Behavior Without Internet:** The app does not crash, but the `google_fonts` package fails to fetch the requested font. The UI degrades to the default fallback system font, resulting in visual inconsistency.
- **Classification:** RUNTIME INTERNET OPTIONAL (Visual Degradation).

## 5. Dashboard Internet Dependencies

- **Dependencies:**
  - `https://fonts.googleapis.com` & `https://fonts.gstatic.com`
  - `https://unpkg.com/@phosphor-icons/web`
- **Usage:** Found directly in `E:\SmartHomeMobileApp\edge\dashboard\templates\base.html`.
- **Behavior Without Internet:** The HTML loads and the dashboard remains fully functional. However, typography falls back to system defaults, and icons appear as broken missing-image boxes.
- **Classification:** RUNTIME INTERNET OPTIONAL (Visual Degradation).

## 6. Backend Internet Dependencies

- **Dependencies:** None.
- **Analysis:** Direct inspection of the FastAPI backend (`E:\SmartHomeMobileApp\edge\api\`, `services\`, etc.) reveals no outbound public network calls (`requests`, `httpx`, `aiohttp`, etc.). Communication is exclusively via LAN (e.g., retrieving camera frames over local Wi-Fi or MQTT).
- **Classification:** LOCAL LAN — NOT INTERNET.

## 7. AI Internet Dependencies

- **Dependencies:** None.
- **Analysis:** Inspection of `E:\SmartHomeMobileApp\edge\ai\` proves that Face Recognition (Haar Cascades, ArcFace ONNX) and Energy Prediction (XGBoost) models are all stored on disk and loaded locally. There are no runtime API calls to external cloud AI providers.
- **Classification:** FULLY OFFLINE.

## 8. ESP32-CAM Internet Dependencies

- **Dependencies:** None.
- **Analysis:** Firmware operates strictly over local Wi-Fi connecting to `10.0.0.23` over HTTP (for image upload) and MQTT (for servo triggering).
- **Classification:** LOCAL LAN — NOT INTERNET.

## 9. Energy Meter Internet Dependencies

- **Dependencies:** None.
- **Analysis:** Firmware sends readings strictly over local Wi-Fi via an HTTP POST request to `10.0.0.23`.
- **Classification:** LOCAL LAN — NOT INTERNET.

## 10. Complete Dependency Table

| Dependency                    | Component     | Exact File                         | Internet Required? | Purpose  | Failure Without Internet                    | Recommended Offline Alternative                                     |
| :---------------------------- | :------------ | :--------------------------------- | :----------------- | :------- | :------------------------------------------ | :------------------------------------------------------------------ |
| `google_fonts` (Montserrat) | Flutter App   | `lib/screens/splash_screen.dart` | OPTIONAL           | Styling  | Cosmetic: Falls back to default system font | Bundle`Montserrat.ttf` in `assets/fonts/`                       |
| Google Fonts CDN              | Web Dashboard | `dashboard/templates/base.html`  | OPTIONAL           | Styling  | Cosmetic: Falls back to default system font | Download and serve`Inter` webfonts via FastAPI `/static/fonts/` |
| Phosphor Icons CDN            | Web Dashboard | `dashboard/templates/base.html`  | OPTIONAL           | UI Icons | Cosmetic: Missing icons in UI               | Download Phosphor files and serve via FastAPI`/static/icons/`     |

_(Note: `pub.dev` package fetching and `pip` installation are BUILD-TIME INTERNET dependencies only. Android schemas like `http://schemas.android.com/` are XML namespaces, not runtime requests.)_

## 11. Offline Alternative for Every Dependency

**1. Flutter `google_fonts` Replacement**

- **Current Architecture:** Flutter → Internet → Google Fonts API
- **Recommended Offline Architecture:** Flutter → Local bundled font asset
- **Implementation:** Download the `Montserrat` font, place it inside `smart_home_app/assets/fonts/`, declare it in `pubspec.yaml` under `fonts:`, and replace `GoogleFonts.montserrat` with `TextStyle(fontFamily: 'Montserrat')`.

**2. Web Dashboard Fonts Replacement**

- **Current Architecture:** Browser → Internet → fonts.googleapis.com
- **Recommended Offline Architecture:** Browser → Local HTTP → FastAPI Static Folder
- **Implementation:** Download `Inter` `.woff2` files, place them in `edge/dashboard/static/fonts/`, and reference them directly in `style.css` using `@font-face`.

**3. Web Dashboard Icons Replacement**

- **Current Architecture:** Browser → Internet → unpkg.com
- **Recommended Offline Architecture:** Browser → Local HTTP → FastAPI Static Folder
- **Implementation:** Download the Phosphor Icons web package, store it in `edge/dashboard/static/icons/`, and link to the local CSS file in `base.html`.

## 12. Files That Would Need Modification

- `E:\SmartHomeMobileApp\smart_home_app\pubspec.yaml` (Remove `google_fonts`, register local assets)
- `E:\SmartHomeMobileApp\smart_home_app\lib\screens\splash_screen.dart` (Remove import, switch to `TextStyle`)
- `E:\SmartHomeMobileApp\edge\dashboard\templates\base.html` (Remove CDN links, add static links)
- Additions:
  - `E:\SmartHomeMobileApp\smart_home_app\assets\fonts\Montserrat.ttf`
  - `E:\SmartHomeMobileApp\edge\dashboard\static\fonts\...`
  - `E:\SmartHomeMobileApp\edge\dashboard\static\icons\...`

**Difficulty:** EASY
**Risk:** LOW

## 13. Recommended Migration Plan

**Phase 1: Web Dashboard Localization**

- Download Phosphor Icons and Inter fonts.
- Add them to the backend's static directory.
- Update `base.html` and verify the dashboard looks correct on a browser without an internet connection.

**Phase 2: Flutter App Localization**

- Download Montserrat fonts into Flutter assets.
- Update `pubspec.yaml` and `splash_screen.dart`.
- Verify the mobile app runs beautifully even when the phone is on an isolated Wi-Fi access point.

## 14. Expected System After Removing Internet Dependencies

After successfully executing the migration plan, **PUBLIC INTERNET REQUIRED = ZERO**.
The system will become a true, isolated Intranet platform. A user could completely unplug their modem from the wall, leaving only the local Wi-Fi router active, and the Smart Home would operate flawlessly with zero functionality loss and zero visual degradation.

## 15. Final Verdict

**1. Can the entire Smart Home system currently work without public Internet?**
Yes. The core functionality is highly resilient and operates purely via LAN.

**2. If not, exactly which features fail?**
No operational or security features fail.

**3. Are those failures functional or only visual/cosmetic?**
The failures are strictly visual/cosmetic. The web dashboard will lose its icons and custom fonts, and the Flutter app's splash screen will default to system fonts.

**4. What exact changes would make PUBLIC INTERNET REQUIRED = ZERO?**
Downloading three assets (Flutter font, Dashboard font, Dashboard icons) and hosting them locally via the Flutter asset bundle and FastAPI's `/static/` folder.

**5. After those changes, would everything still work normally over local Wi-Fi/LAN?**
Yes. The entire system—FastAPI backend, ESP32 automation, AI inference, and the Flutter app—would continue to communicate perfectly over local Wi-Fi/LAN, with completely preserved aesthetics and zero reliance on the outside world.
