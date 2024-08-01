from typing import Any

from django.test import TestCase

from ninja_simple_jwt.settings import DEFAULTS
from ninja_simple_jwt.utils import make_authentication_params


class TestMakeAuthenticationParams(TestCase):
    @staticmethod
    def merge_settings(**kwargs: Any) -> dict:
        return {**DEFAULTS, **kwargs}

    def test_make_default_username_field_params(self) -> None:
        with self.settings():
            params = {"username": "username", "password": "password"}
            result = make_authentication_params(params)
            self.assertEqual(params, result, "Default settings should return the same params.")

    def test_make_customized_username_field_params(self) -> None:
        with self.settings(NINJA_SIMPLE_JWT=self.merge_settings(USERNAME_FIELD="email")):
            params = {"username": "email", "password": "password"}
            expected = {"email": "email", "password": "password"}
            result = make_authentication_params(params)
            self.assertEqual(expected, result, "Customized settings should return the same params.")
