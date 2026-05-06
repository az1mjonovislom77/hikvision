import requests
from requests.auth import HTTPDigestAuth

HK_URL = "http://192.168.0.68/ISAPI/AccessControl/UserInfo/Search?format=json"
HK_USER = "admin"
HK_PASS = "Ats@amaar442"

payload = {
    "UserInfoSearchCond": {
        "searchID": "1",
        "maxResults": 30,
        "searchResultPosition": 0
    }
}

r = requests.post(
    HK_URL,
    json=payload,
    auth=HTTPDigestAuth(HK_USER, HK_PASS),
    timeout=10
)

print("STATUS:", r.status_code)
print("TEXT:", r.text[:500])
