from datetime import timedelta
from typing import Any
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.test import TestCase
from django.utils.dateparse import parse_datetime
from freezegun import freeze_time
from ninja.errors import AuthenticationError
from ninja.security.http import DecodeError

from ninja_simple_jwt.auth.ninja_auth import HttpJwtAuth
from ninja_simple_jwt.jwt.key_creation import make_and_save_key_pair
from ninja_simple_jwt.jwt.token_operations import get_access_token_for_user
from ninja_simple_jwt.settings import DEFAULTS


class TestNinjaAuth(TestCase):
    @staticmethod
    def merge_settings(**kwargs: Any) -> dict:
        return {**DEFAULTS, **kwargs}

    def setUp(self) -> None:
        make_and_save_key_pair()
        self.user = get_user_model().objects.create_user(username="testuser", password="testpass")
        self.auth = HttpJwtAuth()

    def test_authenticate_with_valid_token(self) -> None:
        """Test authentication with a valid JWT token."""
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=5),
                TOKEN_CLAIM_USER_ATTRIBUTE_MAP={
                    "user_id": "id",
                    "username": "username",
                },
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                token, _ = get_access_token_for_user(self.user)

                # Create mock request
                request = MagicMock(spec=HttpRequest)
                request.headers = {"Authorization": f"Bearer {token}"}
                request.user = AnonymousUser()

                # Authenticate
                result = self.auth.authenticate(request, token)

                self.assertTrue(result, "Authentication should return True")
                self.assertIsNotNone(request.user, "User should be set on request")
                self.assertEqual(request.user.id, self.user.id, "User ID should match")
                self.assertEqual(request.user.username, self.user.username, "Username should match")

    def test_authenticate_with_invalid_token(self) -> None:
        """Test authentication with an invalid JWT token."""
        request = MagicMock(spec=HttpRequest)
        request.headers = {"Authorization": "Bearer invalid_token"}
        request.user = AnonymousUser()

        with self.assertRaises(AuthenticationError):
            self.auth.authenticate(request, "invalid_token")

    def test_authenticate_with_expired_token(self) -> None:
        """Test authentication with an expired JWT token."""
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=5),
                TOKEN_CLAIM_USER_ATTRIBUTE_MAP={
                    "user_id": "id",
                    "username": "username",
                },
            )
        ):
            # Create token in the past
            with freeze_time("2024-01-11 12:00:01"):
                token, _ = get_access_token_for_user(self.user)

            # Try to use it after expiration
            with freeze_time("2024-01-11 12:10:01"):
                request = MagicMock(spec=HttpRequest)
                request.headers = {"Authorization": f"Bearer {token}"}
                request.user = AnonymousUser()

                with self.assertRaises(AuthenticationError):
                    self.auth.authenticate(request, token)

    def test_decode_authorization_valid_header(self) -> None:
        """Test decoding a valid Authorization header."""
        token = self.auth.decode_authorization("Bearer test_token_123")
        self.assertEqual(token, "test_token_123", "Token should be extracted correctly")

    def test_decode_authorization_invalid_format(self) -> None:
        """Test decoding an invalid Authorization header format."""
        with self.assertRaises(DecodeError) as context:
            self.auth.decode_authorization("test_token_123")

        self.assertIn("Invalid Authorization header", str(context.exception))

    def test_decode_authorization_wrong_scheme(self) -> None:
        """Test decoding an Authorization header with wrong scheme."""
        with self.assertRaises(DecodeError) as context:
            self.auth.decode_authorization("Basic test_token_123")

        self.assertIn("Invalid Authorization header", str(context.exception))

    def test_decode_authorization_case_insensitive(self) -> None:
        """Test that Bearer scheme is case-insensitive."""
        token = self.auth.decode_authorization("bearer test_token_123")
        self.assertEqual(token, "test_token_123", "Should accept lowercase 'bearer'")

        token = self.auth.decode_authorization("BEARER test_token_123")
        self.assertEqual(token, "test_token_123", "Should accept uppercase 'BEARER'")

    def test_authenticate_with_stateless_user(self) -> None:
        """Test that authentication works with stateless user creation (no DB lookup)."""
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=5),
                TOKEN_CLAIM_USER_ATTRIBUTE_MAP={
                    "user_id": "id",
                    "username": "username",
                },
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                token, _ = get_access_token_for_user(self.user)
                user_id = self.user.id
                username = self.user.username

                # Delete the user to prove we're not fetching from DB
                self.user.delete()

                request = MagicMock(spec=HttpRequest)
                request.headers = {"Authorization": f"Bearer {token}"}
                request.user = AnonymousUser()

                # Authenticate should still work because we create user from token claims
                result = self.auth.authenticate(request, token)

                self.assertTrue(result, "Authentication should return True")
                self.assertIsNotNone(request.user, "User should be set on request")
                self.assertEqual(request.user.id, user_id, "User ID should match token claim")
                self.assertEqual(request.user.username, username, "Username should match token claim")


