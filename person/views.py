import requests
from drf_spectacular.utils import extend_schema
from requests.auth import HTTPDigestAuth
from rest_framework.views import APIView
from rest_framework.response import Response
from person.models import Person
from person.utils import download_face_from_url, fix_hikvision_time, get_next_employee_no
from person.serializers import PersonSerializer, PersonCreateSerializer, PersonUpdateSerializer
from datetime import timedelta
from django.utils import timezone

HIKVISION_IP = "192.168.0.68"
HIKVISION_USER = "admin"
HIKVISION_PASS = "Ats@amaar442"


class FullSyncPersonsView(APIView):
    def get(self, request):

        count_url = f"http://{HIKVISION_IP}/ISAPI/AccessControl/UserInfo/Search?format=json"

        count_payload = {
            "UserInfoSearchCond": {
                "searchID": "1",
                "searchResultPosition": 0,
                "maxResults": 1
            }
        }

        count_res = requests.post(count_url, json=count_payload, auth=HTTPDigestAuth(HIKVISION_USER, HIKVISION_PASS),
                                  timeout=10).json()

        total_matches = count_res.get("UserInfoSearch", {}).get("totalMatches", 0)
        db_persons = Person.objects.all()
        db_count = db_persons.count()

        if total_matches == db_count:
            serializer = PersonSerializer(db_persons, many=True, context={"request": request})
            return Response({"synced": False, "message": "All persons already synced", "users": serializer.data})

        full_payload = {
            "UserInfoSearchCond": {
                "searchID": "1",
                "searchResultPosition": 0,
                "maxResults": 300
            }
        }

        full_res = requests.post(count_url, json=full_payload, auth=HTTPDigestAuth(HIKVISION_USER, HIKVISION_PASS),
                                 timeout=10).json()

        hikvision_users = full_res.get("UserInfoSearch", {}).get("UserInfo", [])
        hk_ids = {u.get("employeeNo") for u in hikvision_users}
        db_ids = set(db_persons.values_list("employee_no", flat=True))
        to_delete = db_ids - hk_ids
        Person.objects.filter(employee_no__in=to_delete).delete()
        to_add = hk_ids - db_ids
        added = 0

        for u in hikvision_users:
            emp = u.get("employeeNo")
            if emp not in to_add:
                continue

            name = u.get("name")
            face_url = u.get("faceURL")

            person, _ = Person.objects.update_or_create(
                employee_no=emp,
                defaults={
                    "name": name,
                    "user_type": u.get("userType", "normal"),
                    "door_right": u.get("doorRight", "1"),
                    "raw_json": u,
                    "face_url": face_url,
                }
            )

            if face_url:
                img = download_face_from_url(face_url)
                if img:
                    person.face_image.save(f"{emp}.jpg", img, save=True)

            added += 1

        final_qs = Person.objects.all()
        serializer = PersonSerializer(final_qs, many=True, context={"request": request})

        return Response({"synced": True, "deleted": len(to_delete), "added": added, "users": serializer.data})


class PersonCreateView(APIView):

    @extend_schema(request=PersonCreateSerializer, responses={200: None})
    def post(self, request):
        ser = PersonCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        v = ser.validated_data
        next_emp = get_next_employee_no()
        begin_fixed, end_fixed = fix_hikvision_time(v["begin_time"], v["end_time"])

        url = f"http://{HIKVISION_IP}/ISAPI/AccessControl/UserInfo/Record?format=json"

        payload = {
            "UserInfo": {
                "employeeNo": next_emp,
                "name": v["name"],
                "userType": v["user_type"],
                "Valid": {
                    "enable": True,
                    "beginTime": begin_fixed,
                    "endTime": end_fixed,
                    "timeType": "local"
                },
                "doorRight": v["door_right"]
            }
        }

        res = requests.post(url, json=payload, auth=HTTPDigestAuth(HIKVISION_USER, HIKVISION_PASS), timeout=10)
        if res.status_code != 200: return Response({"error": "Hikvision error", "detail": res.text}, status=400)

        Person.objects.create(
            employee_no=next_emp,
            name=v["name"],
            user_type=v["user_type"],
            begin_time=v["begin_time"],
            end_time=v["end_time"],
            door_right=v["door_right"],
            raw_json=payload
        )

        return Response({
            "status": "Person created",
            "employee_no": next_emp
        })


