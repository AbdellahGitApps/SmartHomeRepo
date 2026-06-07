import requests

def test():
    session = requests.Session()
    # Attempt login
    login_data = {'username': 'system_owner', 'password': '1'}
    # the endpoint might be expecting application/x-www-form-urlencoded
    res = session.post('http://127.0.0.1:8000/dashboard-login', data=login_data, allow_redirects=True)
    
    # fetch users
    users_res = session.get('http://127.0.0.1:8000/users')
    html = users_res.text
    
    if 'data-i18n="col_user"' in html or 'data-i18n-placeholder' in html:
        print("SUCCESS! data-i18n found in runtime HTML.")
    else:
        print("FAILED! No data-i18n tags found in /users HTML.")
        print("Snippet length:", len(html))
        # print snippet around <thead>
        if '<thead>' in html:
            idx = html.find('<thead>')
            print(html[idx:idx+300])

if __name__ == "__main__":
    test()
