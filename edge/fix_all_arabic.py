import os
import glob
import io

def fix_file(filepath):
    with io.open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # We want to find substrings that are pure mojibake. 
    # Usually they contain 'ظ' or 'ط'.
    import re
    # Match words containing these characters
    def replacer(match):
        s = match.group(0)
        try:
            # Only fix if it actually contains the mojibake chars
            if 'ظ' in s or 'ط' in s:
                return s.encode('cp1256').decode('utf-8')
        except:
            pass
        return s

    # Match anything between quotes or text nodes that might be arabic mojibake
    # Actually, let's just match any sequence of Arabic characters in the mojibake range
    # Windows-1256 Arabic chars are mostly in the \u0600-\u06FF range, same as real Arabic.
    # We can just split by lines and try to fix the whole line, if it fails we don't.
    # But a line might contain a real UTF-8 emoji that fails cp1256 encoding.
    
    # Better: find substrings between quotes
    new_content = []
    lines = content.split('\n')
    changed = False
    
    for line in lines:
        if 'ظ' in line or 'ط' in line:
            # Let's try to fix the whole line first
            try:
                fixed_line = line.encode('cp1256').decode('utf-8')
                new_content.append(fixed_line)
                changed = True
                continue
            except:
                pass
            
            # If whole line fails, try piece by piece (between quotes)
            def quote_replacer(m):
                try:
                    return '"' + m.group(1).encode('cp1256').decode('utf-8') + '"'
                except:
                    return m.group(0)
            
            fixed_line = re.sub(r'"([^"]*?[ظط][^"]*?)"', quote_replacer, line)
            if fixed_line != line:
                new_content.append(fixed_line)
                changed = True
                continue
                
        new_content.append(line)
        
    if changed:
        with io.open(filepath, "w", encoding="utf-8") as f:
            f.write('\n'.join(new_content))
        print("Fixed:", filepath)

if __name__ == "__main__":
    templates_dir = "e:/SmartHomeMobileApp/edge/dashboard/templates"
    for file in glob.glob(os.path.join(templates_dir, "*.html")):
        fix_file(file)
    
    static_js = "e:/SmartHomeMobileApp/edge/dashboard/static/js/i18n.js"
    if os.path.exists(static_js):
        fix_file(static_js)
