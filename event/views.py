import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from .models import AccessEvent
from .serializers import AccessEventSerializer
from .utils.fetch import fetch_face_events
from .utils.events_name import major_name, minor_name
from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from datetime import timedelta


class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = None


class AccessEventList(ListAPIView):
    serializer_class = AccessEventSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        latest = AccessEvent.objects.filter(major=5, minor=75).order_by('-time').first()
        since_time = None
        if latest:
            since_time = latest.time - timedelta(seconds=5)
        new_count = fetch_face_events(since=since_time)

        if new_count > 0:
            print(f"Yangi {new_count} ta event avtomatik yuklandi")

        return AccessEvent.objects.filter(major=5, minor=75).order_by('-time')


@csrf_exempt
def hikvision_webhook(request):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "detail": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)
        events = data.get("Notification", {}).get("Event", [])

        for ev in events:
            event_time = parse_datetime(ev.get("time"))
            event_major = ev.get("major")
            event_minor = ev.get("minor")

            if AccessEvent.objects.filter(time=event_time, major=event_major, minor=event_minor).exists():
                continue

            AccessEvent.objects.create(
                serial_no=ev.get("serialNo"),
                time=event_time,
                major=event_major,
                minor=event_minor,
                major_name=major_name(event_major),
                minor_name=minor_name(event_minor),
                name=ev.get("name"),
                employee_no=ev.get("employeeNoString"),
                picture_url=ev.get("pictureURL"),
                raw_json=ev
            )

        return JsonResponse({"status": "ok"})

    except Exception as e:
        return JsonResponse({"status": "error", "detail": str(e)}, status=400)
