import warnings
from typing import Any
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from ninja_simple_jwt.settings import DEFAULTS


class TestMakeJwtKeyCommand(TestCase):
    @staticmethod
    def merge_settings(**kwargs: Any) -> dict:
        return {**DEFAULTS, **kwargs}

    def test_creates_key_pair_with_default_rs256(self) -> None:
        call_command("make_jwt_key")

    def test_creates_key_pair_with_eddsa(self) -> None:
        with self.settings(NINJA_SIMPLE_JWT=self.merge_settings(JWT_ALGORITHM="EdDSA")):
            call_command("make_jwt_key")


class TestMakeRsaCommand(TestCase):
    def test_emits_deprecation_warning(self) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            call_command("make_rsa")

        deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
        self.assertEqual(len(deprecation_warnings), 1)
        self.assertIn("make_jwt_key", str(deprecation_warnings[0].message))

    @patch("ninja_simple_jwt.management.commands.make_rsa.call_command")
    def test_delegates_to_make_jwt_key(self, mock_call_command: Any) -> None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            call_command("make_rsa")

        mock_call_command.assert_called_once_with("make_jwt_key")
