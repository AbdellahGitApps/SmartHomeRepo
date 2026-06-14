import re
import json

def analyze_family_migration():
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()

    orm_usages = re.findall(r'def \w+.*?FamilyMember.*?', content, re.DOTALL | re.IGNORECASE)
    # A more precise way:
    # Find all functions containing "FamilyMember"
    funcs = re.split(r'^def ', content, flags=re.MULTILINE)[1:]
    
    uses_orm = []
    uses_sqlite = []
    
    for func in funcs:
        func_name = func.split('(')[0]
        if 'FamilyMember' in func:
            uses_orm.append(func_name)
        if 'family_members' in func.lower() and ('conn.execute' in func or 'cursor.execute' in func or 'cur.execute' in func):
            uses_sqlite.append(func_name)
            
    print("Uses ORM:")
    for x in uses_orm: print("- " + x)
    print("\nUses SQLite raw:")
    for x in uses_sqlite: print("- " + x)

if __name__ == '__main__':
    analyze_family_migration()
