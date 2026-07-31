import logging

from event.selectors.events import get_target_user, get_user_devices
from event.services.event_sync import EventSyncService
from user.models import User

logger = logging.getLogger(__name__)


def truthy_param(val):
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("1", "true", "yes", "on")


class EventSyncAPIService:
    @staticmethod
    def resolve_devices(*, user, user_id):
        if user.role == User.UserRoles.SUPERADMIN or user.is_staff:
            if not user_id:
                logger.warning("event sync rejected: superadmin/staff request without user_id")
                return None, {"error": "user_id majburiy"}, 400

            target_user = get_target_user(user_id=user_id)
            if not target_user:
                logger.warning("event sync rejected: target user not found user_id=%s", user_id)
                return None, {"error": "User topilmadi"}, 404

            return get_user_devices(user=target_user), None, None

        return get_user_devices(user=user), None, None

    @staticmethod
    def sync(*, user, devices, full):
        device_info = list(devices.values("id", "name", "ip", "status"))
        logger.info("event sync devices resolved: user_id=%s full=%s devices=%s", user.id, full, device_info)

        total_saved = EventSyncService.sync_events(devices, full=full)
        logger.info(
            "event sync finished: user_id=%s full=%s total_saved=%s device_count=%s",
            user.id,
            full,
            total_saved,
            len(device_info),
        )

        return {
            "success": True,
            "added": total_saved,
            "deleted": 0,
            "full": full,
        }
