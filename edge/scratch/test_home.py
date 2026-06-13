import sys
sys.path.append('e:/SmartHomeMobileApp/edge')

from api.family_management_flow import create_family_member, FamilyMemberCreate, list_family_members
from routers.dashboard import delete_home_route
import sqlite3

try:
    print('Creating a mock home and family member...')
    class MockReq: pass
    req = MockReq()
    
    # Create member for home 888
    create_family_member(FamilyMemberCreate(home_id=888, name='Delete Me', role='Guest', enabled=True), req)
    
    print('Setting up mock home 888 in DB...')
    conn = sqlite3.connect('e:/SmartHomeMobileApp/edge/database/smart_home_edge.db')
    conn.execute("INSERT OR IGNORE INTO homes (id, name, home_code) VALUES (888, 'Temp Home', 'TEMP-888')")
    conn.commit()
    
    print('Deleting home 888 via delete_home_route...')
    res = delete_home_route('TEMP-888', conn)
    print('Delete Result:', res)
    
    mems = list_family_members(home_id=888)['members']
    print('Members left for home 888:', len(mems))
    
    if len(mems) == 0:
        print('Validation Passed: delete_home_route cleanup worked!')
    else:
        print('Validation Failed: members still exist!')
        sys.exit(1)
        
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
