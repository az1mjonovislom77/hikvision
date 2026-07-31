from utils.services.notifications import NotificationService
from utils.services.smartcity_daily_stats import SmartCityDailyStatsService
from utils.services.smartcity_stats import SmartCityStatsService
from utils.services.subscription import SubscriptionService


class SubscriptionAPIService:
    @staticmethod
    def create_from_serializer(*, serializer, request_user, user_id):
        target_user = SubscriptionService.resolve_target_user(request_user, user_id)
        plan = serializer.validated_data["plan"]
        return SubscriptionService.create_subscription(serializer=serializer, user=target_user, plan=plan)


class AdminNotificationAPIService:
    @staticmethod
    def send(*, text, user_ids):
        users = NotificationService.resolve_users(user_ids)
        NotificationService.send_bulk(text=text, users=users)


class SmartCityAPIService:
    @staticmethod
    def build_stats(*, time_filter):
        service = SmartCityStatsService(time_filter)
        return service.build()

    @staticmethod
    def build_daily_stats(*, date, mahalla):
        service = SmartCityDailyStatsService(date=date, mahalla_id=mahalla)
        return service.build()
