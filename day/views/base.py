from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from utils.views.base import PartialPutMixin

User = get_user_model()


class BaseUserModelViewSet(PartialPutMixin, viewsets.ModelViewSet):
    http_method_names = ["get", "post", "put", "delete"]
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return self.queryset

        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        requested = self.request

        if requested.user.is_superuser or requested.user.is_staff:
            user_id = requested.data.get("user_id")
            if not user_id:
                raise ValueError("user_id admin uchun majburiy")

            user = User.objects.filter(id=user_id).first()
            if not user:
                raise ValueError("Bunday user_id mavjud emas")

            return serializer.save(user=user)

        return serializer.save(user=requested.user)
