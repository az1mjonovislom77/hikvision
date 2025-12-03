import requests
from drf_spectacular.utils import extend_schema, OpenApiParameter
from requests.auth import HTTPDigestAuth
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.timezone import make_aware
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.utils import timezone
from django.utils.dateparse import parse_date
from event.models import AccessEvent
from person.models import Employee
from person.utils import download_face_from_url, fix_hikvision_time, get_next_employee_no, UZ_TZ, format_late
from person.serializers import EmployeeSerializer, EmployeeCreateSerializer, EmployeeUpdateSerializer
from decouple import config

HIKVISION_IP = config("HIKVISION_IP")
HIKVISION_USER = config("HIKVISION_USER")
HIKVISION_PASS = config("HIKVISION_PASS")


@extend_schema(tags=['Employee'])
class FullSyncEmployeesView(APIView):
    def get(self, request):

        count_url = f"http://{HIKVISION_IP}/ISAPI/AccessControl/UserInfo/Search?format=json"

        count_payload = {
            "UserInfoSearchCond": {
                "searchID": "1",
                "searchResultPosition": 0,
                "maxResults": 1
            }
        }

        count_res = requests.post(
            count_url,
            json=count_payload,
            auth=HTTPDigestAuth(HIKVISION_USER, HIKVISION_PASS),
            timeout=10
        ).json()

        total_matches = count_res.get("UserInfoSearch", {}).get("totalMatches", 0)
        db_persons = Employee.objects.all()
        db_count = db_persons.count()

        # ❗ Logika o‘zgarmadi
        if total_matches == db_count:
            serializer = EmployeeSerializer(db_persons, many=True, context={"request": request})
            return Response({"synced": False, "message": "All persons already synced", "users": serializer.data})

        full_payload = {
            "UserInfoSearchCond": {
                "searchID": "1",
                "searchResultPosition": 0,
                "maxResults": 300
            }
        }

        full_res = requests.post(
            count_url,
            json=full_payload,
            auth=HTTPDigestAuth(HIKVISION_USER, HIKVISION_PASS),
            timeout=10
        ).json()

        hikvision_users = full_res.get("UserInfoSearch", {}).get("UserInfo", [])
        hk_ids = {u.get("employeeNo") for u in hikvision_users}
        db_ids = set(db_persons.values_list("employee_no", flat=True))

        # delete
        to_delete = db_ids - hk_ids
        Employee.objects.filter(employee_no__in=to_delete).delete()

        # add
        to_add = hk_ids - db_ids
        added = 0

        for u in hikvision_users:
            emp = u.get("employeeNo")
            if emp not in to_add:
                continue

            name = u.get("name")
            face_url = u.get("faceURL")

            person, _ = Employee.objects.update_or_create(
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

        final_qs = Employee.objects.all()
        serializer = EmployeeSerializer(final_qs, many=True, context={"request": request})

        return Response({"synced": True, "deleted": len(to_delete), "added": added, "users": serializer.data})


@extend_schema(tags=['Employee'])
class EmployeeCreateView(APIView):

    @extend_schema(request=EmployeeCreateSerializer, responses={200: None})
    def post(self, request):
        serializers = EmployeeCreateSerializer(data=request.data)
        serializers.is_valid(raise_exception=True)
        v = serializers.validated_data

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

        res = requests.post(
            url, json=payload,
            auth=HTTPDigestAuth(HIKVISION_USER, HIKVISION_PASS),
            timeout=10
        )

        if res.status_code != 200:
            return Response({"error": "Hikvision error", "detail": res.text}, status=400)

        Employee.objects.create(
            employee_no=next_emp,
            name=v["name"],
            user_type=v["user_type"],
            begin_time=v["begin_time"],
            end_time=v["end_time"],
            door_right=v["door_right"],
            raw_json=payload
        )

        return Response({"status": "Employee created", "employee_no": next_emp})


@extend_schema(tags=['Employee'])
class EmployeeUpdateView(APIView):

    @extend_schema(request=EmployeeUpdateSerializer, responses={200: None})
    def put(self, request, employee_no):

        person = Employee.objects.filter(employee_no=employee_no).first()
        if not person:
            return Response({"error": "Employee not found"}, status=404)

        ser = EmployeeUpdateSerializer(data=request.data, partial=True)
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

        res = requests.put(
            url, json=payload,
            auth=HTTPDigestAuth(HIKVISION_USER, HIKVISION_PASS),
            timeout=10
        )

        if res.status_code != 200:
            return Response({"error": "Hikvision update failed", "detail": res.text}, status=400)

        person.name = name
        person.user_type = user_type
        person.door_right = door_right
        person.begin_time = begin_dt
        person.end_time = end_dt
        person.save()

        return Response({"status": "updated"})


@extend_schema(tags=['Employee'])
class EmployeeDeleteView(APIView):

    def delete(self, request, employee_no):
        url = f"http://{HIKVISION_IP}/ISAPI/AccessControl/UserInfo/Delete?format=json"

        payload = {
            "UserInfoDelCond": {
                "EmployeeNoList": [{"employeeNo": employee_no}]
            }
        }

        res = requests.put(
            url, json=payload,
            auth=HTTPDigestAuth(HIKVISION_USER, HIKVISION_PASS),
            timeout=10
        )

        if res.status_code != 200:
            return Response({"error": "Delete failed", "detail": res.text}, status=400)

        Employee.objects.filter(employee_no=employee_no).delete()

        return Response({"status": "deleted"})


@extend_schema(tags=["Employee"], parameters=[OpenApiParameter(name="date", required=False, type=str)])
class DailyAccessListView(APIView):

    def get(self, request):

        date_str = request.GET.get("date")
        if not date_str:
            date_obj = now().date()
            date_str = date_obj.strftime("%Y-%m-%d")
        else:
            date_obj = parse_date(date_str)
            if not date_obj:
                return Response({"error": "Sanani noto‘g‘ri formatda kiritdingiz"}, status=400)

        employee_set = set(
            AccessEvent.objects.values_list("employee_no", flat=True)
        )

        result = []

        total = len(employee_set)
        came = 0
        late = 0
        absent = 0

        staff_map = {
            s.employee_no: s
            for s in Employee.objects.select_related("shift").all()
        }

        for emp_id in employee_set:

            staff_obj = staff_map.get(emp_id)

            # 🔥 staff_obj.person bo‘lgan joy → staff_obj
            if staff_obj and staff_obj.face_image:
                face_url = request.build_absolute_uri(staff_obj.face_image.url)
            else:
                face_url = None

            name = AccessEvent.objects.filter(employee_no=emp_id).values_list("name", flat=True).first()

            first_entry = AccessEvent.objects.filter(
                employee_no=emp_id,
                raw_json__label="Kirish",
                time__date=date_obj
            ).order_by("time").first()

            last_exit = AccessEvent.objects.filter(
                employee_no=emp_id,
                raw_json__label="Chiqish",
                time__date=date_obj
            ).order_by("-time").first()

            kirish_vaqti = first_entry.time.astimezone(UZ_TZ) if first_entry else None
            chiqish_vaqti = last_exit.time.astimezone(UZ_TZ) if last_exit else None

            if first_entry:
                came += 1
            else:
                absent += 1

            late_minutes = 0

            if staff_obj and staff_obj.shift and first_entry:
                shift_start_dt = make_aware(
                    datetime.combine(date_obj, staff_obj.shift.start_time),
                    UZ_TZ
                )
                if first_entry.time > shift_start_dt:
                    late += 1
                    late_minutes = int((first_entry.time - shift_start_dt).total_seconds() // 60)

            result.append(
                {
                    "employee_no": emp_id,
                    "name": name,
                    "kirish_vaqti": kirish_vaqti,
                    "chiqish_vaqti": chiqish_vaqti,
                    "kech_qolgan": format_late(late_minutes),
                    "face": face_url
                }
            )

        stats = {
            "xodimlar_soni": total,
            "kelganlar": came,
            "kech_qolganlar": late,
            "kelmaganlar": absent
        }

        return Response({"date": date_str, "employees": result, "stats": stats})

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
#         person = Employee.objects.filter(employee_no=emp).first()
#         if person:
#             person.face_image.save(f"{emp}.jpg", v["image"], save=True)
#
#         return Response({
#             "status": "Face uploaded successfully",
#             "employee_no": emp
#         })
