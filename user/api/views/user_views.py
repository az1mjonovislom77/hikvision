from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from user.api.serializers.user_serializers import UserCreateSerializer, UserDetailSerializer
from user.selectors.user import users_queryset
from utils.base.permissions import is_admin
from utils.base.views_base import PartialPutMixin


@extend_schema(tags=["User"])
class UserViewSet(PartialPutMixin, viewsets.ModelViewSet):
    queryset = users_queryset()
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "put", "delete"]
    pagination_class = None

    def get_queryset(self):
        if is_admin(self.request.user):
            return users_queryset()
        return users_queryset().filter(id=self.request.user.id)

    def destroy(self, request, *args, **kwargs):
        if not is_admin(request.user):
            return Response({"detail": "Ruxsat yo'q"}, status=403)
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action == ["retrieve"]:
            return UserDetailSerializer
        return UserCreateSerializer
