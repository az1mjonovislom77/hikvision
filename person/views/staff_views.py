import pytz
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets
from rest_framework.views import APIView
from event.models import AccessEvent
from person.models import Staff
from person.serializers import StaffSerializer
from utils.views import PartialPutMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.dateparse import parse_date

UZ_TZ = pytz.timezone("Asia/Shanghai")


@extend_schema(tags=['Staff'])
class StaffViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]
    pagination_class = None


@extend_schema(tags=['Staff'])
class DailyAccessListView(APIView):

    @extend_schema(
        summary="Berilgan sana bo‘yicha barcha xodimlar va ularning kirish/chiqish vaqtlarini qaytaradi",
        parameters=[OpenApiParameter(name="date", required=True, type=str, description="Format: YYYY-MM-DD", )])
    def get(self, request):

        date_str = request.GET.get("date")
        if not date_str:
            return Response({"error": "date kiritilmadi"}, status=400)

        date_obj = parse_date(date_str)
        if not date_obj:
            return Response({"error": "Sanani noto‘g‘ri formatda kiritdingiz"}, status=400)

        employee_set = set(AccessEvent.objects.values_list("employee_no", flat=True))

        result = []

        for emp_id in employee_set:
            name = (AccessEvent.objects.filter(employee_no=emp_id).values_list("name", flat=True).first())

            first_entry = AccessEvent.objects.filter(employee_no=emp_id, raw_json__label="Kirish",
                                                     time__date=date_obj).order_by("time").first()

            last_exit = AccessEvent.objects.filter(employee_no=emp_id, raw_json__label="Chiqish",
                                                   time__date=date_obj).order_by("-time").first()

            result.append(
                {"employee_no": emp_id,
                 "name": name,
                 "kirish_vaqti": first_entry.time.astimezone(UZ_TZ) if first_entry else None,
                 "chiqish_vaqti": last_exit.time.astimezone(UZ_TZ) if last_exit else None})

        return Response({"date": date_str, "employees": result})
