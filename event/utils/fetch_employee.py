import time
import requests
import logging
from requests.auth import HTTPDigestAuth

logger = logging.getLogger(__name__)


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

    logger.info("fetch_all_employees started: device=%s", device.ip)

    for i in range(max_loops):
        payload = {
            "UserInfoSearchCond": {
                "searchID": search_id,
                "searchResultPosition": offset,
                "maxResults": limit,
            }
        }

        try:
            r = session.post(url, json=payload, timeout=20)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
            logger.error("fetch_all_employees: request failed device=%s offset=%d", device.ip, offset)
            break

        if r.status_code == 401:
            logger.warning("fetch_all_employees: 401 at offset=%d, resetting session device=%s", offset, device.ip)
            time.sleep(1)
            session = create_session()
            try:
                r = session.post(url, json=payload, timeout=20)
            except Exception:
                logger.exception("fetch_all_employees: retry failed after 401 device=%s", device.ip)
                break

        if r.status_code != 200:
            logger.error(
                "fetch_all_employees: unexpected status=%d device=%s offset=%d", r.status_code, device.ip, offset
            )
            break

        try:
            data = r.json()
        except Exception:
            logger.exception("fetch_all_employees: json parse error device=%s offset=%d", device.ip, offset)
            break

        block = data.get("UserInfoSearch", {})
        users = block.get("UserInfo", []) or []

        logger.debug("fetch_all_employees: batch device=%s offset=%d got=%d total=%d",
                     device.ip, offset, len(users), len(all_users))

        if block.get("searchID") and block["searchID"] != "0":
            search_id = block["searchID"]

        if not users:
            break

        all_users.extend(users)
        offset += len(users)

        if len(users) < 30:
            break

        time.sleep(0.5)

    logger.info("fetch_all_employees done: device=%s total=%d", device.ip, len(all_users))
    return all_users
