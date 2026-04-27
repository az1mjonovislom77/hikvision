from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from event.models import AccessEvent
from event.utils.fetch import fetch_face_events
from utils.models import Devices
from user.models import User


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
        since = timezone.datetime(2026, 4, 27, 8, 0, 0, tzinfo=timezone.get_current_timezone())
        payloads = []

        def fake_post(*args, **kwargs):
            payloads.append(kwargs["json"])
            if len(payloads) == 1:
                return DummyResponse(
                    200,
                    {
                        "AcsEvent": {
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
        self.assertEqual(payloads[0]["AcsEventCond"]["startTime"], "2026-04-27 08:00:00")

        event = AccessEvent.objects.get()
        self.assertEqual(event.major, 5)
        self.assertEqual(event.minor, 75)
        self.assertEqual(event.minor_name, "FaceRecognitionSuccess")
        self.assertEqual(event.employee_no, "E-1")
