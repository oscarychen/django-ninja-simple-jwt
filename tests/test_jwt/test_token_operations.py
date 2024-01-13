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


class TestEncodeDecodeToken(TestCase):
    @staticmethod
    def merge_settings(**kwargs: Any) -> dict:
        return {**DEFAULTS, **kwargs}

    def setUp(self) -> None:
        make_and_save_key_pair()

    def test_encode_token(self) -> None:
        test_payload = {
            "name": "bebe",
        }

        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_REFRESH_TOKEN_LIFETIME=timedelta(days=30),
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=15),
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                token, token_data = encode_token(payload=test_payload, token_type=TokenTypes.REFRESH)

        self.assertIsNotNone(token, "token created")
        self.assertEqual(token_data["exp"], 1707566401, "Token data has correct expiry time.")
        self.assertEqual(token_data["iat"], 1704974401, "Token data has correct issue time.")
        self.assertEqual(token_data["token_type"], TokenTypes.REFRESH, "Token data has correct token type.")
        self.assertEqual(token_data["name"], "bebe", "Token data has correct payload data.")
        self.assertIsNotNone(token_data["jti"], "Token data has jti claim.")

    def test_decode_token(self) -> None:
        test_payload = {
            "name": "bebe",
        }
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_REFRESH_TOKEN_LIFETIME=timedelta(days=30),
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=15),
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                token, _ = encode_token(payload=test_payload, token_type=TokenTypes.ACCESS)
                decoded_data = decode_token(token, token_type=TokenTypes.ACCESS)

        self.assertEqual(decoded_data["exp"], 1704975301, "Token has correct expiry time.")
        self.assertEqual(decoded_data["iat"], 1704974401, "Token has correct issue time.")
        self.assertEqual(decoded_data["token_type"], TokenTypes.ACCESS, "Token has correct token type.")
        self.assertEqual(decoded_data["name"], "bebe", "Token has correct payload data.")
        self.assertIsNotNone(decoded_data["jti"], "Token has jti claim.")

    def test_decode_token_with_wrong_token_type_raises_invalid_token_exception(self) -> None:
        exception_raised = False
        test_payload = {
            "name": "bebe",
        }
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_REFRESH_TOKEN_LIFETIME=timedelta(days=30),
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=15),
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                token, _ = encode_token(payload=test_payload, token_type=TokenTypes.REFRESH)

        try:
            decode_token(token, token_type=TokenTypes.ACCESS)
        except InvalidTokenError:
            exception_raised = True

        self.assertTrue(exception_raised, "Exception raised as expected if token type is wrong.")

    def test_decode_invalid_token_raises_decode_error_exception(self) -> None:
        exception_raised = False

        try:
            decode_token("not.real.token", token_type=TokenTypes.REFRESH)
        except DecodeError:
            exception_raised = True

        self.assertTrue(exception_raised, "Exception raised as expected if token is invalid.")

    def test_decode_expired_token_raises_expired_signature_exception(self) -> None:
        exception_raised = False

        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_REFRESH_TOKEN_LIFETIME=timedelta(days=30),
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=15),
            )
        ):
            with freeze_time("2000-01-01 12:00:00"):
                token, _ = encode_token(payload={}, token_type=TokenTypes.ACCESS)

            with freeze_time("2020-01-01 12:00:00"):
                try:
                    decode_token(token, token_type=TokenTypes.ACCESS)
                except ExpiredSignatureError:
                    exception_raised = True

        self.assertTrue(exception_raised, "Exception raised as expected if token has expired.")

    def test_get_access_token_from_refresh_token(self) -> None:
        test_payload = {
            "username": "bebe",
        }

        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_REFRESH_TOKEN_LIFETIME=timedelta(days=30),
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=15),
                TOKEN_CLAIM_USER_ATTRIBUTE_MAP={
                    "user_id": "id",
                    "username": "username",
                },
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                refresh_token, _ = encode_token(payload=test_payload, token_type=TokenTypes.REFRESH)
            with freeze_time("2024-01-11 12:00:02"):
                access_token, access_token_data = get_access_token_from_refresh_token(refresh_token)
            with freeze_time("2024-01-11 12:00:03"):
                decoded_access_token_data = decode_token(access_token, token_type=TokenTypes.ACCESS)

        self.assertEqual(access_token_data["exp"], 1704975302, "Token data has correct expiry time.")
        self.assertEqual(access_token_data["iat"], 1704974402, "Token data has correct issue time.")
        self.assertEqual(access_token_data["username"], "bebe", "Token data has correct payload data.")
        self.assertEqual(decoded_access_token_data["exp"], 1704975302, "Token has correct expiry time.")
        self.assertEqual(decoded_access_token_data["iat"], 1704974402, "Token has correct issue time.")
        self.assertEqual(decoded_access_token_data["username"], "bebe", "Token data has correct payload data.")

    def test_get_access_token_from_expired_refresh_token_raises_exception(self) -> None:
        exception_raised = False
        with freeze_time("2024-01-11 12:00:01"):
            refresh_token, _ = encode_token(payload={}, token_type=TokenTypes.REFRESH)

        with freeze_time("2025-01-11 12:00:02"):
            try:
                get_access_token_from_refresh_token(refresh_token)
            except ExpiredSignatureError:
                exception_raised = True

        self.assertTrue(exception_raised, "Exception raised as expected if token has expired.")


