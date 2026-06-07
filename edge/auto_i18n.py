import os
import re
import json

def load_en_dict():
    js_path = "e:/SmartHomeMobileApp/edge/dashboard/static/js/i18n.js"
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract the 'en:' block
    en_block_match = re.search(r'en:\s*\{([\s\S]*?)\},\s*ar:', content)
    if not en_block_match:
        return {}
    
    en_block = en_block_match.group(1)
    
    mapping = {}
    for line in en_block.split('\n'):
        line = line.strip()
        if not line or line.startswith('//'): continue
        match = re.search(r'"([^"]+)":\s*"([^"]+)"', line)
        if match:
            key, val = match.groups()
            mapping[val.strip()] = key
    return mapping

def auto_i18n():
    mapping = load_en_dict()
    # Sort mapping by length of value (longest first) to avoid partial matches
    sorted_items = sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True)
    
    templates_dir = "e:/SmartHomeMobileApp/edge/dashboard/templates"
    for filename in os.listdir(templates_dir):
        if not filename.endswith('.html'): continue
        filepath = os.path.join(templates_dir, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            html = f.read()
            
        changed = False
        
        # We need to find text between > and <
        # e.g., >Dashboard< -> ><span data-i18n="nav_dashboard">Dashboard</span><
        # Better yet, if it's already inside a tag like <h1 class="...">Dashboard</h1>, we just add data-i18n
        
        for val, key in sorted_items:
            # Skip very short or generic strings that might false positive
            if len(val) < 2 or val in ["--", "Ok", "Yes", "No"]: continue
            
            # 1. Look for exact tag content: <tag>val</tag> -> <tag data-i18n="key">val</tag>
            # Use a regex that finds tags containing EXACTLY 'val' (ignoring whitespace padding)
            pattern = r'(<([a-zA-Z0-9]+)([^>]*)>)\s*(' + re.escape(val) + r')\s*(<\/\2>)'
            def replacer1(m):
                tag_open = m.group(1)
                tag_name = m.group(2)
                attrs = m.group(3)
                text = m.group(4)
                tag_close = m.group(5)
                
                if 'data-i18n=' in tag_open:
                    return m.group(0)
                
                return f'<{tag_name}{attrs} data-i18n="{key}">{text}{tag_close}'
                
            new_html, count = re.subn(pattern, replacer1, html, flags=re.IGNORECASE)
            if count > 0:
                html = new_html
                changed = True

            # 2. Look for placeholders: placeholder="val" -> placeholder="val" data-i18n-placeholder="key"
            pattern2 = r'(<input[^>]+)placeholder="(' + re.escape(val) + r')([^"]*)"([^>]*)>'
            def replacer2(m):
                if 'data-i18n-placeholder=' in m.group(0):
                    return m.group(0)
                return f'{m.group(1)}placeholder="{m.group(2)}{m.group(3)}" data-i18n-placeholder="{key}"{m.group(4)}>'
            
            new_html2, count2 = re.subn(pattern2, replacer2, html, flags=re.IGNORECASE)
            if count2 > 0:
                html = new_html2
                changed = True
                
            # 3. Look for plain text nodes that are just text between tags, e.g. <td>val</td>
            # Already handled by #1 mostly.
            
            # 4. Text with icons: > <i class="..."></i> val <
            pattern3 = r'(<([a-zA-Z0-9]+)([^>]*)>)\s*(<i[^>]+><\/i>)\s*(' + re.escape(val) + r')\s*(<\/\2>)'
            def replacer3(m):
                tag_open = m.group(1)
                tag_name = m.group(2)
                attrs = m.group(3)
                icon = m.group(4)
                text = m.group(5)
                tag_close = m.group(6)
                if 'data-i18n=' in tag_open:
                    return m.group(0)
                return f'<{tag_name}{attrs} data-i18n="{key}">{icon} {text}{tag_close}'
            
            new_html3, count3 = re.subn(pattern3, replacer3, html, flags=re.IGNORECASE)
            if count3 > 0:
                html = new_html3
                changed = True
                
        if changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"Updated {filename}")

if __name__ == '__main__':
    auto_i18n()