class PersonUpdateView(APIView):

    @extend_schema(request=PersonUpdateSerializer, responses={200: None})
    def put(self, request, employee_no):

        person = Person.objects.filter(employee_no=employee_no).first()
        if not person:
            return Response({"error": "Person not found"}, status=404)

        ser = PersonUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        v = ser.validated_data
        name = v.get("name", person.name)
        user_type = v.get("user_type", person.user_type)
        door_right = v.get("door_right", person.door_right)
        begin_dt = v.get("begin_time", person.begin_time or timezone.now())
        end_dt = v.get("end_time", person.end_time or (timezone.now() + timedelta(days=3650)))
        begin_fixed, end_fixed = fix_hikvision_time(begin_dt, end_dt)
        url = f"http://{HIKVISION_IP}/ISAPI/AccessControl/UserInfo/Modify?format=json"

        payload = {
            "UserInfo": {
                "employeeNo": employee_no,
                "name": name,
                "userType": user_type,
                "doorRight": door_right,
                "Valid": {
                    "enable": True,
                    "beginTime": begin_fixed,
                    "endTime": end_fixed,
                    "timeType": "local"
                }
            }
        }

        res = requests.put(url, json=payload, auth=HTTPDigestAuth(HIKVISION_USER, HIKVISION_PASS), timeout=10)

        if res.status_code != 200:
            return Response(
                {"error": "Hikvision update failed", "detail": res.text},
                status=400
            )

        person.name = name
        person.user_type = user_type
        person.door_right = door_right
        person.begin_time = begin_dt
        person.end_time = end_dt
        person.save()

        return Response({"status": "updated"})


class PersonDeleteView(APIView):

    def delete(self, request, employee_no):
        url = f"http://{HIKVISION_IP}/ISAPI/AccessControl/UserInfo/Delete?format=json"

        payload = {
            "UserInfoDelCond": {
                "EmployeeNoList": [{"employeeNo": employee_no}]
            }
        }

        res = requests.put(url, json=payload, auth=HTTPDigestAuth(HIKVISION_USER, HIKVISION_PASS), timeout=10)

        if res.status_code != 200:
            return Response({"error": "Delete failed", "detail": res.text}, status=400)

        Person.objects.filter(employee_no=employee_no).delete()

        return Response({"status": "deleted"})

# class FaceCreateView(APIView):
#
#     @extend_schema(
#         request=FaceCreateSerializer,
#         responses={200: openapi.TYPE_OBJECT}
#     )
#     def post(self, request):
#
#         ser = FaceCreateSerializer(data=request.data)
#         ser.is_valid(raise_exception=True)
#         v = ser.validated_data
#
#         emp = v["employee_no"]
#         image = v["image"]
#
#         url = f"http://{HIKVISION_IP}/ISAPI/Intelligent/FDLib/FaceDataRecord?format=json"
#
#         json_part = {
#             "faceLibType": "blackFD",
#             "FDID": "1",            # face library ID (default)
#             "FPID": emp             # person identifier (employeeNo)
#         }
#
#         # Multipart form-data so‘rov
#         files = {
#             "FaceImage": ("face.jpg", image, "image/jpeg"),
#             "faceDataRecord": (None, json.dumps(json_part), "application/json")
#         }
#
#         res = requests.post(
#             url,
#             files=files,
#             auth=HTTPDigestAuth(HIKVISION_USER, HIKVISION_PASS),
#             timeout=10
#         )
#
#         if res.status_code not in (200, 201):
#             return Response({
#                 "error": "Face upload failed",
#                 "detail": res.text
#             }, status=400)
#
#         # LOCAL SAVE
#         person = Person.objects.filter(employee_no=emp).first()
#         if person:
#             person.face_image.save(f"{emp}.jpg", v["image"], save=True)
#
#         return Response({
#             "status": "Face uploaded successfully",
#             "employee_no": emp
#         })
