import time
import requests
import logging
from requests.auth import HTTPDigestAuth

logger = logging.getLogger("hikvision_fetch")
logger.setLevel(logging.DEBUG)


def fetch_all_employees(device):
    url = f"http://{device.ip}/ISAPI/AccessControl/UserInfo/Search?format=json"

    session = requests.Session()
    session.auth = HTTPDigestAuth(device.username, device.password)
    session.headers.update({"Content-Type": "application/json"})

    search_id = "0"
    offset = 0
    limit = 50

    all_users = []

    logger.warning(f"🚀 START FETCH | device={device.ip}")

    while True:
        payload = {
            "UserInfoSearchCond": {
                "searchID": search_id,
                "searchResultPosition": offset,
                "maxResults": limit,
            }
        }

        logger.debug(f"➡️ REQUEST | offset={offset} | limit={limit} | search_id={search_id}")

        try:
            r = session.post(url, json=payload, timeout=15)
        except Exception as e:
            logger.exception(f"❌ REQUEST FAILED | offset={offset}")
            break

        logger.debug(f"⬅️ RESPONSE STATUS = {r.status_code}")

        if r.status_code != 200:
            logger.error(f"❌ BAD STATUS CODE: {r.status_code}")
            break

        try:
            data = r.json()
        except Exception:
            logger.exception("❌ JSON PARSE ERROR")
            break

        block = data.get("UserInfoSearch", {})
        users = block.get("UserInfo", []) or []
        status = block.get("responseStatusStrg", "")

        logger.warning(
            f"📦 BATCH | offset={offset} | count={len(users)} | status={status} | total_collected={len(all_users)}"
        )

        if block.get("searchID") and block["searchID"] != "0":
            logger.debug(f"🔁 NEW search_id: {block['searchID']}")
            search_id = block["searchID"]

        # sample 1-2 user ko‘rib olish
        if users:
            logger.debug(f"👤 SAMPLE USER: {users[0].get('employeeNo')}")

        all_users.extend(users)

        if status != "MORE" or not users:
            logger.warning(
                f"🛑 STOP CONDITION | status={status} | users_empty={not users}"
            )
            break

        offset += len(users)
        time.sleep(0.2)

    logger.warning(f"✅ DONE | TOTAL FETCHED = {len(all_users)}")

    return all_users