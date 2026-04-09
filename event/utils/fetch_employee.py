import time
import requests
from requests.auth import HTTPDigestAuth


def fetch_all_employees(device):
    url = f"http://{device.ip}/ISAPI/AccessControl/UserInfo/Search?format=json"

    session = requests.Session()
    session.auth = HTTPDigestAuth(device.username, device.password)
    session.headers.update({"Content-Type": "application/json"})

    search_id = "0"
    offset = 0
    limit = 50

    all_users = []

    while True:
        payload = {
            "UserInfoSearchCond": {
                "searchID": search_id,
                "searchResultPosition": offset,
                "maxResults": limit,
            }
        }

        r = session.post(url, json=payload, timeout=15)
        if r.status_code != 200:
            print("❌ Request error:", r.status_code)
            break

        data = r.json()
        block = data.get("UserInfoSearch", {})
        users = block.get("UserInfo", []) or []

        print(f"OFFSET={offset} | KELDI={len(users)}")

        if block.get("searchID") and block["searchID"] != "0":
            search_id = block["searchID"]

        if not users:
            break

        all_users.extend(users)

        # 👇 ENG MUHIM O‘ZGARISH
        offset += limit

        # 👇 fallback himoya (infinite loopdan saqlaydi)
        if len(users) < limit:
            break

        time.sleep(0.2)

    return all_users
