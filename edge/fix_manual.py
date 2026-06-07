import os
import re

def fix_js_translations():
    templates_dir = "e:/SmartHomeMobileApp/edge/dashboard/templates"
    
    # In users.html, fix the dynamic rendering
    users_html = os.path.join(templates_dir, "users.html")
    with open(users_html, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Fix the subtitle
    html = html.replace('<div class="page-subtitle">Manage System Owner and registered home owner accounts</div>',
                        '<div class="page-subtitle" data-i18n="users_management_desc">Manage System Owneristrators and home owners</div>')
    
    # Fix "+ Add User"
    html = html.replace('<button class="primary-btn" onclick="showDeferred()">+ Add User</button>',
                        '<button class="primary-btn" onclick="showDeferred()"><i class="ph ph-plus"></i> <span data-i18n="add_user">Add User</span></button>')

    # In users.html, JS: `${statusText}` -> `${window.d7T(active ? "status_active" : "status_disabled", statusText)}`
    # Also Loading users...
    html = html.replace('Loading users...', '<span data-i18n="loading">Loading users...</span>')
    html = html.replace('No users found.', '<span data-i18n="no_users">No users found.</span>')
    html = html.replace('Not logged in yet', '<span data-i18n="never_logged_in">Not logged in yet</span>')
    html = html.replace('Edit System Owner', '<span data-i18n="edit_sysowner">Edit System Owner</span>')
    
    with open(users_html, 'w', encoding='utf-8') as f:
        f.write(html)
        
    print("Fixed users.html")

if __name__ == '__main__':
    fix_js_translations()
