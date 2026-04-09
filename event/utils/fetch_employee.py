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
    seen_ids = set()

    offset = 0
    limit = 50

    for _ in range(20):
        users = _fetch_chunk(session, url, offset, limit)

        if not users:
            break

        for u in users:
            emp_no = u.get("employeeNo")
            if not emp_no or emp_no in seen_ids:
                continue

            seen_ids.add(emp_no)
            all_users[emp_no] = u

        offset += len(users)
        time.sleep(0.2)

    extra_offsets = [0, 30, 60, 90, 120, 150, 200, 300]

    for start in extra_offsets:
        users = _fetch_chunk(session, url, start, limit)

        for u in users:
            emp_no = u.get("employeeNo")
            if not emp_no or emp_no in seen_ids:
                continue

            seen_ids.add(emp_no)
            all_users[emp_no] = u

        time.sleep(0.2)

    return list(all_users.values())
