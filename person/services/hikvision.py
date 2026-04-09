import time

import requests
from requests.auth import HTTPDigestAuth


class HikvisionService:

    @staticmethod
    def _auth(device):
        return HTTPDigestAuth(device.username, device.password)

    @staticmethod
    def _url(device, path):
        return f"http://{device.ip}/ISAPI/{path}?format=json"

    @staticmethod
    def search_users(device, max_results=300):
        url = HikvisionService._url(device, "AccessControl/UserInfo/Search")

        payload = {
            "UserInfoSearchCond": {
                "searchID": "1",
                "searchResultPosition": 0,
                "maxResults": max_results
            }
        }

        result = requests.post(url, json=payload, auth=HikvisionService._auth(device), timeout=10)

        return result.json().get("UserInfoSearch", {}).get("UserInfo", [])

    @staticmethod
    def create_user(device, data):
        url = HikvisionService._url(device, "AccessControl/UserInfo/Record")

        session = requests.Session() 
        session.auth = HTTPDigestAuth(device.username, device.password)

        for i in range(6):
            try:
                time.sleep(1.5)

                r = session.post(
                    url,
                    json=data,
                    timeout=10
                )

                if r.status_code == 200:
                    return r

                print(f"Bad status: {r.status_code} → retry {i + 1}")

            except requests.exceptions.ConnectionError:
                print(f"Connection refused → retry {i + 1}")

            except requests.exceptions.Timeout:
                print(f"Timeout → retry {i + 1}")

        raise Exception("Device busy or refusing connections")

    @staticmethod
    def update_user(device, data):
        url = HikvisionService._url(device, "AccessControl/UserInfo/Modify")
        return requests.put(url, json=data, auth=HikvisionService._auth(device), timeout=10)

    @staticmethod
    def delete_user(device, employee_no):
        url = HikvisionService._url(device, "AccessControl/UserInfo/Delete")
        payload = {"UserInfoDelCond": {"EmployeeNoList": [{"employeeNo": employee_no}]}}
        return requests.put(url, json=payload, auth=HikvisionService._auth(device), timeout=10)
