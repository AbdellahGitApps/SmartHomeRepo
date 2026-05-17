document.addEventListener('DOMContentLoaded', () => {
    // Sidebar Toggle Logic
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }

    // Set active nav item based on current URL path
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        const href = item.getAttribute('href');
        if (currentPath === href || (currentPath === '/' && href === '/')) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Initialize Global State
    initTheme();
    initLanguage();
    initDeviceStatuses();
});

// --- Global Theme Logic ---
function initTheme() {
    let theme = localStorage.getItem('appTheme') || 'dark';
    applyTheme(theme);
}

window.toggleTheme = function() {
    let currentTheme = localStorage.getItem('appTheme') || 'dark';
    let newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('appTheme', newTheme);
    applyTheme(newTheme);
};

function applyTheme(theme) {
    const icon = document.getElementById('themeIcon');
    if (theme === 'light') {
        document.body.classList.add('theme-light');
        if (icon) icon.className = 'ph ph-moon';
    } else {
        document.body.classList.remove('theme-light');
        if (icon) icon.className = 'ph ph-sun';
    }
}

// --- Global Language Logic ---
function initLanguage() {
    let lang = localStorage.getItem('appLang') || 'en';
    applyLanguage(lang);
}

window.toggleLanguage = function() {
    let currentLang = localStorage.getItem('appLang') || 'en';
    let newLang = currentLang === 'en' ? 'ar' : 'en';
    localStorage.setItem('appLang', newLang);
    applyLanguage(newLang);
};

function applyLanguage(lang) {
    if (lang === 'ar') {
        document.body.setAttribute('dir', 'rtl');
    } else {
        document.body.removeAttribute('dir');
    }
    
    const langLabel = document.getElementById('langLabel');
    if (langLabel) {
        langLabel.textContent = lang === 'en' ? 'AR' : 'EN';
    }

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (window.getTranslation) {
            const newText = window.getTranslation(key);
            const icon = el.querySelector('i');
            if (icon) {
                el.innerHTML = '';
                el.appendChild(icon);
                el.appendChild(document.createTextNode(' ' + newText));
            } else {
                el.textContent = newText;
            }
        }
    });
}

// --- Device Mocking Logic ---
function initDeviceStatuses() {
    let statuses = JSON.parse(localStorage.getItem('deviceStatuses')) || {};
    document.querySelectorAll('.device-status-badge').forEach(badge => {
        let deviceId = badge.getAttribute('data-device-id');
        if (deviceId && statuses[deviceId]) {
            applyDeviceStatusUI(deviceId, statuses[deviceId]);
        }
    });
}

window.mockToggleDeviceStatus = function(deviceId) {
    let statuses = JSON.parse(localStorage.getItem('deviceStatuses')) || {};
    let currentStatus = statuses[deviceId] || 'Online';
    let newStatus = currentStatus === 'Online' ? 'Disabled' : 'Online';
    statuses[deviceId] = newStatus;
    localStorage.setItem('deviceStatuses', JSON.stringify(statuses));
    
    applyDeviceStatusUI(deviceId, newStatus);
    if (window.getTranslation) {
        let statusText = window.getTranslation(newStatus === 'Online' ? 'status_online' : 'status_disabled');
        showToast(`Device ${deviceId} -> ${statusText}`);
    } else {
        showToast(`Device ${deviceId} is now ${newStatus}`);
    }
};

window.mockRestartDevice = function(btnElement) {
    let msg = window.getTranslation ? window.getTranslation('msg_restart') : 'Restarting device...';
    showToast(msg);
    const icon = btnElement.querySelector('i');
    if (icon) {
        icon.classList.add('ph-spinner', 'ph-spin');
        icon.classList.remove('ph-power');
        setTimeout(() => {
            icon.classList.remove('ph-spinner', 'ph-spin');
            icon.classList.add('ph-power');
            let successMsg = window.getTranslation ? window.getTranslation('msg_restarted') : 'Device restarted successfully.';
            showToast(successMsg);
        }, 1500);
    }
};

window.mockRemoveDevice = function(btnElement) {
    let confirmMsg = window.getTranslation ? window.getTranslation('confirm_remove') : 'Are you sure you want to remove this device?';
    if (confirm(confirmMsg)) {
        const row = btnElement.closest('.device-row') || btnElement.closest('tr');
        if (row) {
            row.style.transition = 'opacity 0.3s ease';
            row.style.opacity = '0';
            setTimeout(() => {
                row.remove();
                let successMsg = window.getTranslation ? window.getTranslation('msg_removed') : 'Device removed from system.';
                showToast(successMsg);
            }, 300);
        }
    }
};

function applyDeviceStatusUI(deviceId, status) {
    document.querySelectorAll(`.device-status-badge[data-device-id="${deviceId}"]`).forEach(badge => {
        badge.style.transition = 'all 0.3s ease';
        let text = window.getTranslation ? window.getTranslation(status === 'Online' ? 'status_online' : 'status_disabled') : status;
        if (status === 'Online') {
            badge.className = 'badge badge-success device-status-badge';
            badge.textContent = text;
        } else {
            badge.className = 'badge badge-offline device-status-badge';
            badge.textContent = text;
        }
    });
    
    document.querySelectorAll(`.btn-toggle-status[data-device-id="${deviceId}"]`).forEach(btn => {
        if (status === 'Online') {
            btn.innerHTML = '<i class="ph ph-pause"></i>';
            btn.title = window.getTranslation ? window.getTranslation('btn_disable') : 'Disable Device';
        } else {
            btn.innerHTML = '<i class="ph ph-play"></i>';
            btn.title = window.getTranslation ? window.getTranslation('btn_enable') : 'Enable Device';
        }
    });
}

function showToast(message) {
    let toast = document.createElement('div');
    toast.textContent = message;
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.left = '50%';
    toast.style.transform = 'translateX(-50%) translateY(20px)';
    toast.style.opacity = '0';
    toast.style.background = 'var(--accent-primary)';
    toast.style.color = 'white';
    toast.style.padding = '12px 24px';
    toast.style.borderRadius = '8px';
    toast.style.zIndex = '9999';
    toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    toast.style.transition = 'all 0.3s ease';
    document.body.appendChild(toast);
    
    requestAnimationFrame(() => {
        toast.style.transform = 'translateX(-50%) translateY(0)';
        toast.style.opacity = '1';
    });
    
    setTimeout(() => { 
        toast.style.transform = 'translateX(-50%) translateY(20px)';
        toast.style.opacity = '0'; 
    }, 2500);
    setTimeout(() => { toast.remove(); }, 2800);
}
