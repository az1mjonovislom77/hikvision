import requests
from decouple import config
from requests.auth import HTTPDigestAuth

HIKVISION_IP = config("HIKVISION_IP")
HIKVISION_USER = config("HIKVISION_USER")
HIKVISION_PASS = config("HIKVISION_PASS")


class HikvisionService:

    BASE = f"http://{HIKVISION_IP}/ISAPI"

    @staticmethod
    def _auth():
        return HTTPDigestAuth(HIKVISION_USER, HIKVISION_PASS)

    @staticmethod
    def post(path, payload):
        url = f"{HikvisionService.BASE}/{path}?format=json"
        return requests.post(url, json=payload, auth=HikvisionService._auth(), timeout=10)

    @staticmethod
    def put(path, payload):
        url = f"{HikvisionService.BASE}/{path}?format=json"
        return requests.put(url, json=payload, auth=HikvisionService._auth(), timeout=10)

    @staticmethod
    def search_users(max_results=300):
        payload = {
            "UserInfoSearchCond": {
                "searchID": "1",
                "searchResultPosition": 0,
                "maxResults": max_results
            }
        }
        result = HikvisionService.post("AccessControl/UserInfo/Search", payload)
        return result.json().get("UserInfoSearch", {}).get("UserInfo", [])

    @staticmethod
    def create_user(data):
        return HikvisionService.post("AccessControl/UserInfo/Record", data)

    @staticmethod
    def update_user(data):
        return HikvisionService.put("AccessControl/UserInfo/Modify", data)

    @staticmethod
    def delete_user(employee_no):
        payload = {"UserInfoDelCond": {"EmployeeNoList": [{"employeeNo": employee_no}]}}
        return HikvisionService.put("AccessControl/UserInfo/Delete", payload)
