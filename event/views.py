import json
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import AccessEvent
from .serializers import AccessEventSerializer
from .utils.fetch import fetch_history_events
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from .utils.events_name import major_name, minor_name


class AccessEventList(APIView):
    def get(self, request):
        events = AccessEvent.objects.order_by('-time')[:200]
        serializer = AccessEventSerializer(events, many=True)
        return Response(serializer.data)


def load_hikvision_history(request):
    count = fetch_history_events()
    return JsonResponse({"saved": count})


@csrf_exempt
def hikvision_webhook(request):
    if request.method != 'POST':
        return JsonResponse({"status": "error", "detail": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body)
        events = data.get("Notification", {}).get("Event", [])

        for ev in events:
            serial = ev.get("serialNo")
            if not serial:
                continue

            if AccessEvent.objects.filter(serial_no=serial).exists():
                continue

            AccessEvent.objects.create(
                serial_no=serial,
                time=parse_datetime(ev.get("time")),
                major=ev.get("major"),
                minor=ev.get("minor"),
                major_name=major_name(ev.get("major")),
                minor_name=minor_name(ev.get("minor")),
                name=ev.get("name"),
                employee_no=ev.get("employeeNoString"),
                picture_url=ev.get("pictureURL"),
                raw_json=ev
            )
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "detail": str(e)}, status=400)
