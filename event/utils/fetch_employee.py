import time
import uuid
import requests
from requests.auth import HTTPDigestAuth


def fetch_all_employees(device):
    url = f"http://{device.ip}/ISAPI/AccessControl/UserInfo/Search?format=json"

    session = requests.Session()
    session.auth = HTTPDigestAuth(device.username, device.password)
    session.headers.update({"Content-Type": "application/json"})

    search_id = str(uuid.uuid4())
    offset = 0
    limit = 50

    all_users = []
    seen_ids = set()

    for _ in range(1000):

        payload = {
            "UserInfoSearchCond": {
                "searchID": search_id,
                "searchResultPosition": offset,
                "maxResults": limit,
            }
        }

        try:
            r = session.post(url, json=payload, timeout=15)
        except requests.RequestException:
            break

        if r.status_code != 200:
            break

        try:
            data = r.json()
        except Exception:
            break

        block = data.get("UserInfoSearch", {})
        users = block.get("UserInfo", []) or []
        total = block.get("totalMatches", 0)

        if not users:
            break

        new_count = 0

        for u in users:
            emp_no = u.get("employeeNo")

            if not emp_no or emp_no in seen_ids:
                continue

            seen_ids.add(emp_no)
            all_users.append(u)
            new_count += 1

        if new_count == 0:
            break

        offset += len(users)
        if total and offset >= total:
            break

        time.sleep(0.2)

    return all_users
