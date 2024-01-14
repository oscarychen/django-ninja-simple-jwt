from django.utils.functional import classproperty
from django.utils.module_loading import import_string

from ninja_simple_jwt.settings import ninja_simple_jwt_settings


class InMemoryJwtKeyPair:
    _private_key = None
    _public_key = None

    @classproperty
    def private_key(self) -> bytes:
        if self._private_key is None:
            self._private_key = self._get_private_jwt_key()
        return self._private_key

    @classproperty
    def public_key(self) -> bytes:
        if self._public_key is None:
            self._public_key = self._get_public_jwt_key()
        return self._public_key

    @staticmethod
    def _get_private_jwt_key() -> bytes:
        jwt_key_storage = import_string(ninja_simple_jwt_settings.JWT_KEY_STORAGE)
        with jwt_key_storage.open(ninja_simple_jwt_settings.JWT_PRIVATE_KEY_PATH) as f:
            return f.read()

    @staticmethod
    def _get_public_jwt_key() -> bytes:
        jwt_key_storage = import_string(ninja_simple_jwt_settings.JWT_KEY_STORAGE)
        with jwt_key_storage.open(ninja_simple_jwt_settings.JWT_PUBLIC_KEY_PATH) as f:
            return f.read()

    @classmethod
    def clear(cls) -> None:
        cls._public_key = None
        cls._private_key = None
