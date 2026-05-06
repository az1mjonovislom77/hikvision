from django.utils import timezone

from user.models import User
from utils.models import Subscription


def users_queryset():
    return User.objects.all()


def get_active_subscription(*, user):
    return (
        Subscription.objects
        .filter(user=user, is_active=True, end_date__gt=timezone.now())
        .select_related("plan")
        .first()
    )

