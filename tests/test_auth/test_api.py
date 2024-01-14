from datetime import datetime, timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from freezegun import freeze_time

from ninja_simple_jwt.jwt.key_creation import make_and_save_key_pair
from ninja_simple_jwt.jwt.token_operations import get_refresh_token_for_user
from ninja_simple_jwt.settings import DEFAULTS


class TestAuthEndPoints(TestCase):
    @staticmethod
    def merge_settings(**kwargs: Any) -> dict:
        return {**DEFAULTS, **kwargs}

    def setUp(self) -> None:
        make_and_save_key_pair()


class TestMobileSignIn(TestAuthEndPoints):
    def test_user_can_sign_in(self) -> None:
        username = "user"
        password = "password"
        user = get_user_model().objects.create_user(username=username, password=password)

        response = self.client.post(
            reverse("api-1.0.0:mobile_signin"),
            data={"username": username, "password": password},
            content_type="application/json",
        )

        self.assertEqual(200, response.status_code, "Correct status code.")
        self.assertIn("refresh", response.json(), "Response data contains refresh token.")
        self.assertIn("access", response.json(), "Response data contains access token.")

        user.refresh_from_db()
        self.assertIsNotNone(user.last_login, "User.last_login updated.")

    def test_inactive_user_cannot_sign_in(self) -> None:
        username = "user"
        password = "password"
        get_user_model().objects.create_user(username=username, password=password, is_active=False)

        response = self.client.post(
            reverse("api-1.0.0:mobile_signin"),
            data={"username": username, "password": password},
            content_type="application/json",
        )

        self.assertEqual(401, response.status_code, "Inactive user cannot sign in.")


class TestMobileRefresh(TestAuthEndPoints):
    def test_user_can_refresh_token(self) -> None:
        user = get_user_model().objects.create_user(username="user")

        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_REFRESH_TOKEN_LIFETIME=timedelta(days=31),
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=5),
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                refresh_token, _ = get_refresh_token_for_user(user)
                response = self.client.post(
                    reverse("api-1.0.0:mobile_token_refresh"),
                    data={"refresh": refresh_token},
                    content_type="application/json",
                )

        self.assertEqual(200, response.status_code, "Correct status code.")
        self.assertIn("access", response.json(), "Response data contains access token.")
        self.assertNotIn("refresh", response.json(), "Response data should not contain refresh token.")


class TestWebSignIn(TestAuthEndPoints):
    def test_user_can_sign_in(self) -> None:
        username = "user"
        password = "password"
        user = get_user_model().objects.create_user(username=username, password=password)

        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_REFRESH_TOKEN_LIFETIME=timedelta(days=31),
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=5),
                WEB_REFRESH_COOKIE_PATH="/tests/refresh_api_path",
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                response = self.client.post(
                    reverse("api-1.0.0:web_signin"),
                    data={"username": username, "password": password},
                    content_type="application/json",
                )

        self.assertEqual(200, response.status_code, "Correct status code.")
        self.assertNotIn("refresh", response.json(), "Response body should not contain refresh token.")
        self.assertIn("refresh", response.cookies, "Response header Set-Cookie has refresh token.")
        self.assertIn("access", response.json(), "Response body contains access token.")

        refresh_token_cookie = response.cookies.get("refresh")
        self.assertTrue(refresh_token_cookie["httponly"], "Refresh token cookie is HttpOnly.")
        self.assertEqual(
            "/tests/refresh_api_path", refresh_token_cookie["path"], "Refresh token cookie has correct path."
        )
        cookie_expires = datetime.strptime(refresh_token_cookie["expires"], "%a, %d %b %Y %H:%M:%S %Z")
        self.assertEqual(datetime(2024, 2, 11, 12, 0, 2), cookie_expires, "Refresh token cookies has correct expires.")

        user.refresh_from_db()
        self.assertIsNotNone(user.last_login, "User.last_login updated.")

    def test_inactive_user_cannot_sign_in(self) -> None:
        username = "user"
        password = "password"
        get_user_model().objects.create_user(username=username, password=password, is_active=False)

        response = self.client.post(
            reverse("api-1.0.0:web_signin"),
            data={"username": username, "password": password},
            content_type="application/json",
        )

        self.assertEqual(401, response.status_code, "Inactive user cannot sign in.")


class TestWebRefresh(TestAuthEndPoints):
    def test_user_token_refresh(self) -> None:
        user = get_user_model().objects.create_user(username="user")

        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_REFRESH_TOKEN_LIFETIME=timedelta(days=31),
                JWT_ACCESS_TOKEN_LIFETIME=timedelta(minutes=5),
                JWT_REFRESH_COOKIE_NAME="refresh-token",
            )
        ):
            with freeze_time("2024-01-11 12:00:01"):
                refresh_token, _ = get_refresh_token_for_user(user)

                response = self.client.post(
                    reverse("api-1.0.0:web_token_refresh"),
                    content_type="application/json",
                    HTTP_COOKIE=f"refresh-token={refresh_token}",
                )

        self.assertEqual(200, response.status_code, "Correct status code.")
        self.assertIn("access", response.json(), "Response body has access token.")
        self.assertNotIn("refresh", response.json(), "Response body should not have refresh token.")
