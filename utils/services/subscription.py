from django.utils import timezone
from dateutil.relativedelta import relativedelta
from utils.models import Subscription, User


class SubscriptionService:

    @staticmethod
    def resolve_target_user(request_user, user_id):
        if request_user.is_staff or request_user.role == request_user.UserRoles.SUPERADMIN:
            return User.objects.get(id=user_id)
        return request_user

    @staticmethod
    def deactivate_previous(user):
        Subscription.objects.filter(user=user, is_active=True).update(is_active=False)

    @staticmethod
    def create_subscription(serializer, user, plan):
        start = timezone.now()
        end = start + relativedelta(months=plan.duration_months)

        SubscriptionService.deactivate_previous(user)

        serializer.save(user=user, start_date=start, end_date=end, is_active=True, is_paid=True, )

        return serializer.instance
