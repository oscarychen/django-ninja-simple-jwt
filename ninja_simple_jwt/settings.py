from typing import Any, Optional, TypedDict

from django.conf import settings
from django.test.signals import setting_changed

USER_SETTINGS = getattr(settings, "NINJA_SIMPLE_JWT", None)


class NinjaSimpleJwtSettingsDict(TypedDict):
    pass


DEFAULTS: NinjaSimpleJwtSettingsDict = {}
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

        # get from user settings or default value
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
