import os

def inject_missing():
    templates_dir = "e:/SmartHomeMobileApp/edge/dashboard/templates"
    
    replacements = [
        ('Loading users...', '<span data-i18n="loading_users">Loading users...</span>'),
        ('No users found.', '<span data-i18n="no_users">No users found.</span>'),
        ('Not logged in yet', '<span data-i18n="never_logged_in">Not logged in yet</span>'),
        ('Edit System Owner', '<span data-i18n="edit_sysowner">Edit System Owner</span>'),
        ('No energy devices registered yet.', '<span data-i18n="no_energy_devices">No energy devices registered yet.</span>'),
        ('Loading energy devices...', '<span data-i18n="loading_energy">Loading energy devices...</span>'),
        ('Failed to load energy data.', '<span data-i18n="failed_energy">Failed to load energy data.</span>'),
        ('No devices registered for this home.', '<span data-i18n="no_home_devices">No devices registered for this home.</span>'),
        ('All Dates', '<span data-i18n="all_dates">All Dates</span>'),
        ('No logs found for the selected criteria.', '<span data-i18n="no_logs_found">No logs found for the selected criteria.</span>'),
        ('Loading logs...', '<span data-i18n="loading_logs">Loading logs...</span>'),
        ('Delete Filtered', '<span data-i18n="delete_filtered">Delete Filtered</span>'),
        ('Loading status...', '<span data-i18n="loading_status">Loading status...</span>'),
        ('Loading overview data...', '<span data-i18n="loading_overview">Loading overview data...</span>'),
    ]

    for filename in os.listdir(templates_dir):
        if not filename.endswith('.html'): continue
        filepath = os.path.join(templates_dir, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            html = f.read()
            
        changed = False
        
        for old, new in replacements:
            # simple replace for any occurrences that are not already tagged
            if old in html and new not in html:
                html = html.replace(old, new)
                changed = True
                
        if changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"Injected missing into {filename}")

if __name__ == '__main__':
    inject_missing()
