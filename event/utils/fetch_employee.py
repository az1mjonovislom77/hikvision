import time
import requests
import logging
from requests.auth import HTTPDigestAuth

logger = logging.getLogger("hikvision_fetch")
logger.setLevel(logging.DEBUG)


def fetch_all_employees(device):
    url = f"http://{device.ip}/ISAPI/AccessControl/UserInfo/Search?format=json"

    def create_session():
        s = requests.Session()
        s.auth = HTTPDigestAuth(device.username, device.password)
        s.headers.update({"Content-Type": "application/json"})
        return s

    session = create_session()

    search_id = "0"
    offset = 0
    limit = 50
    all_users = []
    max_loops = 1000

    logger.warning(f"🚀 START FETCH | device={device.ip}")

    for i in range(max_loops):
        payload = {
            "UserInfoSearchCond": {
                "searchID": search_id,
                "searchResultPosition": offset,
                "maxResults": limit,
            }
        }

        logger.debug(f"➡️ REQUEST | offset={offset} | limit={limit}")

        try:
            r = session.post(url, json=payload, timeout=20)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            logger.error(f"❌ REQUEST FAILED | offset={offset}")
            break

        logger.debug(f"⬅️ STATUS = {r.status_code}")

        if r.status_code == 401:
            logger.warning(f"🔐 401 detected | offset={offset} → RESET SESSION")

            time.sleep(1)
            session = create_session()

            try:
                r = session.post(url, json=payload, timeout=20)
                logger.warning("🔄 NEW SESSION CREATED")
            except Exception:
                logger.exception("❌ RETRY FAILED AFTER 401")
                break

        if r.status_code != 200:
            logger.error(f"❌ BAD STATUS CODE: {r.status_code} | offset={offset}")
            break

        try:
            data = r.json()
        except Exception:
            logger.exception("❌ JSON PARSE ERROR")
            break

        block = data.get("UserInfoSearch", {})
        users = block.get("UserInfo", []) or []
        logger.warning(f"📦 BATCH | offset={offset} | got={len(users)} | total={len(all_users)}")

        if block.get("searchID") and block["searchID"] != "0":
            search_id = block["searchID"]

        if not users:
            logger.warning("🛑 STOP: empty users")
            break

        all_users.extend(users)
        offset += len(users)

        if len(users) < 30:
            logger.warning("🛑 STOP: last batch")
            break

        time.sleep(0.5)

    logger.warning(f"✅ DONE | TOTAL FETCHED = {len(all_users)}")

    return all_users
