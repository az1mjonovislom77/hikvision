from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


class PartialPutMixin:
    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class BaseUserViewSet(PartialPutMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.UserRoles.SUPERADMIN:
            return self.queryset
        return self.queryset.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user

        if user.is_staff or user.UserRoles.SUPERADMIN:
            user_id = self.request.data.get("user_id")
            if not user_id:
                raise ValidationError({"user_id": "superadmin uchun majburiy"})
            target_user = User.objects.filter(id=user_id).first()
            if not target_user:
                raise ValidationError({"user_id": "Bunday user topilmadi"})
            serializer.save(user=target_user)
        else:
            serializer.save(user=user)
