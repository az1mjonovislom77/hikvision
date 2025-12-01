import json
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from .models import AccessEvent
from .serializers import AccessEventSerializer
from .utils.fetch import fetch_face_events
from .utils.events_name import major_name, minor_name


class AccessEventList(APIView):
    def get(self, request, *args, **kwargs):
        try:
            fetched_count = fetch_face_events()
            events = AccessEvent.objects.filter(major=5, minor=75).order_by('-time')
            serializer = AccessEventSerializer(events, many=True)

            return Response({
                "fetched": fetched_count,
                "total": events.count(),
                "events": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
