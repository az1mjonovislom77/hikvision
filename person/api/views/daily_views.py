from django.http import HttpResponse
from django.utils.dateparse import parse_date
from django.utils.timezone import localdate, now
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from person.services.api import DailyAccessAPIService


def get_request_date(request):
    date_str = request.GET.get("date")
    return parse_date(date_str) if date_str else localdate()


@extend_schema(
    tags=["Employee"],
    parameters=[
        OpenApiParameter(name="date", type=str),
        OpenApiParameter(name="branch_id", type=int),
    ],
)
class DailyAccessListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_obj = get_request_date(request)
        branch_id = request.GET.get("branch_id")

        return Response(DailyAccessAPIService.list_payload(
            user=request.user,
            branch_id=branch_id,
            date_obj=date_obj,
            request=request,
        ))


@extend_schema(tags=["DailyExel"], parameters=[OpenApiParameter(name="date", type=str)])
class DailyAccessExcelExport(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_str = request.GET.get("date")
        date_obj = parse_date(date_str) if date_str else now().date()
        content = DailyAccessAPIService.excel_bytes(user=request.user, date_obj=date_obj)

        return HttpResponse(
            content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="daily_{date_obj}.xlsx"'}
        )

