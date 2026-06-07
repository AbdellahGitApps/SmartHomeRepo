import os
import re

def append_missing_i18n():
    js_path = "e:/SmartHomeMobileApp/edge/dashboard/static/js/i18n.js"
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_en_keys = {
        "loading": "Loading...",
        "loading_users": "Loading users...",
        "no_users": "No users found.",
        "never_logged_in": "Not logged in yet",
        "edit_sysowner": "Edit System Owner",
        "no_energy_devices": "No energy devices registered yet.",
        "loading_energy": "Loading energy devices...",
        "failed_energy": "Failed to load energy data.",
        "no_home_devices": "No devices registered for this home.",
        "all_dates": "All Dates",
        "no_logs_found": "No logs found for the selected criteria.",
        "loading_logs": "Loading logs...",
        "delete_filtered": "Delete Filtered",
        "loading_status": "Loading status...",
        "loading_overview": "Loading overview data...",
        "users_management_desc": "Manage System Owner and registered home owner accounts"
    }

    new_ar_keys = {
        "loading": "جاري التحميل...",
        "loading_users": "جاري تحميل المستخدمين...",
        "no_users": "لم يتم العثور على مستخدمين.",
        "never_logged_in": "لم يسجل الدخول بعد",
        "edit_sysowner": "تعديل مالك النظام",
        "no_energy_devices": "لا توجد أجهزة طاقة مسجلة بعد.",
        "loading_energy": "جاري تحميل أجهزة الطاقة...",
        "failed_energy": "فشل تحميل بيانات الطاقة.",
        "no_home_devices": "لم يتم تسجيل أجهزة لهذا المنزل.",
        "all_dates": "جميع التواريخ",
        "no_logs_found": "لم يتم العثور على سجلات تطابق البحث.",
        "loading_logs": "جاري تحميل السجلات...",
        "delete_filtered": "حذف المصفاة",
        "loading_status": "جاري تحميل الحالة...",
        "loading_overview": "جاري تحميل البيانات العامة...",
        "users_management_desc": "إدارة مسؤولي النظام وأصحاب المنازل"
    }

    # Inject into the 'en: {' block
    # We find 'en: {' and inject after the first '{'
    en_insert = ""
    for k, v in new_en_keys.items():
        if f'"{k}":' not in content:
            en_insert += f'    "{k}": "{v}",\n'
            
    ar_insert = ""
    for k, v in new_ar_keys.items():
        if f'"{k}":' not in content:
            ar_insert += f'    "{k}": "{v}",\n'

    # Replace en: {
    content = re.sub(r'en:\s*\{', 'en: {\n' + en_insert, content)
    # Replace ar: {
    content = re.sub(r'ar:\s*\{', 'ar: {\n' + ar_insert, content)

    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Appended missing translations to i18n.js")

if __name__ == "__main__":
    append_missing_i18n()
