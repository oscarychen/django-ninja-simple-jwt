from datetime import timedelta
from typing import Any, Callable, Optional, TypedDict

from django.conf import settings
from django.test.signals import setting_changed
from typing_extensions import NotRequired

USER_SETTINGS = getattr(settings, "NINJA_SIMPLE_JWT", None)


class NinjaSimpleJwtSettingsDict(TypedDict):
    JWT_PRIVATE_KEY_STORAGE: NotRequired[str]
    JWT_PUBLIC_KEY_STORAGE: NotRequired[str]
    JWT_PRIVATE_KEY_PATH: NotRequired[str]
    JWT_PUBLIC_KEY_PATH: NotRequired[str]
    JWT_REFRESH_COOKIE_NAME: NotRequired[str]
    JWT_REFRESH_TOKEN_LIFETIME: NotRequired[timedelta]
    JWT_ACCESS_TOKEN_LIFETIME: NotRequired[timedelta]
    WEB_REFRESH_COOKIE_SECURE: NotRequired[bool]
    WEB_REFRESH_COOKIE_HTTP_ONLY: NotRequired[bool]
    WEB_REFRESH_COOKIE_SAME_SITE_POLICY: NotRequired[str]
    WEB_REFRESH_COOKIE_PATH: NotRequired[str]
    USERNAME_FIELD: NotRequired[str]
    TOKEN_CLAIM_USER_ATTRIBUTE_MAP: NotRequired[dict[str, str | Callable[[Any], str | int | float | bool | None]]]
    TOKEN_USER_ENCODER_CLS: NotRequired[str]


DEFAULTS: NinjaSimpleJwtSettingsDict = {
    "JWT_PRIVATE_KEY_STORAGE": "ninja_simple_jwt.jwt.key_store.local_disk_key_storage",
    "JWT_PUBLIC_KEY_STORAGE": "ninja_simple_jwt.jwt.key_store.local_disk_key_storage",
    "JWT_PRIVATE_KEY_PATH": "jwt-signing.pem",
    "JWT_PUBLIC_KEY_PATH": "jwt-signing.pub",
    "JWT_REFRESH_COOKIE_NAME": "refresh",
    "JWT_REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "JWT_ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "WEB_REFRESH_COOKIE_SECURE": not settings.DEBUG,
    "WEB_REFRESH_COOKIE_HTTP_ONLY": True,
    "WEB_REFRESH_COOKIE_SAME_SITE_POLICY": "Strict",
    "WEB_REFRESH_COOKIE_PATH": "/api/auth/web/token-refresh",
    "USERNAME_FIELD": "username",
    "TOKEN_CLAIM_USER_ATTRIBUTE_MAP": {
        "user_id": "id",
        "username": "username",
        "last_login": "last_login",
    },
    "TOKEN_USER_ENCODER_CLS": "ninja_simple_jwt.jwt.json_encode.TokenUserEncoder",
}

EMPTY_SETTINGS: NinjaSimpleJwtSettingsDict = {}


class NinjaSimpleJwtSettings:
    def __init__(
        self,
        user_settings: Optional[NinjaSimpleJwtSettingsDict] = None,
        defaults: Optional[NinjaSimpleJwtSettingsDict] = None,
    ) -> None:
        self._user_settings = user_settings or EMPTY_SETTINGS
        self.defaults = defaults or DEFAULTS
        self._cached_attrs: set = set()

    @property
    def user_settings(self) -> NinjaSimpleJwtSettingsDict:
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, "NINJA_SIMPLE_JWT", EMPTY_SETTINGS)
        return self._user_settings

    def __getattr__(self, attr: str) -> Any:
        # check the setting is accepted
        if attr not in self.defaults:
            raise AttributeError(f"Invalid NINJA_SIMPLE_JWT setting: {attr}")

        try:
            val = self.user_settings[attr]  # type: ignore
        except KeyError:
            val = self.defaults[attr]  # type: ignore

        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self) -> None:
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


ninja_simple_jwt_settings = NinjaSimpleJwtSettings(USER_SETTINGS, DEFAULTS)


def reload_drf_stripe_settings(*args: Any, **kwargs: Any) -> None:
    setting = kwargs["setting"]
    if setting == "NINJA_SIMPLE_JWT":
        ninja_simple_jwt_settings.reload()


setting_changed.connect(reload_drf_stripe_settings)
