from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from utils.views import PartialPutMixin


class BaseUserModelViewSet(PartialPutMixin, viewsets.ModelViewSet):
    http_method_names = ["get", "post", "put", "delete"]
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
