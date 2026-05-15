import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_ar.dart';
import 'app_localizations_en.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('ar'),
    Locale('en'),
  ];

  /// The title of the application
  ///
  /// In en, this message translates to:
  /// **'Axis   أكســــيس'**
  String get appTitle;

  /// No description provided for @home.
  ///
  /// In en, this message translates to:
  /// **'Home'**
  String get home;

  /// No description provided for @doors.
  ///
  /// In en, this message translates to:
  /// **'Doors'**
  String get doors;

  /// No description provided for @energy.
  ///
  /// In en, this message translates to:
  /// **'Energy'**
  String get energy;

  /// No description provided for @alerts.
  ///
  /// In en, this message translates to:
  /// **'Alerts'**
  String get alerts;

  /// No description provided for @camera.
  ///
  /// In en, this message translates to:
  /// **'Camera'**
  String get camera;

  /// No description provided for @greeting.
  ///
  /// In en, this message translates to:
  /// **'Hello, Abdellah'**
  String get greeting;

  /// No description provided for @welcomeBack.
  ///
  /// In en, this message translates to:
  /// **'Welcome back'**
  String get welcomeBack;

  /// No description provided for @electricity.
  ///
  /// In en, this message translates to:
  /// **'Electricity'**
  String get electricity;

  /// No description provided for @devicesActive.
  ///
  /// In en, this message translates to:
  /// **'Active Device'**
  String get devicesActive;

  /// No description provided for @energyConsumption.
  ///
  /// In en, this message translates to:
  /// **'Consumption'**
  String get energyConsumption;

  /// No description provided for @statusNormal.
  ///
  /// In en, this message translates to:
  /// **'Normal'**
  String get statusNormal;

  /// No description provided for @statusActive.
  ///
  /// In en, this message translates to:
  /// **'Active'**
  String get statusActive;

  /// No description provided for @statusLocked.
  ///
  /// In en, this message translates to:
  /// **'Fully Locked'**
  String get statusLocked;

  /// No description provided for @statusUnlocked.
  ///
  /// In en, this message translates to:
  /// **'Unlocked'**
  String get statusUnlocked;

  /// No description provided for @mainDoor.
  ///
  /// In en, this message translates to:
  /// **'Main Door'**
  String get mainDoor;

  /// No description provided for @garageDoor.
  ///
  /// In en, this message translates to:
  /// **'Garage Door'**
  String get garageDoor;

  /// No description provided for @backDoor.
  ///
  /// In en, this message translates to:
  /// **'Back Door'**
  String get backDoor;

  /// No description provided for @viewAll.
  ///
  /// In en, this message translates to:
  /// **'View All'**
  String get viewAll;

  /// No description provided for @settings.
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get settings;

  /// No description provided for @theme.
  ///
  /// In en, this message translates to:
  /// **'Theme'**
  String get theme;

  /// No description provided for @language.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get language;

  /// No description provided for @lightMode.
  ///
  /// In en, this message translates to:
  /// **'Light'**
  String get lightMode;

  /// No description provided for @darkMode.
  ///
  /// In en, this message translates to:
  /// **'Dark'**
  String get darkMode;

  /// No description provided for @noAlerts.
  ///
  /// In en, this message translates to:
  /// **'No alerts currently'**
  String get noAlerts;

  /// No description provided for @kW.
  ///
  /// In en, this message translates to:
  /// **'kW'**
  String get kW;

  /// No description provided for @clear.
  ///
  /// In en, this message translates to:
  /// **'Clear'**
  String get clear;

  /// No description provided for @weeklyOverview.
  ///
  /// In en, this message translates to:
  /// **'Weekly Overview'**
  String get weeklyOverview;

  /// No description provided for @highEnergyUsage.
  ///
  /// In en, this message translates to:
  /// **'High Energy Usage'**
  String get highEnergyUsage;

  /// No description provided for @mainDoorUnlocked.
  ///
  /// In en, this message translates to:
  /// **'Main Door Unlocked'**
  String get mainDoorUnlocked;

  /// No description provided for @systemUpdateCompleted.
  ///
  /// In en, this message translates to:
  /// **'System Update Completed'**
  String get systemUpdateCompleted;

  /// No description provided for @justNow.
  ///
  /// In en, this message translates to:
  /// **'Just now'**
  String get justNow;

  /// No description provided for @minsAgo.
  ///
  /// In en, this message translates to:
  /// **'10 mins ago'**
  String get minsAgo;

  /// No description provided for @hoursAgo.
  ///
  /// In en, this message translates to:
  /// **'2 hours ago'**
  String get hoursAgo;

  /// No description provided for @cameraEvents.
  ///
  /// In en, this message translates to:
  /// **'Camera Events'**
  String get cameraEvents;

  /// No description provided for @noCameraEvents.
  ///
  /// In en, this message translates to:
  /// **'No camera events currently'**
  String get noCameraEvents;

  /// No description provided for @frontDoorCamera.
  ///
  /// In en, this message translates to:
  /// **'Front Door Camera'**
  String get frontDoorCamera;

  /// No description provided for @garageCamera.
  ///
  /// In en, this message translates to:
  /// **'Garage Camera'**
  String get garageCamera;

  /// No description provided for @backyardCamera.
  ///
  /// In en, this message translates to:
  /// **'Backyard Camera'**
  String get backyardCamera;

  /// No description provided for @motionDetected.
  ///
  /// In en, this message translates to:
  /// **'Motion Detected'**
  String get motionDetected;

  /// No description provided for @personDetected.
  ///
  /// In en, this message translates to:
  /// **'Person Detected'**
  String get personDetected;

  /// No description provided for @noMotion.
  ///
  /// In en, this message translates to:
  /// **'No Motion'**
  String get noMotion;

  /// No description provided for @live.
  ///
  /// In en, this message translates to:
  /// **'Live'**
  String get live;

  /// No description provided for @recording.
  ///
  /// In en, this message translates to:
  /// **'Recording'**
  String get recording;

  /// No description provided for @viewRecordings.
  ///
  /// In en, this message translates to:
  /// **'View Recordings'**
  String get viewRecordings;

  /// No description provided for @accessLog.
  ///
  /// In en, this message translates to:
  /// **'Access Log'**
  String get accessLog;

  /// No description provided for @noAccessLogs.
  ///
  /// In en, this message translates to:
  /// **'No access logs yet'**
  String get noAccessLogs;

  /// No description provided for @accessGranted.
  ///
  /// In en, this message translates to:
  /// **'Access Granted'**
  String get accessGranted;

  /// No description provided for @accessDenied.
  ///
  /// In en, this message translates to:
  /// **'Access Denied'**
  String get accessDenied;

  /// No description provided for @aiRecognition.
  ///
  /// In en, this message translates to:
  /// **'AI Recognition'**
  String get aiRecognition;

  /// No description provided for @manualApp.
  ///
  /// In en, this message translates to:
  /// **'Manual (App)'**
  String get manualApp;

  /// No description provided for @unknownPerson.
  ///
  /// In en, this message translates to:
  /// **'Unknown Person'**
  String get unknownPerson;

  /// No description provided for @energyReports.
  ///
  /// In en, this message translates to:
  /// **'Energy Reports'**
  String get energyReports;

  /// No description provided for @daily.
  ///
  /// In en, this message translates to:
  /// **'Daily'**
  String get daily;

  /// No description provided for @weekly.
  ///
  /// In en, this message translates to:
  /// **'Weekly'**
  String get weekly;

  /// No description provided for @monthly.
  ///
  /// In en, this message translates to:
  /// **'Monthly'**
  String get monthly;

  /// No description provided for @totalConsumption.
  ///
  /// In en, this message translates to:
  /// **'Total Consumption'**
  String get totalConsumption;

  /// No description provided for @averageUsage.
  ///
  /// In en, this message translates to:
  /// **'Average Usage'**
  String get averageUsage;

  /// No description provided for @peakUsage.
  ///
  /// In en, this message translates to:
  /// **'Peak Usage'**
  String get peakUsage;

  /// No description provided for @kWh.
  ///
  /// In en, this message translates to:
  /// **'kWh'**
  String get kWh;

  /// No description provided for @predictions.
  ///
  /// In en, this message translates to:
  /// **'Predictions'**
  String get predictions;

  /// No description provided for @predictedUsage.
  ///
  /// In en, this message translates to:
  /// **'Predicted Usage'**
  String get predictedUsage;

  /// No description provided for @nextDay.
  ///
  /// In en, this message translates to:
  /// **'Next Day'**
  String get nextDay;

  /// No description provided for @nextWeek.
  ///
  /// In en, this message translates to:
  /// **'Next Week'**
  String get nextWeek;

  /// No description provided for @nextMonth.
  ///
  /// In en, this message translates to:
  /// **'Next Month'**
  String get nextMonth;

  /// No description provided for @basedOnHistory.
  ///
  /// In en, this message translates to:
  /// **'Based on historical data'**
  String get basedOnHistory;

  /// No description provided for @voltage.
  ///
  /// In en, this message translates to:
  /// **'Voltage'**
  String get voltage;

  /// No description provided for @current.
  ///
  /// In en, this message translates to:
  /// **'Current'**
  String get current;

  /// No description provided for @power.
  ///
  /// In en, this message translates to:
  /// **'Power'**
  String get power;

  /// No description provided for @realTimeReadings.
  ///
  /// In en, this message translates to:
  /// **'Real-Time Readings'**
  String get realTimeReadings;

  /// No description provided for @volts.
  ///
  /// In en, this message translates to:
  /// **'V'**
  String get volts;

  /// No description provided for @amps.
  ///
  /// In en, this message translates to:
  /// **'A'**
  String get amps;

  /// No description provided for @watts.
  ///
  /// In en, this message translates to:
  /// **'W'**
  String get watts;

  /// No description provided for @alertTypeUnknownFace.
  ///
  /// In en, this message translates to:
  /// **'Unknown Face'**
  String get alertTypeUnknownFace;

  /// No description provided for @alertTypeHighEnergy.
  ///
  /// In en, this message translates to:
  /// **'High Energy Usage'**
  String get alertTypeHighEnergy;

  /// No description provided for @resolve.
  ///
  /// In en, this message translates to:
  /// **'Resolve'**
  String get resolve;

  /// No description provided for @resolved.
  ///
  /// In en, this message translates to:
  /// **'Resolved'**
  String get resolved;

  /// No description provided for @activeAlert.
  ///
  /// In en, this message translates to:
  /// **'Active'**
  String get activeAlert;

  /// No description provided for @comparedToPrevious.
  ///
  /// In en, this message translates to:
  /// **'Compared to previous period'**
  String get comparedToPrevious;

  /// No description provided for @higherThanAverage.
  ///
  /// In en, this message translates to:
  /// **'higher than average'**
  String get higherThanAverage;

  /// No description provided for @faceDetected.
  ///
  /// In en, this message translates to:
  /// **'Face Detected'**
  String get faceDetected;

  /// No description provided for @unknownFaceDetected.
  ///
  /// In en, this message translates to:
  /// **'Unknown Face Detected'**
  String get unknownFaceDetected;

  /// No description provided for @registeredFace.
  ///
  /// In en, this message translates to:
  /// **'Registered Face'**
  String get registeredFace;

  /// No description provided for @detectionTime.
  ///
  /// In en, this message translates to:
  /// **'Detection Time'**
  String get detectionTime;

  /// No description provided for @faceEvents.
  ///
  /// In en, this message translates to:
  /// **'Face Events'**
  String get faceEvents;

  /// No description provided for @login.
  ///
  /// In en, this message translates to:
  /// **'Login'**
  String get login;

  /// No description provided for @username.
  ///
  /// In en, this message translates to:
  /// **'Username'**
  String get username;

  /// No description provided for @password.
  ///
  /// In en, this message translates to:
  /// **'Password'**
  String get password;

  /// No description provided for @loginButton.
  ///
  /// In en, this message translates to:
  /// **'Sign In'**
  String get loginButton;

  /// No description provided for @loginError.
  ///
  /// In en, this message translates to:
  /// **'Invalid username or password'**
  String get loginError;

  /// No description provided for @admin.
  ///
  /// In en, this message translates to:
  /// **'Admin'**
  String get admin;

  /// No description provided for @user.
  ///
  /// In en, this message translates to:
  /// **'User'**
  String get user;

  /// No description provided for @role.
  ///
  /// In en, this message translates to:
  /// **'Role'**
  String get role;

  /// No description provided for @logout.
  ///
  /// In en, this message translates to:
  /// **'Logout'**
  String get logout;

  /// No description provided for @userManagement.
  ///
  /// In en, this message translates to:
  /// **'User Management'**
  String get userManagement;

  /// No description provided for @manualUnlock.
  ///
  /// In en, this message translates to:
  /// **'Manual Unlock'**
  String get manualUnlock;

  /// No description provided for @enterPin.
  ///
  /// In en, this message translates to:
  /// **'Enter PIN Code'**
  String get enterPin;

  /// No description provided for @pinCode.
  ///
  /// In en, this message translates to:
  /// **'PIN Code'**
  String get pinCode;

  /// No description provided for @unlock.
  ///
  /// In en, this message translates to:
  /// **'Unlock'**
  String get unlock;

  /// No description provided for @cancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// No description provided for @pinError.
  ///
  /// In en, this message translates to:
  /// **'Incorrect PIN code'**
  String get pinError;

  /// No description provided for @doorUnlockedManually.
  ///
  /// In en, this message translates to:
  /// **'Door unlocked manually'**
  String get doorUnlockedManually;

  /// No description provided for @biometricAuth.
  ///
  /// In en, this message translates to:
  /// **'Biometric Authentication'**
  String get biometricAuth;

  /// No description provided for @signInFirstLogin.
  ///
  /// In en, this message translates to:
  /// **'Sign in (First login)'**
  String get signInFirstLogin;

  /// No description provided for @usernameOrEmail.
  ///
  /// In en, this message translates to:
  /// **'User name Or Email'**
  String get usernameOrEmail;

  /// No description provided for @homeCode.
  ///
  /// In en, this message translates to:
  /// **'Home Code'**
  String get homeCode;

  /// No description provided for @userPinOrPassword.
  ///
  /// In en, this message translates to:
  /// **'User PIN / User Password'**
  String get userPinOrPassword;

  /// No description provided for @enterAsUser.
  ///
  /// In en, this message translates to:
  /// **'Enter as A User'**
  String get enterAsUser;

  /// No description provided for @deviceOffline.
  ///
  /// In en, this message translates to:
  /// **'Device Offline'**
  String get deviceOffline;

  /// No description provided for @pendingDecision.
  ///
  /// In en, this message translates to:
  /// **'Pending Decision'**
  String get pendingDecision;

  /// No description provided for @cameraLabel.
  ///
  /// In en, this message translates to:
  /// **'Camera'**
  String get cameraLabel;

  /// No description provided for @statusLabel.
  ///
  /// In en, this message translates to:
  /// **'Status'**
  String get statusLabel;

  /// No description provided for @openAction.
  ///
  /// In en, this message translates to:
  /// **'Open'**
  String get openAction;

  /// No description provided for @denyAction.
  ///
  /// In en, this message translates to:
  /// **'Deny'**
  String get denyAction;

  /// No description provided for @addToFamily.
  ///
  /// In en, this message translates to:
  /// **'Add to Family'**
  String get addToFamily;

  /// No description provided for @securityAlerts.
  ///
  /// In en, this message translates to:
  /// **'Security'**
  String get securityAlerts;

  /// No description provided for @security.
  ///
  /// In en, this message translates to:
  /// **'Security'**
  String get security;

  /// No description provided for @systemAlerts.
  ///
  /// In en, this message translates to:
  /// **'System'**
  String get systemAlerts;

  /// No description provided for @allAlerts.
  ///
  /// In en, this message translates to:
  /// **'All'**
  String get allAlerts;

  /// No description provided for @account.
  ///
  /// In en, this message translates to:
  /// **'Account'**
  String get account;

  /// No description provided for @adminName.
  ///
  /// In en, this message translates to:
  /// **'Admin Name'**
  String get adminName;

  /// No description provided for @changePassword.
  ///
  /// In en, this message translates to:
  /// **'Change Password'**
  String get changePassword;

  /// No description provided for @appLock.
  ///
  /// In en, this message translates to:
  /// **'App Lock'**
  String get appLock;

  /// No description provided for @localNetwork.
  ///
  /// In en, this message translates to:
  /// **'Local Network'**
  String get localNetwork;

  /// No description provided for @serverIp.
  ///
  /// In en, this message translates to:
  /// **'Server IP'**
  String get serverIp;

  /// No description provided for @cameraStreamUrl.
  ///
  /// In en, this message translates to:
  /// **'Camera Stream URL'**
  String get cameraStreamUrl;

  /// No description provided for @homeCodeLabel.
  ///
  /// In en, this message translates to:
  /// **'Home Code / ESP32'**
  String get homeCodeLabel;

  /// No description provided for @testConnection.
  ///
  /// In en, this message translates to:
  /// **'Test Connection'**
  String get testConnection;

  /// No description provided for @saveSettings.
  ///
  /// In en, this message translates to:
  /// **'Save Settings'**
  String get saveSettings;

  /// No description provided for @resetDefaults.
  ///
  /// In en, this message translates to:
  /// **'Reset Defaults'**
  String get resetDefaults;

  /// No description provided for @connectionSuccess.
  ///
  /// In en, this message translates to:
  /// **'Connection Successful'**
  String get connectionSuccess;

  /// No description provided for @connectionFailed.
  ///
  /// In en, this message translates to:
  /// **'Connection Failed'**
  String get connectionFailed;

  /// No description provided for @copiedToClipboard.
  ///
  /// In en, this message translates to:
  /// **'Copied to clipboard'**
  String get copiedToClipboard;

  /// No description provided for @appearance.
  ///
  /// In en, this message translates to:
  /// **'Appearance'**
  String get appearance;

  /// No description provided for @family.
  ///
  /// In en, this message translates to:
  /// **'Family'**
  String get family;

  /// No description provided for @addMember.
  ///
  /// In en, this message translates to:
  /// **'Add Member'**
  String get addMember;

  /// No description provided for @deleteMember.
  ///
  /// In en, this message translates to:
  /// **'Delete Member'**
  String get deleteMember;

  /// No description provided for @faceEnrolled.
  ///
  /// In en, this message translates to:
  /// **'Face Enrolled'**
  String get faceEnrolled;

  /// No description provided for @noFace.
  ///
  /// In en, this message translates to:
  /// **'No Face'**
  String get noFace;

  /// No description provided for @enrollFace.
  ///
  /// In en, this message translates to:
  /// **'Enroll Face'**
  String get enrollFace;

  /// No description provided for @captureFromCamera.
  ///
  /// In en, this message translates to:
  /// **'Capture from Camera'**
  String get captureFromCamera;

  /// No description provided for @pickFromGallery.
  ///
  /// In en, this message translates to:
  /// **'Pick from Gallery'**
  String get pickFromGallery;

  /// No description provided for @memberName.
  ///
  /// In en, this message translates to:
  /// **'Member Name'**
  String get memberName;

  /// No description provided for @memberRole.
  ///
  /// In en, this message translates to:
  /// **'Role'**
  String get memberRole;

  /// No description provided for @unknownFace.
  ///
  /// In en, this message translates to:
  /// **'Unknown Face'**
  String get unknownFace;

  /// No description provided for @delete.
  ///
  /// In en, this message translates to:
  /// **'Delete'**
  String get delete;

  /// No description provided for @saveMember.
  ///
  /// In en, this message translates to:
  /// **'Save Member'**
  String get saveMember;

  /// No description provided for @removeMemberPrompt.
  ///
  /// In en, this message translates to:
  /// **'Are you sure you want to remove {name}?'**
  String removeMemberPrompt(String name);

  /// No description provided for @systemSecure.
  ///
  /// In en, this message translates to:
  /// **'SYSTEM SECURE & ONLINE'**
  String get systemSecure;

  /// No description provided for @frontDoor.
  ///
  /// In en, this message translates to:
  /// **'Front Door'**
  String get frontDoor;

  /// No description provided for @livingRoomSensor.
  ///
  /// In en, this message translates to:
  /// **'Living Room Sensor'**
  String get livingRoomSensor;

  /// No description provided for @permissionDenied.
  ///
  /// In en, this message translates to:
  /// **'Permission Denied'**
  String get permissionDenied;

  /// No description provided for @permissionDeniedPermanently.
  ///
  /// In en, this message translates to:
  /// **'Permission denied permanently. Please enable it in settings.'**
  String get permissionDeniedPermanently;

  /// No description provided for @openSettings.
  ///
  /// In en, this message translates to:
  /// **'Open Settings'**
  String get openSettings;

  /// No description provided for @retry.
  ///
  /// In en, this message translates to:
  /// **'Retry'**
  String get retry;

  /// No description provided for @edit.
  ///
  /// In en, this message translates to:
  /// **'Edit'**
  String get edit;

  /// No description provided for @smartHome.
  ///
  /// In en, this message translates to:
  /// **'Smart Home'**
  String get smartHome;

  /// No description provided for @appTagline.
  ///
  /// In en, this message translates to:
  /// **'Secure • Connected • Intelligent'**
  String get appTagline;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['ar', 'en'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'ar':
      return AppLocalizationsAr();
    case 'en':
      return AppLocalizationsEn();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
