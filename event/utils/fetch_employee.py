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
    limit = 100

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
            break

        data = r.json()
        block = data.get("UserInfoSearch", {})

        users = block.get("UserInfo", []) or []
        status = block.get("responseStatusStrg", "")

        if block.get("searchID") and block["searchID"] != "0":
            search_id = block["searchID"]

        all_users.extend(users)

        if status != "MORE" or not users:
            break

        offset += len(users)
        time.sleep(0.2)

    return all_users
