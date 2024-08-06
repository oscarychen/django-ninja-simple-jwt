from typing import Any

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase

from ninja_simple_jwt.auth.ninja_auth import HttpJwtAuth
from ninja_simple_jwt.jwt.key_creation import make_and_save_key_pair
from ninja_simple_jwt.settings import DEFAULTS


class TestNinjaAuth(TestCase):
    @staticmethod
    def merge_settings(**kwargs: Any) -> dict:
        return {**DEFAULTS, **kwargs}

    def setUp(self) -> None:
        make_and_save_key_pair()


class TestHttpJwtAuth(TestNinjaAuth):
    def test_set_string_token_claims_to_user(self) -> None:
        username = "user"
        token_data = {"username": username}
        user = AnonymousUser()
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(TOKEN_CLAIM_USER_ATTRIBUTE_MAP={"username": "username"})
        ):
            HttpJwtAuth.set_token_claims_to_user(user, token_data)
            self.assertEqual(user.username, username, "Default settings should set the token claims to the user.")

    def test_set_customized_callable_token_claims_to_user(self) -> None:
        username = "user"
        token_data = {"username": username}
        user = AnonymousUser()
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(TOKEN_CLAIM_USER_ATTRIBUTE_MAP={"username": lambda u: "foo"})
        ):
            HttpJwtAuth.set_token_claims_to_user(user, token_data)
            self.assertEqual(user.username, username, "Customized settings should set the token claims to the user.")
