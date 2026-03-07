from datetime import timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.test import TestCase
from freezegun import freeze_time
from jwt import DecodeError, ExpiredSignatureError, InvalidTokenError

from ninja_simple_jwt.jwt.key_creation import make_and_save_key_pair
from ninja_simple_jwt.jwt.token_operations import (
    TokenTypes,
    decode_token,
    encode_token,
    get_access_token_for_user,
    get_access_token_from_refresh_token,
    get_refresh_token_for_user,
)
from ninja_simple_jwt.settings import DEFAULTS


class TestEdDSAEncodeDecodeToken(TestCase):
    @staticmethod
    def merge_settings(**kwargs: Any) -> dict:
        return {**DEFAULTS, **kwargs, "JWT_ALGORITHM": "EdDSA"}

    def setUp(self) -> None:
        with self.settings(NINJA_SIMPLE_JWT=self.merge_settings()):
            make_and_save_key_pair()

    def test_encode_token(self) -> None:
        test_payload = {"name": "bebe"}
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_REFRESH_TOKEN_LIFETIME=timedelta(days=30),
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=15),
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                token, token_data = encode_token(payload=test_payload, token_type=TokenTypes.REFRESH)

        self.assertIsNotNone(token)
        self.assertEqual(token_data["exp"], 1707566401)
        self.assertEqual(token_data["iat"], 1704974401)
        self.assertEqual(token_data["token_type"], TokenTypes.REFRESH)
        self.assertEqual(token_data["name"], "bebe")
        self.assertIsNotNone(token_data["jti"])

    def test_decode_token(self) -> None:
        test_payload = {"name": "bebe"}
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_REFRESH_TOKEN_LIFETIME=timedelta(days=30),
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=15),
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                token, _ = encode_token(payload=test_payload, token_type=TokenTypes.ACCESS)
                decoded_data = decode_token(token, token_type=TokenTypes.ACCESS)

        self.assertEqual(decoded_data["exp"], 1704975301)
        self.assertEqual(decoded_data["iat"], 1704974401)
        self.assertEqual(decoded_data["token_type"], TokenTypes.ACCESS)
        self.assertEqual(decoded_data["name"], "bebe")
        self.assertIsNotNone(decoded_data["jti"])

    def test_decode_token_with_wrong_token_type_raises_exception(self) -> None:
        test_payload = {"name": "bebe"}
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_REFRESH_TOKEN_LIFETIME=timedelta(days=30),
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=15),
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                token, _ = encode_token(payload=test_payload, token_type=TokenTypes.REFRESH)

            with self.assertRaises(InvalidTokenError):
                decode_token(token, token_type=TokenTypes.ACCESS)

    def test_decode_invalid_token_raises_decode_error(self) -> None:
        with self.settings(NINJA_SIMPLE_JWT=self.merge_settings()):
            with self.assertRaises(DecodeError):
                decode_token("not.real.token", token_type=TokenTypes.REFRESH)

    def test_decode_expired_token_raises_expired_signature(self) -> None:
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_REFRESH_TOKEN_LIFETIME=timedelta(days=30),
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=15),
            )
        ):
            with freeze_time("2000-01-01 12:00:00"):
                token, _ = encode_token(payload={}, token_type=TokenTypes.ACCESS)

            with freeze_time("2020-01-01 12:00:00"):
                with self.assertRaises(ExpiredSignatureError):
                    decode_token(token, token_type=TokenTypes.ACCESS)

    def test_get_access_token_from_refresh_token(self) -> None:
        test_payload = {"username": "bebe"}
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_REFRESH_TOKEN_LIFETIME=timedelta(days=30),
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=15),
                TOKEN_CLAIM_USER_ATTRIBUTE_MAP={"user_id": "id", "username": "username"},
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                refresh_token, _ = encode_token(payload=test_payload, token_type=TokenTypes.REFRESH)
            with freeze_time("2024-01-11 12:00:02"):
                access_token, access_token_data = get_access_token_from_refresh_token(refresh_token)
            with freeze_time("2024-01-11 12:00:03"):
                decoded = decode_token(access_token, token_type=TokenTypes.ACCESS)

        self.assertEqual(access_token_data["username"], "bebe")
        self.assertEqual(decoded["username"], "bebe")


class TestEdDSAUserTokenFunctions(TestCase):
    @staticmethod
    def merge_settings(**kwargs: Any) -> dict:
        return {**DEFAULTS, **kwargs, "JWT_ALGORITHM": "EdDSA"}

    def setUp(self) -> None:
        with self.settings(NINJA_SIMPLE_JWT=self.merge_settings()):
            make_and_save_key_pair()
        self.user = get_user_model().objects.create_user("tester")

    def test_get_refresh_token_for_user(self) -> None:
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                TOKEN_CLAIM_USER_ATTRIBUTE_MAP={"user_id": "id", "username": "username"},
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                token, token_data = get_refresh_token_for_user(self.user)
                decoded = decode_token(token, token_type=TokenTypes.REFRESH)

        self.assertEqual(token_data["token_type"], TokenTypes.REFRESH)
        self.assertIn("user_id", token_data)
        self.assertIn("username", token_data)
        self.assertEqual(decoded["token_type"], TokenTypes.REFRESH)
        self.assertIn("user_id", decoded)

    def test_get_access_token_for_user(self) -> None:
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                TOKEN_CLAIM_USER_ATTRIBUTE_MAP={"user_id": "id", "username": "username"},
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                token, token_data = get_access_token_for_user(self.user)
                decoded = decode_token(token, token_type=TokenTypes.ACCESS)

        self.assertEqual(token_data["token_type"], TokenTypes.ACCESS)
        self.assertIn("user_id", token_data)
        self.assertEqual(decoded["token_type"], TokenTypes.ACCESS)
        self.assertIn("user_id", decoded)
