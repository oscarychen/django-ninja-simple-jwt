from django.test import TestCase
from freezegun import freeze_time
from jwt import DecodeError, ExpiredSignatureError, InvalidTokenError

from ninja_simple_jwt.jwt.key_creation import make_and_save_key_pair
from ninja_simple_jwt.jwt.token_operations import TokenTypes, decode_token, encode_token


class TestEncodeToken(TestCase):
    def setUp(self) -> None:
        make_and_save_key_pair()

    def test_encode_token(self) -> None:
        test_payload = {
            "name": "bebe",
        }

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
        with freeze_time("2024-01-11 12:00:01"):
            token, _ = encode_token(payload=test_payload, token_type=TokenTypes.REFRESH)

        try:
            decode_token(token, token_type=TokenTypes.ACCESS)
        except InvalidTokenError:
            exception_raised = True

        self.assertTrue(exception_raised, "Exception raised as expected.")

    def test_decode_invalid_token_raises_decode_error_exception(self) -> None:
        exception_raised = False

        try:
            decode_token("not.real.token", token_type=TokenTypes.REFRESH)
        except DecodeError:
            exception_raised = True

        self.assertTrue(exception_raised, "Exception raised as expected.")

    def test_decode_expired_token_raises_expired_signature_exception(self) -> None:
        exception_raised = False

        with freeze_time("2000-01-01 12:00:00"):
            token, _ = encode_token(payload={}, token_type=TokenTypes.ACCESS)

        with freeze_time("2020-01-01 12:00:00"):
            try:
                decode_token(token, token_type=TokenTypes.ACCESS)
            except ExpiredSignatureError:
                exception_raised = True

        self.assertTrue(exception_raised, "Exception raised as expected.")
