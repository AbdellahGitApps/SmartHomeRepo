import os
import re

def auto_js_i18n():
    js_path = "e:/SmartHomeMobileApp/edge/dashboard/static/js/i18n.js"
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    en_block_match = re.search(r'en:\s*\{([\s\S]*?)\},\s*ar:', content)
    en_block = en_block_match.group(1)
    
    mapping = {}
    for line in en_block.split('\n'):
        line = line.strip()
        if not line or line.startswith('//'): continue
        match = re.search(r'"([^"]+)":\s*"([^"]+)"', line)
        if match:
            key, val = match.groups()
            mapping[val.strip()] = key

    # Sort mapping by length of value (longest first)
    sorted_items = sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True)
    
    templates_dir = "e:/SmartHomeMobileApp/edge/dashboard/templates"
    for filename in os.listdir(templates_dir):
        if not filename.endswith('.html'): continue
        filepath = os.path.join(templates_dir, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            html = f.read()
            
        changed = False
        
        # We find inside backticks or quotes, but only if they are text
        # Since doing this automatically in JS strings is risky (we might break syntax),
        # we only replace known exact matches that are plain text (no variables)
        
        for val, key in sorted_items:
            if len(val) < 4: continue
            
            # Find literal `val` not preceded by data-i18n=
            # and replace it with `<span data-i18n="key">val</span>`
            # BUT only if it is preceded by > or " or ` or >\s*
            # Actually, doing `html.replace(val, f'<span data-i18n="{key}">{val}</span>')` 
            # might corrupt things like `title="val"` or `class="val"`.
            # We already did HTML tags. Let's look specifically for `>val<` inside JS strings
            
            pattern = r'>\s*(' + re.escape(val) + r')\s*<'
            def replacer(m):
                # if already has data-i18n, skip
                return f'><span data-i18n="{key}">{m.group(1)}</span><'
                
            # Replace only in `<script>` blocks
            script_blocks = re.split(r'(<script[\s\S]*?<\/script>)', html, flags=re.IGNORECASE)
            
            new_script_blocks = []
            for i, block in enumerate(script_blocks):
                if block.lower().startswith('<script'):
                    # inside JS
                    new_block, count = re.subn(pattern, replacer, block)
                    if count > 0:
                        block = new_block
                        changed = True
                new_script_blocks.append(block)
            
            html = ''.join(new_script_blocks)
            
        if changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"Updated JS in {filename}")

if __name__ == '__main__':
    auto_js_i18n()
