from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

User = get_user_model()


class PartialPutMixin:
    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


class BaseUserViewSet(PartialPutMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        if self.request.user.UserRoles.SUPERADMIN or self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        request = self.request

        if request.user.UserRoles.SUPERADMIN or request.user.is_staff:
            user_id = request.data.get("user_id")
            if not user_id:
                raise ValueError("user_id admin uchun majburiy")
            user = User.objects.filter(id=user_id).first()
            if not user:
                raise ValueError("Bunday user_id topilmadi")
            serializer.save(user=user)
        else:
            serializer.save(user=request.user)
