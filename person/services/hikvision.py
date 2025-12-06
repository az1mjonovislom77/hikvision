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

        r = requests.post(url, json=payload, auth=HikvisionService._auth(device), timeout=10)

        return r.json().get("UserInfoSearch", {}).get("UserInfo", [])

    @staticmethod
    def create_user(device, data):
        url = HikvisionService._url(device, "AccessControl/UserInfo/Record")
        return requests.post(url, json=data, auth=HikvisionService._auth(device), timeout=10)

    @staticmethod
    def update_user(device, data):
        url = HikvisionService._url(device, "AccessControl/UserInfo/Modify")
        return requests.put(url, json=data, auth=HikvisionService._auth(device), timeout=10)

    @staticmethod
    def delete_user(device, employee_no):
        url = HikvisionService._url(device, "AccessControl/UserInfo/Delete")
        payload = {"UserInfoDelCond": {"EmployeeNoList": [{"employeeNo": employee_no}]}}
        return requests.put(url, json=payload, auth=HikvisionService._auth(device), timeout=10)
