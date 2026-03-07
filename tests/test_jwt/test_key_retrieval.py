from typing import Any

from django.test import TestCase

from ninja_simple_jwt.jwt.key_creation import make_and_save_key_pair, make_keys
from ninja_simple_jwt.jwt.key_retrieval import InMemoryJwtKeyPair
from ninja_simple_jwt.jwt.token_operations import TokenTypes, decode_token, encode_token
from ninja_simple_jwt.settings import DEFAULTS


class TestKeyRetrievalFromSettings(TestCase):
    @staticmethod
    def merge_settings(**kwargs: Any) -> dict:
        return {**DEFAULTS, **kwargs}

    def setUp(self) -> None:
        InMemoryJwtKeyPair.clear()

    def tearDown(self) -> None:
        InMemoryJwtKeyPair.clear()

    def test_private_key_loaded_from_setting_as_str(self) -> None:
        priv_bytes, pub_bytes = make_keys()
        priv_str = priv_bytes.decode()
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_PRIVATE_KEY=priv_str,
                JWT_PUBLIC_KEY=pub_bytes.decode(),
            )
        ):
            result = InMemoryJwtKeyPair.private_key
        self.assertIsInstance(result, bytes)
        self.assertEqual(result, priv_bytes)

    def test_public_key_loaded_from_setting_as_str(self) -> None:
        priv_bytes, pub_bytes = make_keys()
        pub_str = pub_bytes.decode()
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_PRIVATE_KEY=priv_bytes.decode(),
                JWT_PUBLIC_KEY=pub_str,
            )
        ):
            result = InMemoryJwtKeyPair.public_key
        self.assertIsInstance(result, bytes)
        self.assertEqual(result, pub_bytes)

    def test_private_key_loaded_from_setting_as_bytes(self) -> None:
        priv_bytes, pub_bytes = make_keys()
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_PRIVATE_KEY=priv_bytes,
                JWT_PUBLIC_KEY=pub_bytes,
            )
        ):
            result = InMemoryJwtKeyPair.private_key
        self.assertIsInstance(result, bytes)
        self.assertEqual(result, priv_bytes)

    def test_public_key_loaded_from_setting_as_bytes(self) -> None:
        priv_bytes, pub_bytes = make_keys()
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_PRIVATE_KEY=priv_bytes,
                JWT_PUBLIC_KEY=pub_bytes,
            )
        ):
            result = InMemoryJwtKeyPair.public_key
        self.assertIsInstance(result, bytes)
        self.assertEqual(result, pub_bytes)

    def test_falls_back_to_file_when_settings_are_none(self) -> None:
        make_and_save_key_pair()
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_PRIVATE_KEY=None,
                JWT_PUBLIC_KEY=None,
            )
        ):
            priv = InMemoryJwtKeyPair.private_key
            pub = InMemoryJwtKeyPair.public_key
        self.assertIsNotNone(priv)
        self.assertIsNotNone(pub)
        self.assertIn(b"PRIVATE KEY", priv)
        self.assertIn(b"PUBLIC KEY", pub)

    def test_encode_decode_with_keys_from_settings(self) -> None:
        priv_bytes, pub_bytes = make_keys()
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_PRIVATE_KEY=priv_bytes.decode(),
                JWT_PUBLIC_KEY=pub_bytes.decode(),
            )
        ):
            token, _ = encode_token(payload={"user": "test"}, token_type=TokenTypes.ACCESS)
            decoded = decode_token(token, token_type=TokenTypes.ACCESS)
        self.assertEqual(decoded["user"], "test")

    def test_encode_decode_with_eddsa_keys_from_settings(self) -> None:
        with self.settings(NINJA_SIMPLE_JWT=self.merge_settings(JWT_ALGORITHM="EdDSA")):
            priv_bytes, pub_bytes = make_keys()
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_ALGORITHM="EdDSA",
                JWT_PRIVATE_KEY=priv_bytes.decode(),
                JWT_PUBLIC_KEY=pub_bytes.decode(),
            )
        ):
            token, _ = encode_token(payload={"user": "test"}, token_type=TokenTypes.ACCESS)
            decoded = decode_token(token, token_type=TokenTypes.ACCESS)
        self.assertEqual(decoded["user"], "test")


class TestKeyRetrievalCaching(TestCase):
    @staticmethod
    def merge_settings(**kwargs: Any) -> dict:
        return {**DEFAULTS, **kwargs}

    def setUp(self) -> None:
        InMemoryJwtKeyPair.clear()

    def tearDown(self) -> None:
        InMemoryJwtKeyPair.clear()

    def test_clear_resets_cached_keys(self) -> None:
        priv_bytes, pub_bytes = make_keys()
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_PRIVATE_KEY=priv_bytes.decode(),
                JWT_PUBLIC_KEY=pub_bytes.decode(),
            )
        ):
            _ = InMemoryJwtKeyPair.private_key
            _ = InMemoryJwtKeyPair.public_key
        InMemoryJwtKeyPair.clear()
        # After clear, accessing keys again should require re-fetching
        # Verify by loading with different keys and confirming the new values are returned
        new_priv_bytes, new_pub_bytes = make_keys()
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_PRIVATE_KEY=new_priv_bytes.decode(),
                JWT_PUBLIC_KEY=new_pub_bytes.decode(),
            )
        ):
            self.assertEqual(InMemoryJwtKeyPair.private_key, new_priv_bytes)
            self.assertEqual(InMemoryJwtKeyPair.public_key, new_pub_bytes)

    def test_keys_are_cached_after_first_access(self) -> None:
        priv_bytes, pub_bytes = make_keys()
        with self.settings(
            NINJA_SIMPLE_JWT=self.merge_settings(
                JWT_PRIVATE_KEY=priv_bytes.decode(),
                JWT_PUBLIC_KEY=pub_bytes.decode(),
            )
        ):
            _ = InMemoryJwtKeyPair.private_key
            _ = InMemoryJwtKeyPair.public_key
        # Keys should still be cached even outside the settings override
        self.assertEqual(InMemoryJwtKeyPair.private_key, priv_bytes)
        self.assertEqual(InMemoryJwtKeyPair.public_key, pub_bytes)
