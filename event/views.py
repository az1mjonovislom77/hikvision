from rest_framework.generics import ListAPIView
from rest_framework.pagination import PageNumberPagination
from event.serializers import AccessEventSerializer
from event.services.event_sync import EventSyncService


class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = None


class AccessEventList(ListAPIView):
    serializer_class = AccessEventSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        new_count = EventSyncService.sync_events()

        if new_count > 0:
            print(f"Yangi {new_count} ta event yuklandi")

        return EventSyncService.get_events_queryset()
