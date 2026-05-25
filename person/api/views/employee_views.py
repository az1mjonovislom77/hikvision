from datetime import datetime, time
from django.utils.dateparse import parse_date
from django.utils.timezone import localdate, make_aware
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from person.api.serializers import EmployeeCreateSerializer, EmployeeHistorySerializer, EmployeeSerializer, \
    EmployeeUpdateSerializer
from person.selectors.person import get_branch_employees, get_device, get_employee_with_device_user
from person.services.api import EmployeeAPIService, EmployeeHistoryService
from user.models import User


class EmployeePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })


@extend_schema(tags=['Employee'],
               parameters=[
                   OpenApiParameter(name="branch_id", type=int, description="Branch ID (majburiy)", required=True),
                   OpenApiParameter(name="user_id", type=int, required=False, description="Faqat superadmin uchun")
               ])
class EmployeeSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        branch_id = request.query_params.get("branch_id")

        if not branch_id:
            return Response({"error": "branch_id majburiy"}, status=400)

        branch, error, status_code = EmployeeAPIService.resolve_branch(
            user=request.user,
            branch_id=branch_id,
            user_id=request.query_params.get("user_id"),
        )
        if error:
            return Response(error, status=status_code)

        if not branch:
            return Response({"error": "Branch topilmadi yoki sizga tegishli emas"}, status=400)

        if not branch.device_id:
            return Response({"error": "Ushbu branch uchun device topilmadi"}, status=400)

        return Response(EmployeeAPIService.sync_branch_devices(branch=branch))


@extend_schema(tags=['Employee'],
               parameters=[
                   OpenApiParameter(name="branch_id", type=int, description="Branch ID (majburiy)", required=True),
                   OpenApiParameter(name="user_id", type=int, required=False, description="Faqat superadmin uchun")
               ])
class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmployeeSerializer

    def get(self, request):
        branch_id = request.query_params.get("branch_id")

        if not branch_id:
            return Response({"error": "branch_id majburiy"}, status=400)

        branch, error, status_code = EmployeeAPIService.resolve_branch(
            user=request.user,
            branch_id=branch_id,
            user_id=request.query_params.get("user_id"),
        )
        if error:
            return Response(error, status=status_code)

        if not branch:
            return Response({"error": "Branch topilmadi yoki sizga tegishli emas"}, status=400)

        employees = get_branch_employees(branch=branch)
        serializer = EmployeeSerializer(employees, many=True, context={"request": request})
        return Response(serializer.data)


@extend_schema(tags=["Employee"], responses={200: EmployeeSerializer})
class EmployeeDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmployeeSerializer

    def get(self, request, employee_id):
        emp = get_employee_with_device_user(employee_id=employee_id)
        if not emp:
            return Response({"error": "Topilmadi"}, status=404)

        if not request.user.UserRoles.SUPERADMIN and not request.user.is_staff:
            if emp.device.user != request.user:
                return Response({"error": "Ruxsat yoвЂq"}, status=403)

        serializer = EmployeeSerializer(emp, context={"request": request})
        return Response(serializer.data)


@extend_schema(tags=["Employee"])
class EmployeeCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=EmployeeCreateSerializer)
    def post(self, request):
        ser = EmployeeCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        device_id = request.data.get("device_id")

        if not device_id:
            return Response({"error": "device_id majburiy"}, status=400)

        if request.user.role == User.UserRoles.SUPERADMIN or request.user.is_staff:
            device = get_device(device_id=device_id)
        else:
            device = get_device(device_id=device_id, user=request.user)

        if not device:
            return Response({"error": "Device topilmadi yoki sizga tegishli emas"}, status=400)

        payload, error, status_code = EmployeeAPIService.create_employee(data=ser.validated_data, device=device)
        if error:
            return Response(error, status=status_code)

        return Response(payload)


@extend_schema(tags=["Employee"])
class EmployeeUpdateView(APIView):
    serializer_class = EmployeeUpdateSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request, employee_id):
        emp = get_employee_with_device_user(employee_id=employee_id)
        if not emp:
            return Response({"error": "Topilmadi"}, status=404)

        if not request.user.UserRoles.SUPERADMIN and not request.user.is_staff:
            if emp.device.user != request.user:
                return Response({"error": "Ruxsat yoвЂq"}, status=403)

        serializer = EmployeeUpdateSerializer(emp, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        payload, status_code = EmployeeAPIService.update_employee(employee=emp, serializer=serializer)
        if status_code:
            return Response(payload, status=status_code)

        return Response(payload)


@extend_schema(tags=["Employee"])
class EmployeeDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, employee_id):
        emp = get_employee_with_device_user(employee_id=employee_id)
        if not emp:
            return Response({"error": "Not found"}, status=404)

        if not request.user.UserRoles.SUPERADMIN and not request.user.is_staff:
            if emp.device.user != request.user:
                return Response({"error": "Ruxsat yoвЂq"}, status=403)

        payload, status_code = EmployeeAPIService.delete_employee(employee=emp)
        if status_code:
            return Response(payload, status=status_code)

        return Response(payload)


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
        employee_id = self.request.query_params.get("employee_id")
        date_str = self.request.query_params.get("date")
        date = parse_date(date_str) if date_str else localdate()

        start = make_aware(datetime.combine(date, time.min))
        end = make_aware(datetime.combine(date, time.max))
        employee = get_employee_with_device_user(employee_id=employee_id)

        return EmployeeHistoryService.build_queryset(
            user=self.request.user,
            employee=employee,
            employee_id=employee_id,
            start=start,
            end=end,
        )
