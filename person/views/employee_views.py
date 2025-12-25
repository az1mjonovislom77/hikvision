import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.permissions import IsAuthenticated
from person.models import Employee, EmployeeHistory
from user.models import User
from utils.models import Devices
from person.serializers import (EmployeeSerializer, EmployeeCreateSerializer, EmployeeUpdateSerializer,
                                EmployeeHistorySerializer)
from person.utils import fix_hikvision_time
from person.services.hikvision import HikvisionService
from person.services.employee import EmployeeService
from rest_framework.generics import ListAPIView
from django.utils.timezone import localdate
from rest_framework import status
from utils.utils.schema import user_extend_schema


@user_extend_schema("Employee")
class EmployeeSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.role == User.UserRoles.SUPERADMIN or user.is_staff:
            user_id = request.query_params.get("user_id")

            if not user_id:
                return Response({"error": "user_id superadmin uchun majburiy"}, status=400)

            target_user = User.objects.filter(id=user_id).first()
            if not target_user:
                return Response({"error": "Bunday user topilmadi"}, status=404)

            devices = Devices.objects.filter(user=target_user)
        else:
            devices = Devices.objects.filter(user=user)

        if not devices.exists():
            return Response({"error": "Ushbu userga device biriktirilmagan"}, status=400)

        total_stats = {"synced_devices": 0, "added": 0, "deleted": 0, }

        for device in devices:
            hk_users = HikvisionService.search_users(device)
            stats = EmployeeService.sync_from_hikvision(device, hk_users)

            total_stats["synced_devices"] += 1
            total_stats["added"] += stats["added"]
            total_stats["deleted"] += stats["deleted"]

        return Response({"success": True, **total_stats})


@user_extend_schema("Employee")
class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmployeeSerializer

    def get(self, request):
        user = request.user

        if user.role == User.UserRoles.SUPERADMIN or user.is_staff:
            user_id = request.GET.get("user_id")
            if not user_id:
                return Response({"error": "user_id superadmin uchun majburiy"}, status=400)

            target_user = User.objects.filter(id=user_id).first()
            if not target_user:
                return Response({"error": "Bunday user topilmadi"}, status=404)

            employees = Employee.objects.filter(device__user=target_user)

        else:
            employees = Employee.objects.filter(device__user=user)

        serializer = EmployeeSerializer(employees, many=True, context={"request": request})

        return Response(serializer.data)


@extend_schema(tags=["Employee"], responses={200: EmployeeSerializer})
class EmployeeDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmployeeSerializer

    def get(self, request, employee_id):
        emp = Employee.objects.select_related("device__user").filter(id=employee_id).first()
        if not emp:
            return Response({"error": "Topilmadi"}, status=404)

        if not request.user.UserRoles.SUPERADMIN and not request.user.is_staff:
            if emp.device.user != request.user:
                return Response({"error": "Ruxsat yo‘q"}, status=403)

        serializer = EmployeeSerializer(emp, context={"request": request})
        return Response(serializer.data)


@extend_schema(tags=["Employee"])
class EmployeeCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=EmployeeCreateSerializer)
    def post(self, request):
        ser = EmployeeCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        user = request.user

        if user.role == User.UserRoles.SUPERADMIN or user.is_staff:
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

        employee_no = uuid.uuid4().hex[:16]

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

        employee = Employee.objects.create(**data, device=device, employee_no=employee_no)

        return Response({"status": "created", "employee_no": employee_no, "id": employee.id, "device": device.ip})


@extend_schema(tags=["Employee"])
class EmployeeUpdateView(APIView):
    serializer_class = EmployeeUpdateSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request, employee_id):
        emp = Employee.objects.select_related("device__user").filter(id=employee_id).first()
        if not emp:
            return Response({"error": "Topilmadi"}, status=404)

        if not request.user.UserRoles.SUPERADMIN and not request.user.is_staff:
            if emp.device.user != request.user:
                return Response({"error": "Ruxsat yo‘q"}, status=403)

        serializer = EmployeeUpdateSerializer(emp, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        name = data.get("name", emp.name)
        user_type = data.get("user_type", emp.user_type)
        door_right = data.get("door_right", emp.door_right)
        begin = data.get("begin_time", emp.begin_time)
        end = data.get("end_time", emp.end_time)

        begin_str, end_str = fix_hikvision_time(begin, end)

        payload = {
            "UserInfo": {
                "employeeNo": emp.employee_no,
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

        serializer.save()

        return Response({"status": "updated"})


@extend_schema(tags=["Employee"])
class EmployeeDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, employee_id):
        emp = Employee.objects.select_related("device__user").filter(id=employee_id).first()
        if not emp:
            return Response({"error": "Not found"}, status=404)

        if not request.user.UserRoles.SUPERADMIN and not request.user.is_staff:
            if emp.device.user != request.user:
                return Response({"error": "Ruxsat yo‘q"}, status=403)

        result = HikvisionService.delete_user(emp.device, emp.employee_no)
        if result.status_code != 200:
            return Response({"error": "Delete failed", "detail": result.text}, status=400)

        emp.delete()
        return Response({"status": "deleted"})


@extend_schema(
    tags=["Employee"],
    parameters=[
        OpenApiParameter(name="employee_id", type=int, required=True),
        OpenApiParameter(name="date", type=str, required=False, description="Sana (YYYY-MM-DD)."),
    ], responses={200: EmployeeHistorySerializer(many=True)}
)
class EmployeeHistoryListView(ListAPIView):
    serializer_class = EmployeeHistorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # pagination yo‘q

    def list(self, request, *args, **kwargs):
        if not request.query_params.get("employee_id"):
            return Response({"error": "employee_id majburiy"}, status=status.HTTP_400_BAD_REQUEST)
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        employee_id = self.request.query_params.get("employee_id")
        date = self.request.query_params.get("date")

        if not date:
            date = localdate()

        qs = EmployeeHistory.objects.filter(employee_id=employee_id, event_time__date=date)

        if not user.role == User.UserRoles.SUPERADMIN and not user.is_staff:
            user_devices = Devices.objects.filter(user=user)
            if not Employee.objects.filter(id=employee_id, device__in=user_devices).exists():
                return EmployeeHistory.objects.none()

        return qs.order_by("-event_time")

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
