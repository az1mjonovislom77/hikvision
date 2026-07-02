from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.utils import timezone

from event.models import AccessEvent
from utils.models import Devices, TelegramChannel
from utils.telegram.telegram import session, BASE_URL, send_telegram


class Command(BaseCommand):
    help = "Telegram real_time diagnostika: qurilmalar, kanallar, bot holati"

    def add_arguments(self, parser):
        parser.add_argument("--send-test", action="store_true", help="Har bir resolved kanalga test habar yuborish")

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write(f"NOW: {now}")

        self.stdout.write("\n=== QURILMALAR ===")
        for d in Devices.objects.all():
            last = AccessEvent.objects.filter(device=d).order_by("-time").first()
            unsent = AccessEvent.objects.filter(device=d, sent_to_telegram=False).count()
            cache_last = cache.get(f"last_event_time:{d.id}")
            lock = cache.get(f"hikvision:event-sync:{d.id}")
            self.stdout.write(
                f"device={d.id} name={d.name!r} ip={d.ip} status={d.status} user_id={d.user_id}"
            )
            self.stdout.write(
                f"   oxirgi_event={last.time if last else 'YO`Q'} | unsent={unsent} | cache_last={cache_last} | sync_lock={'BOR' if lock else 'yo`q'}"
            )
            channels = TelegramChannel.objects.filter(device=d)
            if not channels:
                self.stdout.write(self.style.ERROR("   ❌ Bu qurilmaga kanal biriktirilmagan!"))
            for c in channels:
                mark = "✅" if c.resolved_id else "❌ resolved_id YO`Q"
                self.stdout.write(f"   kanal id={c.id} name={c.name!r} resolved_id={c.resolved_id} {mark}")

        orphan = TelegramChannel.objects.filter(device__isnull=True)
        if orphan:
            self.stdout.write("\n=== QURILMASIZ KANALLAR (hech qachon ishlatilmaydi!) ===")
            for c in orphan:
                self.stdout.write(f"   id={c.id} name={c.name!r} resolved_id={c.resolved_id}")

        self.stdout.write("\n=== BOT HOLATI ===")
        try:
            r = session.get(f"{BASE_URL}/getWebhookInfo", timeout=15)
            info = r.json().get("result", {})
            self.stdout.write(f"webhook_url={info.get('url') or '(yo`q — getUpdates ishlaydi)'}")
            if info.get("url"):
                self.stdout.write(self.style.ERROR(
                    "❌ Botda WEBHOOK o`rnatilgan! getUpdates ishlamaydi → kanallar resolve bo`lmaydi.\n"
                    "   Yechim: curl 'https://api.telegram.org/bot<TOKEN>/deleteWebhook'"
                ))
            r = session.get(f"{BASE_URL}/getUpdates", params={"timeout": 0}, timeout=15)
            data = r.json()
            self.stdout.write(f"getUpdates ok={data.get('ok')} updates={len(data.get('result', []))}")
            if not data.get("ok"):
                self.stdout.write(self.style.ERROR(f"getUpdates xato: {data}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Bot API xato: {e}"))

        if options["send_test"]:
            self.stdout.write("\n=== TEST HABAR ===")
            for c in TelegramChannel.objects.filter(resolved_id__isnull=False):
                try:
                    send_telegram(chat_id=c.resolved_id, text=f"🔧 Test: {c.name} ({now:%H:%M:%S})")
                    self.stdout.write(self.style.SUCCESS(f"✅ {c.name} ({c.resolved_id}) — yuborildi"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ {c.name} ({c.resolved_id}) — {e}"))
