import openpyxl
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from person.models import Employee
from person.serializers import EmployeeSerializer, EmployeeCreateSerializer, EmployeeUpdateSerializer
from person.services.employee import EmployeeService
from person.services.hikvision import HikvisionService
from person.utils import get_next_employee_no, fix_hikvision_time, UZ_TZ, format_late, download_face_from_url, \
    get_first_last_events
from django.utils.timezone import now, make_aware
from django.utils.dateparse import parse_date
from datetime import datetime
from django.http import HttpResponse


@extend_schema(tags=['Employee'])
class FullSyncEmployeesView(APIView):

    def get(self, request):
        hk_users = HikvisionService.search_users()
        stats = EmployeeService.sync_from_hikvision(hk_users)
        serializer = EmployeeSerializer(Employee.objects.all(), many=True, context={"request": request})

        return Response({"synced": True, **stats, "users": serializer.data})


@extend_schema(tags=['Employee'])
class EmployeeCreateView(APIView):

    @extend_schema(request=EmployeeCreateSerializer, responses={200: None})
    def post(self, request):
        serializers = EmployeeCreateSerializer(data=request.data)
        serializers.is_valid(raise_exception=True)
        data = serializers.validated_data
        employees_no = get_next_employee_no()
        begin, end = fix_hikvision_time(data["begin_time"], data["end_time"])

        payload = {
            "UserInfo": {
                "employeeNo": employees_no,
                "name": data["name"],
                "userType": data.get("user_type", "normal"),
                "doorRight": data.get("door_right", "1"),
                "Valid": {
                    "enable": True,
                    "beginTime": begin,
                    "endTime": end,
                    "timeType": "local"
                }
            }
        }

        result = HikvisionService.create_user(payload)
        if result.status_code != 200:
            return Response({"error": "Hikvision error", "detail": result.text}, status=400)

        Employee.objects.create(
            employee_no=employees_no,
            name=data["name"],
            user_type=data.get("user_type"),
            door_right=data.get("door_right"),
            begin_time=data["begin_time"],
            end_time=data["end_time"]
        )

        return Response({"status": "created", "employee_no": employees_no})


@extend_schema(tags=['Employee'])
class EmployeeUpdateView(APIView):

    def put(self, request, employee_no):
        person = Employee.objects.filter(employee_no=employee_no).first()
        if not person:
            return Response({"error": "Not found"}, status=404)

        serializers = EmployeeUpdateSerializer(data=request.data, partial=True)
        serializers.is_valid(raise_exception=True)
        data = serializers.validated_data
        name = data.get("name", person.name)
        user_type = data.get("user_type", person.user_type)
        door_right = data.get("door_right", person.door_right)
        begin = data.get("begin_time", person.begin_time)
        end = data.get("end_time", person.end_time)

        begin_str, end_str = fix_hikvision_time(begin, end)

        payload = {
            "UserInfo": {
                "employeeNo": employee_no,
                "name": name,
                "userType": user_type,
                "doorRight": door_right,
                "Valid": {
                    "enable": True,
                    "beginTime": begin_str,
                    "endTime": end_str,
                    "timeType": "local"
                }
            }
        }

        result = HikvisionService.update_user(payload)
        if result.status_code != 200:
            return Response({"error": "Update failed", "detail": result.text}, status=400)

        person.name = name
        person.user_type = user_type
        person.door_right = door_right
        person.begin_time = begin
        person.end_time = end
        person.save()

        return Response({"status": "updated"})


@extend_schema(tags=['Employee'])
class EmployeeDeleteView(APIView):

    def delete(self, request, employee_no):
        result = HikvisionService.delete_user(employee_no)
        if result.status_code != 200:
            return Response({"error": "Delete failed", "detail": result.text}, status=400)

        Employee.objects.filter(employee_no=employee_no).delete()
        return Response({"status": "deleted"})


@extend_schema(tags=["Employee"], parameters=[OpenApiParameter(name="date", type=str)])
class DailyAccessListView(APIView):

    def get(self, request):
        date_str = request.GET.get("date")
        date_obj = parse_date(date_str) if date_str else now().date()
        employees = Employee.objects.select_related("shift")
        result = []

        stats = {"total": employees.count(), "came": 0, "late": 0, "absent": 0}

        for employee in employees:
            first, last = get_first_last_events(employee.employee_no, date_obj)

            if first:
                stats["came"] += 1
            else:
                stats["absent"] += 1

            late_min = 0
            if employee.shift and first:
                shift_start = make_aware(datetime.combine(date_obj, employee.shift.start_time), UZ_TZ)
                if first.time > shift_start:
                    stats["late"] += 1
                    late_min = int((first.time - shift_start).total_seconds() / 60)

            result.append({
                "employee_no": employee.employee_no,
                "name": employee.name,
                "kirish": first.time.astimezone(UZ_TZ) if first else None,
                "chiqish": last.time.astimezone(UZ_TZ) if last else None,
                "late": format_late(late_min),
                "face": request.build_absolute_uri(employee.face_image.url) if employee.face_image else None
            })

        return Response({"date": str(date_obj), "employees": result, "stats": stats})


@extend_schema(tags=["DailyExel"],
               parameters=[OpenApiParameter(name="date", required=False, type=str, description="YYYY-MM-DD")])
class DailyAccessExcelExport(APIView):

    def get(self, request):
        date_str = request.GET.get("date")
        date_obj = parse_date(date_str) if date_str else now().date()
        employees = Employee.objects.select_related("shift")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"{date_obj}"
        headers = ["Employee No", "Name", "Kirish", "Chiqish", "Late", "Shift"]
        ws.append(headers)

        for employee in employees:
            first, last = get_first_last_events(employee.employee_no, date_obj)
            kirish = first.time.astimezone(UZ_TZ).strftime("%H:%M:%S") if first else ""
            chiqish = last.time.astimezone(UZ_TZ).strftime("%H:%M:%S") if last else ""

            late_text = ""
            if employee.shift and first:
                shift_start = make_aware(datetime.combine(date_obj, employee.shift.start_time), UZ_TZ)
                if first.time > shift_start:
                    diff_min = int((first.time - shift_start).total_seconds() / 60)
                    late_text = format_late(diff_min)

            shift_start = employee.shift.start_time.strftime("%H:%M") if employee.shift else ""

            ws.append([employee.employee_no, employee.name, kirish, chiqish, late_text, shift_start])

        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="daily_{date_obj}.xlsx"'
        wb.save(response)
        return response

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
#         person = Employee.objects.filter(employee_no=emp).first()
#         if person:
#             person.face_image.save(f"{emp}.jpg", v["image"], save=True)
#
#         return Response({"status": "Face uploaded successfully","employee_no": emp})
