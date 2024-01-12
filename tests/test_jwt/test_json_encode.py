import json
from datetime import datetime
from uuid import uuid4

from django.test import TestCase

from ninja_simple_jwt.jwt.json_encode import TokenUserEncoder


class TestDjangoUserEncoder(TestCase):
    def test_encoder_can_serialize_datetime(self) -> None:
        test_data = datetime(2012, 1, 14, 12, 0, 1)

        result = json.dumps(test_data, cls=TokenUserEncoder)

        self.assertEqual('"2012-01-14T12:00:01"', result)

    def test_encoder_can_serialize_uuid(self) -> None:
        test_uuid = uuid4()

        result = json.dumps(test_uuid, cls=TokenUserEncoder)

        self.assertEqual(f'"{str(test_uuid)}"', result)
