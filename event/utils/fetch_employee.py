import time
import uuid
import requests
from requests.auth import HTTPDigestAuth


def _fetch_chunk(session, url, start, limit):
    payload = {
        "UserInfoSearchCond": {
            "searchID": str(uuid.uuid4()),
            "searchResultPosition": start,
            "maxResults": limit,
        }
    }

    try:
        r = session.post(url, json=payload, timeout=15)
        if r.status_code != 200:
            return []

        data = r.json()
    except Exception:
        return []

    return data.get("UserInfoSearch", {}).get("UserInfo", []) or []


def fetch_all_employees(device):
    url = f"http://{device.ip}/ISAPI/AccessControl/UserInfo/Search?format=json"

    session = requests.Session()
    session.auth = HTTPDigestAuth(device.username, device.password)
    session.headers.update({"Content-Type": "application/json"})

    all_users = {}
    seen = set()

    offsets = [0, 20, 40, 60, 80, 100, 120, 150, 200]

    for offset in offsets:
        payload = {
            "UserInfoSearchCond": {
                "searchID": str(uuid.uuid4()),
                "searchResultPosition": offset,
                "maxResults": 50,
            }
        }

        try:
            r = session.post(url, json=payload, timeout=10)
            if r.status_code != 200:
                continue

            data = r.json()
            users = data.get("UserInfoSearch", {}).get("UserInfo", []) or []

            for u in users:
                emp_no = u.get("employeeNo")
                if not emp_no or emp_no in seen:
                    continue

                seen.add(emp_no)
                all_users[emp_no] = u

        except Exception:
            continue

        time.sleep(0.2)

    return list(all_users.values())