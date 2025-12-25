from django.core.management.base import BaseCommand
from django.utils.timezone import localdate
from datetime import timedelta

from utils.models import Notification, Subscription


class Command(BaseCommand):
    help = "Obunasi 1 hafta ichida tugaydigan userlarga notification yaratadi"

    def handle(self, *args, **kwargs):
        target_date = localdate() + timedelta(days=7)

        subscriptions = Subscription.objects.filter(end_date__date=target_date, is_active=True, )

        notifications = [
            Notification(user=sub.user, text="⚠️ Obunangiz 1 hafta ichida tugaydi.")
            for sub in subscriptions
        ]

        Notification.objects.bulk_create(notifications)

        self.stdout.write(self.style.SUCCESS(f"{len(notifications)} ta notification yaratildi"))
