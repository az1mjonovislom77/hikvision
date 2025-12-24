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
    http_method_names = ["get", "post", "put", "delete"]
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset

        if user.is_staff or user.role == User.UserRoles.SUPERADMIN:
            user_id = self.request.query_params.get("user_id")

            if user_id:
                if not User.objects.filter(id=user_id).exists():
                    raise ValidationError({"user_id": "Bunday user mavjud emas"})
                return queryset.filter(user_id=user_id)

            return queryset

        return queryset.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user

        if user.is_staff or user.role == User.UserRoles.SUPERADMIN:
            user_id = self.request.query_params.get("user_id")
            if not user_id:
                raise ValidationError({"user_id": "superadmin uchun majburiy"})
            target_user = User.objects.filter(id=user_id).first()
            if not target_user:
                raise ValidationError({"user_id": "Bunday user topilmadi"})
            serializer.save(user=target_user)
        else:
            serializer.save(user=user)
