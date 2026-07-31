from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils.timezone import localdate

from utils.models import Notification, Subscription


class Command(BaseCommand):
    help = "Obunasi 1 haftadan keyin tugaydigan userlarga notification yaratadi"

    def handle(self, *args, **kwargs):
        target_date = localdate() + timedelta(days=7)
        subscriptions = Subscription.objects.filter(end_date__date=target_date, is_active=True).select_related("user")

        notifications = [
            Notification(user=sub.user, text="⚠️ Obunangiz 1 haftadan keyin tugaydi.") for sub in subscriptions
        ]

        Notification.objects.bulk_create(notifications)
        self.stdout.write(self.style.SUCCESS(f"{len(notifications)} ta notification yaratildi"))
