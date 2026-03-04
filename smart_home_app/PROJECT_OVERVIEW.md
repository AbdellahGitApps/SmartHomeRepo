# Project Summary: أكسيس (Axis) Smart Home App

**أكسيس** (Axis) is a professional Smart Home application built with **Flutter**. It features a "Gold & Slate" premium design, smooth animations, and is fully bilingual (English & Arabic).

---

## 🏗️ Technical Architecture (File by File)

### 1. Core & Configuration
*   **`lib/main.dart`**: The application's entry point. It initializes state management (**Provider**), configures localization, and routes users to either the login or the main dashboard.
*   **`pubspec.yaml`**: Defines project metadata, dependencies (like `lucide_icons` for icons and `fl_chart` for energy graphs), and asset paths (images, fonts).

### 2. Branding & Design System
*   **`lib/theme/app_theme.dart`**: The "brain" of the UI. It defines the premium color palette (Luxurious Gold, Deep Slate) and handles switching between **Light** and **Dark** modes.
*   **`lib/providers/app_state_provider.dart`**: Manages the global state of the app, including:
    *   Theme selection (Light/Dark/System).
    *   Language selection (English/Arabic).
    *   Authentication status and User Profile (Name, Role).

### 3. Localization (L10n)
*   **`lib/l10n/`**: Contains `.arb` files (`app_ar.arb`, `app_en.arb`) providing a fully bilingual experience. Every string in the app is localized for seamless Arabic support.

### 4. Screens (UI Pages)
*   **`lib/screens/home_dashboard.dart`**: The central hub featuring a "System Secure" status, user greetings, energy summaries, and interactive device controls.
*   **`lib/screens/energy_screen.dart`**: Analytics page for energy consumption using data visualizations.
*   **`lib/screens/login_screen.dart`**: High-fidelity entry screen for user authentication.
*   **`lib/screens/doors_screen.dart` / `lib/screens/camera_screen.dart`**: Specific interfaces for smart locks and security feeds.
*   **`lib/screens/profile_screen.dart`**: User management and settings portal.

### 5. Data & Components
*   **`lib/models/device_model.dart`**: Defines the data structure for smart devices (Lights, Locks, Sensors).
*   **`lib/widgets/device_card.dart`**: A reusable, animated card component representing a device state.
*   **`lib/widgets/simple_energy_chart.dart`**: A customized chart component for energy visualizations.
*   **`lib/widgets/settings_dialog.dart`**: A clean, modal interface for quick app settings.

---

## 🎨 Key Features
*   **Premium Aesthetics**: Uses glassmorphism and custom gradients.
*   **Full RTL Support**: Native Arabic layout and font integration.
*   **Stateful Control**: Real-time toggling of smart devices.
*   **Data Driven**: Integrated energy tracking and system status monitoring.
