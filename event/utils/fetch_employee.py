import time
import requests
import logging
from requests.auth import HTTPDigestAuth

logger = logging.getLogger("hikvision_fetch")
logger.setLevel(logging.DEBUG)


def fetch_all_employees(device):
    url = f"http://{device.ip}/ISAPI/AccessControl/UserInfo/Search?format=json"

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

        logger.debug(f"➡️ REQUEST | offset={offset} | limit={limit} | search_id={search_id}")

        # ✅ XUDDI ORIGINALDEK — timeout bo‘lsa chiqadi
        try:
            r = requests.post(
                url,
                json=payload,
                auth=HTTPDigestAuth(device.username, device.password),
                headers={"Content-Type": "application/json"},
                timeout=15
            )
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError):
            logger.error("❌ TIMEOUT / CONNECTION ERROR → STOP")
            break  # 🔥 ENG MUHIM (original kabi)

        logger.debug(f"⬅️ RESPONSE STATUS = {r.status_code}")

        if r.status_code == 401:
            logger.warning("🔐 401 detected → retrying...")
            time.sleep(0.5)

            try:
                r = requests.post(
                    url,
                    json=payload,
                    auth=HTTPDigestAuth(device.username, device.password),
                    headers={"Content-Type": "application/json"},
                    timeout=15
                )
            except Exception:
                logger.exception("❌ RETRY FAILED")
                break  # 🔥 originalga mos

        if r.status_code != 200:
            logger.error(f"❌ BAD STATUS CODE: {r.status_code}")
            break  # 🔥 originalga mos

        try:
            data = r.json()
        except Exception:
            logger.exception("❌ JSON PARSE ERROR")
            break  # 🔥 originalga mos

        block = data.get("UserInfoSearch", {})
        users = block.get("UserInfo", []) or []
        status = block.get("responseStatusStrg", "")

        logger.warning(f"📦 BATCH | offset={offset} | count={len(users)} | status={status} | total={len(all_users)}")

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

        time.sleep(0.2)

    logger.warning(f"✅ DONE | TOTAL FETCHED = {len(all_users)}")

    return all_users