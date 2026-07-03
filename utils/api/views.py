from django.http import HttpResponse
from rest_framework import status
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from utils.services.monthly_export import AttendanceExcelExportService
from utils.utils.schema import user_extend_schema
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from utils.base.views_base import BaseUserViewSet, ReadWriteSerializerMixin
from utils.api.serializers import DevicesSerializer, TelegramChannelSerializer, \
    BranchGetSerializer, BranchCreateSerializer, DepartmentCreateSerializer, DepartmentGetSerializer, \
    PlanSerializer, SubscriptionCreateSerializer, SubscriptionDetailSerializer, NotificationSerializer, \
    AdminNotificationSerializer
from utils.selectors.utils import branch_queryset, department_queryset, devices_queryset, notification_queryset, \
    notification_queryset_for_user, plan_queryset, subscription_queryset, telegram_channel_queryset, \
    get_monthly_report_for_excel
from utils.services.api import AdminNotificationAPIService, SmartCityAPIService, SubscriptionAPIService


@user_extend_schema("Devices")
class DevicesViewSet(BaseUserViewSet):
    queryset = devices_queryset()
    serializer_class = DevicesSerializer


@user_extend_schema("Department")
class DepartmentViewSet(ReadWriteSerializerMixin, BaseUserViewSet):
    queryset = department_queryset()
    write_serializer = DepartmentCreateSerializer
    read_serializer = DepartmentGetSerializer


@user_extend_schema("Branch")
class BranchViewSet(ReadWriteSerializerMixin, BaseUserViewSet):
    queryset = branch_queryset()
    write_serializer = BranchCreateSerializer
    read_serializer = BranchGetSerializer


@extend_schema(tags=['TelegramChannel'],
               parameters=[
                   OpenApiParameter(name="branch_id", type=int, required=True),
                   OpenApiParameter(name="user_id", type=int, required=False, description="Faqat superadmin uchun")
               ])
class TelegramChannelViewSet(BaseUserViewSet):
    queryset = telegram_channel_queryset()
    serializer_class = TelegramChannelSerializer


@extend_schema(tags=["Plan"])
class PlanViewSet(viewsets.ModelViewSet):
    queryset = plan_queryset()
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]
    http_method_names = ["get", "post", "put", "delete"]
    pagination_class = None


@user_extend_schema("Subscription")
class SubscriptionViewSet(BaseUserViewSet):
    queryset = subscription_queryset()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return SubscriptionCreateSerializer
        return SubscriptionDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = SubscriptionAPIService.create_from_serializer(
            serializer=serializer, request_user=request.user, user_id=request.query_params.get("user_id"))
        response = SubscriptionDetailSerializer(subscription, context=self.get_serializer_context())

        return Response(response.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Notification"])
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    queryset = notification_queryset()
    pagination_class = None

    def get_queryset(self):
        return notification_queryset_for_user(user=self.request.user)


@extend_schema(tags=["Notification"])
class AdminNotificationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminNotificationSerializer

    def create(self, request):
        text = request.data.get("text")
        user_ids = request.data.get("user_ids")

        if not text:
            return Response({"text": "Majburiy"}, status=status.HTTP_400_BAD_REQUEST)

        AdminNotificationAPIService.send(text=text, user_ids=user_ids)

        return Response({"detail": "Notification yuborildi"}, status=status.HTTP_201_CREATED)


@extend_schema(tags=["SmartCityStats"], parameters=[OpenApiParameter(name="timeFilter", type=str)])
class SmartCityAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        time_filter = request.GET.get("timeFilter", "week")

        try:
            data = SmartCityAPIService.build_stats(time_filter=time_filter)
        except ValueError:
            return Response({"success": False, "message": "Invalid timeFilter"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "success": True,
                "message": "Data fetched successfully",
                "data": data,
            }, status=status.HTTP_200_OK)


@extend_schema(
    tags=["SmartCityDaily"],
    parameters=[
        OpenApiParameter(name="date", type=str, required=True),
        OpenApiParameter(name="mahalla", type=int, required=False),
    ]
)
class SmartCityDailyAPIView(APIView):

    def get(self, request):
        date = request.GET.get("date")
        mahalla = request.GET.get("mahalla")

        if not date:
            return Response({"success": False, "message": "date parameter is required"},
                            status=status.HTTP_400_BAD_REQUEST)

        if mahalla is not None:
            try:
                mahalla = int(mahalla)
            except ValueError:
                return Response({"success": False, "message": "mahalla must be integer"},
                                status=status.HTTP_400_BAD_REQUEST)

        try:
            data = SmartCityAPIService.build_daily_stats(date=date, mahalla=mahalla)

        except ValueError as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "success": True,
                "message": "Daily stats fetched successfully",
                "data": data
            }, status=status.HTTP_200_OK
        )


class MonthlyAttendanceExcelExportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Attendance"],
        parameters=[
            OpenApiParameter(name="branch_id", type=int, location=OpenApiParameter.QUERY, required=True),
            OpenApiParameter(name="year", type=int, location=OpenApiParameter.QUERY, required=True),
            OpenApiParameter(name="month", type=int, location=OpenApiParameter.QUERY, required=True),
            OpenApiParameter(name="employee_id", type=int, location=OpenApiParameter.QUERY, required=False)])
    def get(self, request):
        branch_id = request.GET.get("branch_id")
        year = request.GET.get("year")
        month = request.GET.get("month")
        employee_id = request.GET.get("employee_id")

        if not branch_id:
            return HttpResponse("branch_id required", status=400)

        if not year or not month:
            return HttpResponse("year and month required", status=400)

        report = get_monthly_report_for_excel(
            user=request.user, branch_id=branch_id, year=int(year), month=int(month), employee_id=employee_id)

        if not report:
            return HttpResponse("Branch not found", status=400)

        return AttendanceExcelExportService.generate_monthly_excel(
            report=report, year=int(year), month=int(month))
