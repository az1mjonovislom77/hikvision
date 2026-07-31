from utils.models import Notification, User


class NotificationService:
    @staticmethod
    def resolve_users(user_ids):
        return User.objects.filter(id__in=user_ids) if user_ids else User.objects.all()

    @staticmethod
    def send_bulk(text, users):
        # list() — queryset'ni ikki marta (bulk_create va len uchun) so'ramaslik uchun.
        users = list(users)
        Notification.objects.bulk_create([Notification(user=u, text=text) for u in users])
        return len(users)
