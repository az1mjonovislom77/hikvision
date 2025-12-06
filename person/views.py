import openpyxl
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.utils.timezone import now, make_aware
from django.utils.dateparse import parse_date
from datetime import datetime
from person.models import Employee
from user.models import User
from utils.models import Devices
from person.serializers import (EmployeeSerializer, EmployeeCreateSerializer, EmployeeUpdateSerializer)
from person.utils import (fix_hikvision_time, get_next_employee_no, get_first_last_events, format_late, UZ_TZ)
from person.services.hikvision import HikvisionService
from person.services.employee import EmployeeService


@extend_schema(
    tags=["Employee"],
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=int,
            required=False,
            description="Faqat superadmin uchun. Tanlangan userning device larini sync qiladi."
        )
    ],
    responses={200: EmployeeSerializer(many=True)}
)
class FullSyncEmployeesView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmployeeSerializer

    def get(self, request):

        user = request.user

        if user.is_superuser or user.is_staff:
            user_id = request.GET.get("user_id")

            if not user_id:
                return Response(
                    {"error": "user_id superadmin uchun majburiy"},
                    status=400
                )

            target_user = User.objects.filter(id=user_id).first()
            if not target_user:
                return Response({"error": "Bunday user topilmadi"}, status=404)

            devices = Devices.objects.filter(user=target_user)

        else:
            devices = Devices.objects.filter(user=user)

        if not devices.exists():
            return Response({"error": "Ushbu userga device biriktirilmagan"}, status=400)

        total_stats = {
            "synced_devices": 0,
            "added": 0,
            "deleted": 0,
        }

        employees_final = []

        for device in devices:
            hk_users = HikvisionService.search_users(device)

            stats = EmployeeService.sync_from_hikvision(device, hk_users)

            total_stats["synced_devices"] += 1
            total_stats["added"] += stats["added"]
            total_stats["deleted"] += stats["deleted"]

            employees_final.extend(Employee.objects.filter(device=device))

        employees_final = list(set(employees_final))

        serializer = EmployeeSerializer(employees_final, many=True, context={"request": request})

        return Response({"success": True, **total_stats, "employees": serializer.data})


@extend_schema(tags=["Employee"])
class EmployeeCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=EmployeeCreateSerializer)
    def post(self, request):
        ser = EmployeeCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        user = request.user

        if user.is_superuser or user.is_staff:
            device_id = request.data.get("device_id")
            if not device_id:
                return Response({"error": "device_id admin uchun majburiy"}, status=400)

            device = Devices.objects.filter(id=device_id).first()
            if not device:
                return Response({"error": "Device topilmadi"}, status=404)

        else:
            device = Devices.objects.filter(user=user).first()
            if not device:
                return Response({"error": "Sizga biror device biriktirilmagan"}, status=400)

        employee_no = get_next_employee_no(device)

        begin, end = fix_hikvision_time(data["begin_time"], data["end_time"])

        payload = {
            "UserInfo": {
                "employeeNo": employee_no,
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

        result = HikvisionService.create_user(device, payload)
        if result.status_code != 200:
            return Response({"error": "Hikvision xatosi", "detail": result.text}, status=400)

        Employee.objects.create(
            device=device,
            employee_no=employee_no,
            name=data["name"],
            user_type=data.get("user_type"),
            door_right=data.get("door_right"),
            begin_time=data["begin_time"],
            end_time=data["end_time"],
        )

        return Response({
            "status": "created",
            "employee_no": employee_no,
            "device": device.ip
        })


@extend_schema(tags=["Employee"])
class EmployeeUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, employee_no):
        emp = Employee.objects.filter(employee_no=employee_no).first()
        if not emp:
            return Response({"error": "Topilmadi"}, status=404)

        if not request.user.is_superuser and not request.user.is_staff:
            if emp.device.user != request.user:
                return Response({"error": "Ruxsat yo‘q"}, status=403)

        ser = EmployeeUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        name = data.get("name", emp.name)
        user_type = data.get("user_type", emp.user_type)
        door_right = data.get("door_right", emp.door_right)
        begin = data.get("begin_time", emp.begin_time)
        end = data.get("end_time", emp.end_time)

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

        result = HikvisionService.update_user(emp.device, payload)
        if result.status_code != 200:
            return Response({"error": "Update failed", "detail": result.text}, status=400)

        emp.name = name
        emp.user_type = user_type
        emp.door_right = door_right
        emp.begin_time = begin
        emp.end_time = end
        emp.save()

        return Response({"status": "updated"})


@extend_schema(tags=["Employee"])
class EmployeeDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, employee_no):
        emp = Employee.objects.filter(employee_no=employee_no).first()
        if not emp:
            return Response({"error": "Not found"}, status=404)

        if not request.user.is_superuser and not request.user.is_staff:
            if emp.device.user != request.user:
                return Response({"error": "Ruxsat yo‘q"}, status=403)

        result = HikvisionService.delete_user(emp.device, employee_no)
        if result.status_code != 200:
            return Response({"error": "Delete failed", "detail": result.text}, status=400)

        emp.delete()

        return Response({"status": "deleted"})


@extend_schema(tags=["Employee"], parameters=[OpenApiParameter(name="date", type=str)])
class DailyAccessListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.GET.get("date")
        date_obj = parse_date(date_str) if date_str else now().date()

        user = request.user

        if user.is_superuser or user.is_staff:
            employees = Employee.objects.all()
        else:
            employees = Employee.objects.filter(device__user=user)

        results = []
        stats = {"total": employees.count(), "came": 0, "late": 0, "absent": 0}

        for emp in employees:
            first, last = get_first_last_events(emp.employee_no, date_obj)

            if first:
                stats["came"] += 1
            else:
                stats["absent"] += 1

            late_minutes = 0
            if emp.shift and first:
                shift_start = make_aware(datetime.combine(date_obj, emp.shift.start_time), UZ_TZ)
                if first.time > shift_start:
                    stats["late"] += 1
                    late_minutes = int((first.time - shift_start).total_seconds() / 60)

            results.append({
                "employee_no": emp.employee_no,
                "name": emp.name,
                "kirish": first.time.astimezone(UZ_TZ) if first else None,
                "chiqish": last.time.astimezone(UZ_TZ) if last else None,
                "late": format_late(late_minutes),
                "face": request.build_absolute_uri(emp.face_image.url) if emp.face_image else None
            })

        return Response({"date": str(date_obj), "employees": results, "stats": stats})


@extend_schema(tags=["DailyExel"], parameters=[OpenApiParameter(name="date", type=str)])
class DailyAccessExcelExport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.GET.get("date")
        date_obj = parse_date(date_str) if date_str else now().date()

        employees = Employee.objects.filter(device__user=request.user).select_related("shift")

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"{date_obj}"

        ws.append(["Employee No", "Name", "Kirish", "Chiqish", "Late", "Shift"])

        for emp in employees:
            first, last = get_first_last_events(emp.employee_no, date_obj)
            kirish = first.time.astimezone(UZ_TZ).strftime("%H:%M:%S") if first else ""
            chiqish = last.time.astimezone(UZ_TZ).strftime("%H:%M:%S") if last else ""

            late_text = ""
            if emp.shift and first:
                shift_start = make_aware(datetime.combine(date_obj, emp.shift.start_time), UZ_TZ)
                if first.time > shift_start:
                    diff = int((first.time - shift_start).total_seconds() / 60)
                    late_text = format_late(diff)

            shift_start = emp.shift.start_time.strftime("%H:%M") if emp.shift else ""

            ws.append([emp.employee_no, emp.name, kirish, chiqish, late_text, shift_start])

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
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
