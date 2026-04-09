import uuid
from user.models import User
from rest_framework import status
from datetime import datetime, time
from event.models import AccessEvent
from rest_framework.views import APIView
from utils.models import Devices, Branch
from person.utils import fix_hikvision_time
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from rest_framework.generics import ListAPIView
from person.models import Employee, EmployeeHistory
from person.services.employee import EmployeeService
from person.services.hikvision import HikvisionService
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import localdate, make_aware
from drf_spectacular.utils import extend_schema, OpenApiParameter
from person.serializers import EmployeeSerializer, EmployeeCreateSerializer, EmployeeUpdateSerializer, \
    EmployeeHistorySerializer


@extend_schema(tags=['Employee'],
               parameters=[
                   OpenApiParameter(name="branch_id", type=int, description="Branch ID (majburiy)", required=True),
                   OpenApiParameter(name="user_id", type=int, required=False, description="Faqat superadmin uchun")
               ])
class EmployeeSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        branch_id = request.query_params.get("branch_id")

        if not branch_id:
            return Response({"error": "branch_id majburiy"}, status=400)

        if user.role == User.UserRoles.SUPERADMIN or user.is_staff:
            user_id = request.query_params.get("user_id")

            if not user_id:
                return Response({"error": "user_id superadmin uchun majburiy"}, status=400)

            target_user = User.objects.filter(id=user_id).first()
            if not target_user:
                return Response({"error": "Bunday user topilmadi"}, status=404)

            branch = Branch.objects.filter(id=branch_id, user=target_user).first()
        else:
            branch = Branch.objects.filter(id=branch_id, user=user).first()

        if not branch:
            return Response({"error": "Branch topilmadi yoki sizga tegishli emas"}, status=400)

        devices = Devices.objects.filter(id=branch.device_id)

        if not branch.device_id:
            return Response({"error": "Ushbu branch uchun device topilmadi"}, status=400)

        total_stats = {
            "synced_devices": 0,
            "added": 0,
            "deleted": 0,
        }

        for device in devices:
            stats = EmployeeService.sync_from_hikvision(device)

            total_stats["synced_devices"] += 1
            total_stats["added"] += stats["added"]
            total_stats["deleted"] += stats["deleted"]

        return Response({"success": True, **total_stats})


@extend_schema(tags=['Employee'],
               parameters=[
                   OpenApiParameter(name="branch_id", type=int, description="Branch ID (majburiy)", required=True),
                   OpenApiParameter(name="user_id", type=int, required=False, description="Faqat superadmin uchun")
               ])
class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmployeeSerializer

    def get(self, request):
        user = request.user
        branch_id = request.query_params.get("branch_id")

        if not branch_id:
            return Response({"error": "branch_id majburiy"}, status=400)

        if user.role == User.UserRoles.SUPERADMIN or user.is_staff:
            user_id = request.query_params.get("user_id")

            if not user_id:
                return Response({"error": "user_id superadmin uchun majburiy"}, status=400)

            target_user = User.objects.filter(id=user_id).first()
            if not target_user:
                return Response({"error": "Bunday user topilmadi"}, status=404)

            branch = Branch.objects.filter(id=branch_id, user=target_user).first()

        else:
            branch = Branch.objects.filter(id=branch_id, user=user).first()

        if not branch:
            return Response({"error": "Branch topilmadi yoki sizga tegishli emas"}, status=400)

        employees = (Employee.objects
                     .filter(device=branch.device)
                     .select_related("device"))

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
        device_id = request.data.get("device_id")

        if not device_id:
            return Response({"error": "device_id majburiy"}, status=400)

        if user.role == User.UserRoles.SUPERADMIN or user.is_staff:
            device = Devices.objects.filter(id=device_id).first()
        else:
            device = Devices.objects.filter(id=device_id, user=user).first()

        if not device:
            return Response({"error": "Device topilmadi yoki sizga tegishli emas"}, status=400)

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
        import time
        time.sleep(3)
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
    pagination_class = None

    def list(self, request, *args, **kwargs):
        if not request.query_params.get("employee_id"):
            return Response({"error": "employee_id majburiy"}, status=status.HTTP_400_BAD_REQUEST)
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        employee_id = self.request.query_params.get("employee_id")
        date_str = self.request.query_params.get("date")

        date = parse_date(date_str) if date_str else localdate()

        start = make_aware(datetime.combine(date, time.min))
        end = make_aware(datetime.combine(date, time.max))

        employee = Employee.objects.select_related("device__user").filter(id=employee_id).first()
        if not employee:
            return EmployeeHistory.objects.none()

        if not user.role == User.UserRoles.SUPERADMIN and not user.is_staff:
            if employee.device.user != user:
                return EmployeeHistory.objects.none()

        qs = (EmployeeHistory.objects
              .filter(employee_id=employee_id, event_time__range=(start, end))
              .select_related("event", "employee"))

        if not qs.exists():

            events = list(AccessEvent.objects
                          .filter(employee_no=employee.employee_no, time__range=(start, end))
                          .only("id", "time", "label_name"))

            existing_event_ids = set(
                EmployeeHistory.objects.filter(
                    employee=employee,
                    event_id__in=[e.id for e in events]).values_list("event_id", flat=True))

            to_create = []

            for ev in events:
                if ev.id not in existing_event_ids:
                    to_create.append(
                        EmployeeHistory(employee=employee, event=ev, event_time=ev.time, label_name=ev.label_name))

            if to_create:
                EmployeeHistory.objects.bulk_create(to_create)

            qs = (EmployeeHistory.objects
                  .filter(employee_id=employee_id, event_time__range=(start, end))
                  .select_related("event", "employee"))

        return qs.order_by("-event_time")
