from datetime import datetime
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from event.models import AccessEvent
from event.services.telegram_send import build_message, send_event
from event.utils.fetch import fetch_face_events
from person.models import Employee
from user.models import User
from utils.models import Devices, TelegramChannel


class DummyResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


class FetchFaceEventsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone_number="998901234567", password="secret123")
        self.device = Devices.objects.create(
            user=self.user,
            name="Main door",
            ip="192.168.1.10",
            username="admin",
            password="12345",
            status=Devices.Status.ACTIVE,
        )

    @patch("event.utils.fetch.time.sleep", return_value=None)
    @patch("event.utils.fetch.requests.post")
    def test_since_map_is_sent_as_start_time_and_real_minor_is_saved(self, mock_post, _mock_sleep):
        since = datetime(2026, 4, 27, 8, 0, 0, tzinfo=timezone.get_current_timezone())
        payloads = []

        def fake_post(*args, **kwargs):
            payloads.append(kwargs["json"])
            if len(payloads) == 1:
                return DummyResponse(
                    200,
                    {
                        "AcsEvent": {
                            "responseStatusStrg": "OK",
                            "numOfMatches": 1,
                            "totalMatches": 1,
                            "InfoList": [
                                {
                                    "serialNo": "abc-1",
                                    "time": "2026-04-27T08:05:00+05:00",
                                    "major": 5,
                                    "minor": 75,
                                    "employeeNoString": "E-1",
                                    "labelName": "KIRISH",
                                    "name": "Granted",
                                    "pictureURL": "http://image.local/1.jpg",
                                }
                            ]
                        }
                    },
                )

            return DummyResponse(200, {"AcsEvent": {"InfoList": []}})

        mock_post.side_effect = fake_post

        saved = fetch_face_events([self.device], since_map={self.device.id: since})

        self.assertEqual(saved, 1)
        self.assertEqual(len(payloads), 1)
        self.assertEqual(payloads[0]["AcsEventCond"]["major"], 5)
        self.assertEqual(payloads[0]["AcsEventCond"]["minor"], 75)
        self.assertEqual(payloads[0]["AcsEventCond"]["startTime"], "2026-04-27T08:00:00+05:00")
        self.assertIn("endTime", payloads[0]["AcsEventCond"])

        event = AccessEvent.objects.get()
        self.assertEqual(event.major, 5)
        self.assertEqual(event.minor, 75)
        self.assertEqual(event.minor_name, "FaceRecognitionSuccess")
        self.assertEqual(event.employee_no, "E-1")


class TelegramSendTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(phone_number="998906000001", password="pass")
        self.device = Devices.objects.create(
            user=self.user,
            name="Door",
            ip="192.168.1.20",
            username="admin",
            password="12345",
            status=Devices.Status.ACTIVE,
        )
        self.employee = Employee.objects.create(device=self.device, employee_no="T1", name="Tg Employee")

    def _create_event(self, label="KIRISH", serial="tg-1", employee="default"):
        return AccessEvent.objects.create(
            employee=self.employee if employee == "default" else employee,
            serial_no=serial,
            time=timezone.now(),
            major=5,
            minor=75,
            major_name="m",
            minor_name="n",
            name="Tg Employee",
            employee_no="T1",
            picture_url="",
            raw_json={"labelName": label},
            device=self.device,
            label_name=label,
        )

    def test_build_message_direction_kirish(self):
        msg = build_message(self._create_event("KIRISH", "d-1"))
        self.assertIn("KIRISH", msg)
        self.assertIn("Tg Employee", msg)

    def test_build_message_direction_chiqish(self):
        self.assertIn("CHIQISH", build_message(self._create_event("chiqish", "d-2")))

    def test_build_message_direction_unknown(self):
        self.assertIn("NOMA", build_message(self._create_event("boshqa", "d-3")))

    @patch("event.services.telegram_send.time.sleep", return_value=None)
    @patch("event.services.telegram_send.download_image", return_value=None)
    @patch("event.services.telegram_send.send_telegram")
    def test_send_event_success_marks_sent(self, mock_send, _mock_dl, _mock_sleep):
        TelegramChannel.objects.create(
            user=self.user, device=self.device, name="ch", chat_id="@ch", resolved_id="-100123"
        )
        event = self._create_event(serial="tg-s1")

        self.assertTrue(send_event(event))

        event.refresh_from_db()
        self.assertTrue(event.sent_to_telegram)
        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args.kwargs["chat_id"], "-100123")

    @patch("event.services.telegram_send.send_telegram")
    def test_send_event_no_channels_marks_sent_returns_false(self, mock_send):
        event = self._create_event(serial="tg-s2")

        self.assertFalse(send_event(event))

        event.refresh_from_db()
        self.assertTrue(event.sent_to_telegram)
        mock_send.assert_not_called()

    @patch("event.services.telegram_send.time.sleep", return_value=None)
    @patch("event.services.telegram_send.download_image", return_value=None)
    @patch("event.services.telegram_send.send_telegram", side_effect=RuntimeError("boom"))
    def test_send_event_all_channels_fail_keeps_unsent(self, _mock_send, _mock_dl, _mock_sleep):
        TelegramChannel.objects.create(
            user=self.user, device=self.device, name="ch", chat_id="@ch", resolved_id="-100123"
        )
        event = self._create_event(serial="tg-s3")

        self.assertFalse(send_event(event))

        event.refresh_from_db()
        self.assertFalse(event.sent_to_telegram)

    @patch("event.services.telegram_send.send_telegram")
    def test_send_event_without_employee_marks_sent(self, mock_send):
        event = self._create_event(serial="tg-s4", employee=None)

        self.assertFalse(send_event(event))

        event.refresh_from_db()
        self.assertTrue(event.sent_to_telegram)
        mock_send.assert_not_called()
