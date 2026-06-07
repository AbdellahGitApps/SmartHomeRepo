import re

def refactor():
    with open('e:/SmartHomeMobileApp/edge/dashboard/templates/devices.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Remove all existing script blocks
    clean_html = re.sub(r'<script.*?>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Clean up empty lines left behind
    clean_html = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean_html)

    # Define the new consolidated, optimized JS
    new_js = """
<script>
document.addEventListener("DOMContentLoaded", function() {

    // --- 1. CORE TOAST SYSTEM ---
    window.toast = function(msg, type = "success") {
        const t = document.createElement("div");
        t.className = `toast toast-${type}`;
        t.style.position = "fixed";
        t.style.bottom = "20px";
        t.style.right = "20px";
        t.style.padding = "14px 24px";
        t.style.borderRadius = "12px";
        t.style.background = type === "success" ? "rgba(16, 185, 129, 0.95)" : "rgba(239, 68, 68, 0.95)";
        t.style.color = "#fff";
        t.style.fontWeight = "600";
        t.style.zIndex = "999999";
        t.style.boxShadow = "0 10px 25px rgba(0,0,0,0.3)";
        t.style.opacity = "0";
        t.style.transform = "translateY(20px)";
        t.style.transition = "all 0.3s ease";
        t.innerText = window.d7T ? window.d7T(msg, msg) : msg;
        document.body.appendChild(t);

        requestAnimationFrame(() => {
            t.style.opacity = "1";
            t.style.transform = "translateY(0)";
        });

        setTimeout(() => {
            t.style.opacity = "0";
            t.style.transform = "translateY(20px)";
            setTimeout(() => t.remove(), 300);
        }, 3000);
    };

    window.showToast = window.toast;
    window.showBlueToast = (msg) => window.toast(msg, "success");

    // --- 2. ADVANCED INFO TOGGLE ---
    window.toggleAdvancedInfo = function(deviceId) {
        const row = document.getElementById(`adv-${deviceId}`);
        if (!row) return;
        const isHidden = row.style.display === "none";
        row.style.display = isHidden ? "table-row" : "none";
    };

    // --- 3. DOM UPDATE UTILS (No Reloads) ---
    function updateRowStatus(deviceId, isOnline) {
        const row = document.querySelector(`tr[data-device-id="${deviceId}"]`) || document.getElementById(`row-${deviceId}`);
        if (!row) return;
        const statusSpan = row.querySelector('.device-status-badge') || row.querySelector('.phase10-status-badge');
        if (statusSpan) {
            statusSpan.className = isOnline ? "phase10-status-badge phase10-online" : "phase10-status-badge phase10-offline";
            statusSpan.setAttribute("data-i18n", isOnline ? "status_online" : "badge_offline");
            statusSpan.innerText = isOnline ? "Online" : "Offline";
            if (window.translatePage) window.translatePage();
        }
    }

    function updateRowEnabled(deviceId, isEnabled) {
        const row = document.querySelector(`tr[data-device-id="${deviceId}"]`) || document.getElementById(`row-${deviceId}`);
        if (!row) return;
        
        // Update enabled badge
        const enabledSpan = row.querySelector('.phase10-enabled-badge');
        if (enabledSpan) {
            enabledSpan.className = isEnabled ? "phase10-enabled-badge phase10-enabled" : "phase10-enabled-badge phase10-disabled";
            enabledSpan.setAttribute("data-i18n", isEnabled ? "btn_enable" : "btn_disable");
            enabledSpan.innerText = isEnabled ? "ENABLED" : "DISABLED";
        }

        // Toggle buttons visibility
        const playBtn = row.querySelector('.ph-play');
        const pauseBtn = row.querySelector('.ph-pause');
        if (playBtn && pauseBtn) {
            if (isEnabled) {
                playBtn.parentElement.style.display = 'none';
                pauseBtn.parentElement.style.display = 'inline-block';
            } else {
                playBtn.parentElement.style.display = 'inline-block';
                pauseBtn.parentElement.style.display = 'none';
            }
        }
        if (window.translatePage) window.translatePage();
    }

    function removeRow(deviceId) {
        const row = document.querySelector(`tr[data-device-id="${deviceId}"]`) || document.getElementById(`row-${deviceId}`);
        const advRow = document.getElementById(`adv-${deviceId}`);
        if (row) row.remove();
        if (advRow) advRow.remove();
    }

    // --- 4. DEVICE ACTION PIPELINE ---
    async function executeDeviceAction(deviceId, action, rowElement = null) {
        try {
            // Add loading state
            if (rowElement) rowElement.style.opacity = '0.5';

            const res = await fetch(`/api/dashboard/devices/${encodeURIComponent(deviceId)}/actions/${encodeURIComponent(action)}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });

            if (rowElement) rowElement.style.opacity = '1';

            const data = await res.json();
            if (data.ok || data.status === "success") {
                toast(`Command '${action}' executed successfully.`);
                
                // Perform local DOM updates
                if (action === "restart") updateRowStatus(deviceId, false); // Temporarily show offline
                if (action === "enable") updateRowEnabled(deviceId, true);
                if (action === "disable") updateRowEnabled(deviceId, false);
                if (action === "remove") removeRow(deviceId);
            } else {
                toast(data.message || data.error || "Failed to execute command", "error");
            }
        } catch (err) {
            if (rowElement) rowElement.style.opacity = '1';
            toast("Network error occurred", "error");
        }
    }

    // --- 5. EXPORTED HANDLERS ---
    window.restartDevice = function(btn) {
        const row = btn.closest("tr");
        const deviceId = row.dataset.deviceId || row.id.replace('row-', '');
        if (!deviceId) return;

        if (window.DashboardConfirm) {
            DashboardConfirm.show("Restart Device", "Are you sure you want to reboot this device?", "Restart", "danger", () => {
                executeDeviceAction(deviceId, "restart", row);
            });
        } else {
            if (confirm("Restart Device?")) executeDeviceAction(deviceId, "restart", row);
        }
    };

    window.mockRemoveDevice = function(btn) {
        const row = btn.closest("tr");
        const deviceId = row.dataset.deviceId || row.id.replace('row-', '');
        if (!deviceId) return;

        if (window.DashboardConfirm) {
            DashboardConfirm.show("Remove Device", "Are you sure you want to permanently remove this device?", "Remove", "danger", () => {
                executeDeviceAction(deviceId, "remove", row);
            });
        } else {
            if (confirm("Remove Device?")) executeDeviceAction(deviceId, "remove", row);
        }
    };

    window.mockToggleDeviceStatus = function(btn) {
        const row = btn.closest("tr");
        const deviceId = row.dataset.deviceId || row.id.replace('row-', '');
        if (!deviceId) return;
        
        // Determine action based on current state
        const pauseBtn = row.querySelector('.ph-pause');
        const isCurrentlyEnabled = pauseBtn && pauseBtn.parentElement.style.display !== 'none';
        const action = isCurrentlyEnabled ? "disable" : "enable";

        executeDeviceAction(deviceId, action, row);
    };

    window.enableDevice = function(deviceId) {
        executeDeviceAction(deviceId, "enable", null);
    };

    window.disableDevice = function(deviceId) {
        executeDeviceAction(deviceId, "disable", null);
    };

    // --- 6. DATE/TIME FORMATTER (No Observers) ---
    function formatDateTime(datePart, hourPart, minutePart, secondPart, suffixPart) {
        let hour = parseInt(hourPart, 10);
        const minute = String(minutePart || "00").padStart(2, '0');
        const second = String(secondPart || "00").padStart(2, '0');
        let suffix = suffixPart ? suffixPart.toUpperCase() : (hour >= 12 ? "PM" : "AM");
        if (hour > 12) hour -= 12;
        if (hour === 0) hour = 12;
        return `${datePart}, ${String(hour).padStart(2, '0')}:${minute}:${second} ${suffix}`;
    }

    document.querySelectorAll("td, span, small, .last-seen, [data-last-seen]").forEach(function(el) {
        const text = el.textContent || "";
        const compact = text.replace(/\s+/g, " ").trim();
        if (/^(\d{4}-\d{2}-\d{2})\s*,?\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM)?/i.test(compact)) {
            const fixed = compact.replace(
                /(\d{4}-\d{2}-\d{2})\s*,?\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*(AM|PM)?/gi,
                function(_, d, h, m, s, suf) { return formatDateTime(d, h, m, s, suf); }
            );
            el.textContent = fixed;
        }
    });

    // --- 7. TRANSLATION DICTIONARY INJECTIONS ---
    if (typeof translations !== 'undefined') {
        translations.en["no_devices_msg"] = "No devices registered yet.";
        translations.ar["no_devices_msg"] = "لا توجد أجهزة مسجلة بعد.";
        translations.en["add_first_device_desc"] = "Get started by provisioning devices when creating a home.";
        translations.ar["add_first_device_desc"] = "ابدأ بتهيئة الأجهزة عند إنشاء منزل.";
    }

});
</script>
"""

    with open('e:/SmartHomeMobileApp/edge/dashboard/templates/devices.html', 'w', encoding='utf-8') as f:
        f.write(clean_html.strip() + '\n' + new_js)

if __name__ == '__main__':
    refactor()