class TestHttpJwtAuthWithDatabaseBackend(TestCase):
    """Test HttpJwtAuth with USE_STATELESS_AUTH=False (database-backed authentication)."""

    @staticmethod
    def merge_settings(**kwargs: Any) -> dict:
        return {**DEFAULTS, **kwargs}

    def setUp(self) -> None:
        make_and_save_key_pair()
        self.user = get_user_model().objects.create_user(username="testuser2", password="testpass2")

    def test_authenticate_with_valid_token_and_database_backend(self) -> None:
        """Test authentication with a valid JWT token using database-backed mode."""
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                USE_STATELESS_AUTH=False,
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                token, _ = get_access_token_for_user(self.user)
                request = MagicMock(spec=HttpRequest)
                request.headers = {"Authorization": f"Bearer {token}"}
                request.user = AnonymousUser()

                auth = HttpJwtAuth()
                result = auth.authenticate(request, token)

            self.assertTrue(result, "Authentication should return True")
            self.assertIsNotNone(request.user, "User should be set on request")
            self.assertEqual(request.user.id, self.user.id, "User ID should match")
            self.assertEqual(request.user.username, self.user.username, "Username should match")

    def test_authenticate_with_invalid_token_and_database_backend(self) -> None:
        """Test authentication with an invalid JWT token using database-backed mode."""
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                USE_STATELESS_AUTH=False,
            )
        ):
            request = MagicMock(spec=HttpRequest)
            request.headers = {"Authorization": "Bearer invalid_token"}
            request.user = AnonymousUser()

            auth = HttpJwtAuth()
            with self.assertRaises(AuthenticationError):
                auth.authenticate(request, "invalid_token")

    def test_authenticate_with_expired_token_and_database_backend(self) -> None:
        """Test authentication with an expired JWT token using database-backed mode."""
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                USE_STATELESS_AUTH=False,
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=5),
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                token, _ = get_access_token_for_user(self.user)

            with freeze_time("2024-01-11 12:10:01"):
                request = MagicMock(spec=HttpRequest)
                request.headers = {"Authorization": f"Bearer {token}"}
                request.user = AnonymousUser()

                auth = HttpJwtAuth()
                with self.assertRaises(AuthenticationError):
                    auth.authenticate(request, token)


class TestHttpJwtAuthWithStatelessBackend(TestCase):
    """Test HttpJwtAuth with USE_STATELESS_AUTH=True (stateless authentication)."""

    @staticmethod
    def merge_settings(**kwargs: Any) -> dict:
        return {**DEFAULTS, **kwargs}

    def setUp(self) -> None:
        make_and_save_key_pair()
        self.user = get_user_model().objects.create_user(username="testuser3", password="testpass3")

    def test_authenticate_with_valid_token_and_stateless_backend(self) -> None:
        """Test authentication with a valid JWT token using stateless mode."""
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                USE_STATELESS_AUTH=True,
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                token, _ = get_access_token_for_user(self.user)
                request = MagicMock(spec=HttpRequest)
                request.headers = {"Authorization": f"Bearer {token}"}
                request.user = AnonymousUser()

                auth = HttpJwtAuth()
                result = auth.authenticate(request, token)

            self.assertTrue(result, "Authentication should return True")
            self.assertIsNotNone(request.user, "User should be set on request")
            self.assertEqual(request.user.id, self.user.id, "User ID should match")
            self.assertEqual(request.user.username, self.user.username, "Username should match")
            # After authentication, request.user is a TokenUser, not AnonymousUser
            self.assertEqual(request.user.email, self.user.email, "Email should match")  # pylint: disable=no-member
            self.assertEqual(request.user.is_staff, self.user.is_staff, "Is staff should match")
            self.assertEqual(request.user.is_superuser, self.user.is_superuser, "Is superuser should match")
            self.assertEqual(request.user.is_active, self.user.is_active, "Is active should match")
            # For datetime fields, parse the JWT string and compare with original datetime
            # Note: JWT serialization may lose microsecond precision, so we compare up to seconds
            if self.user.last_login and request.user.last_login:  # pylint: disable=no-member
                parsed_last_login = parse_datetime(request.user.last_login)  # pylint: disable=no-member
                if parsed_last_login and self.user.last_login:
                    # Compare up to seconds precision (ignore microseconds)
                    self.assertEqual(
                        parsed_last_login.replace(microsecond=0),
                        self.user.last_login.replace(microsecond=0),
                        "Last login should match",
                    )
            if self.user.date_joined and request.user.date_joined:  # pylint: disable=no-member
                parsed_date_joined = parse_datetime(request.user.date_joined)  # pylint: disable=no-member
                if parsed_date_joined and self.user.date_joined:
                    # Compare up to seconds precision (ignore microseconds)
                    self.assertEqual(
                        parsed_date_joined.replace(microsecond=0),
                        self.user.date_joined.replace(microsecond=0),
                        "Date joined should match",
                    )

    def test_authenticate_with_invalid_token_and_stateless_backend(self) -> None:
        """Test authentication with an invalid JWT token using stateless mode."""
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                USE_STATELESS_AUTH=True,
            )
        ):
            request = MagicMock(spec=HttpRequest)
            request.headers = {"Authorization": "Bearer invalid_token"}
            request.user = AnonymousUser()

            auth = HttpJwtAuth()
            with self.assertRaises(AuthenticationError):
                auth.authenticate(request, "invalid_token")

    def test_authenticate_with_expired_token_and_stateless_backend(self) -> None:
        """Test authentication with an expired JWT token using stateless mode."""
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                USE_STATELESS_AUTH=True,
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=5),
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                token, _ = get_access_token_for_user(self.user)

            with freeze_time("2024-01-11 12:10:01"):
                request = MagicMock(spec=HttpRequest)
                request.headers = {"Authorization": f"Bearer {token}"}
                request.user = AnonymousUser()

                auth = HttpJwtAuth()
                with self.assertRaises(AuthenticationError):
                    auth.authenticate(request, token)