class TestUserTokenFunctions(TestCase):
    @staticmethod
    def merge_settings(**kwargs: Any) -> dict:
        return {**DEFAULTS, **kwargs}

    def setUp(self) -> None:
        make_and_save_key_pair()
        self.user = get_user_model().objects.create_user("tester")

    def test_get_refresh_token_for_user(self) -> None:
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_REFRESH_TOKEN_LIFETIME=timedelta(days=30),
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=15),
                TOKEN_CLAIM_USER_ATTRIBUTE_MAP={
                    "user_id": "id",
                    "username": "username",
                },
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                token, token_data = get_refresh_token_for_user(self.user)
                decoded_token_data = decode_token(token, token_type=TokenTypes.REFRESH)

        self.assertEqual(token_data["exp"], 1707566401, "Token data has correct exp.")
        self.assertEqual(token_data["iat"], 1704974401, "Token data has correct iat.")
        self.assertEqual(token_data["token_type"], TokenTypes.REFRESH, "Token data has correct token_type.")
        self.assertIn("user_id", token_data, "Token data has user_id.")
        self.assertIn("username", token_data, "Token data has username.")

        self.assertEqual(decoded_token_data["exp"], 1707566401, "Token data has correct exp.")
        self.assertEqual(decoded_token_data["iat"], 1704974401, "Token data has correct iat.")
        self.assertEqual(decoded_token_data["token_type"], TokenTypes.REFRESH, "Token data has correct token_type.")
        self.assertIn("user_id", decoded_token_data, "Token data has user_id.")
        self.assertIn("username", decoded_token_data, "Token data has username.")

    def test_get_access_token_for_user(self) -> None:
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_REFRESH_TOKEN_LIFETIME=timedelta(days=30),
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=15),
                TOKEN_CLAIM_USER_ATTRIBUTE_MAP={
                    "user_id": "id",
                    "username": "username",
                },
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                token, token_data = get_access_token_for_user(self.user)
                decoded_token_data = decode_token(token, token_type=TokenTypes.ACCESS)

        self.assertEqual(token_data["exp"], 1704975301, "Token data has correct exp.")
        self.assertEqual(token_data["iat"], 1704974401, "Token data has correct iat.")
        self.assertEqual(token_data["token_type"], TokenTypes.ACCESS, "Token data has correct token_type.")
        self.assertIn("user_id", token_data, "Token data has user_id.")
        self.assertIn("username", token_data, "Token data has username.")

        self.assertEqual(decoded_token_data["exp"], 1704975301, "Token data has correct exp.")
        self.assertEqual(decoded_token_data["iat"], 1704974401, "Token data has correct iat.")
        self.assertEqual(decoded_token_data["token_type"], TokenTypes.ACCESS, "Token data has correct token_type.")
        self.assertIn("user_id", decoded_token_data, "Token data has user_id.")
        self.assertIn("username", decoded_token_data, "Token data has username.")
