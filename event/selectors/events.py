from event.models import AccessEvent
from user.models import User
from utils.models import Devices


def get_target_user(*, user_id):
    return User.objects.filter(id=user_id).first()


def get_user_devices(*, user):
    return Devices.objects.filter(user=user)


def get_access_events_queryset():
    return AccessEvent.objects.select_related("device", "employee")

