from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from django.test import TestCase

from ninja_simple_jwt.jwt.key_creation import _make_ed25519_keys, _make_rsa_keys, make_keys
from ninja_simple_jwt.settings import DEFAULTS


class TestMakeRsaKeys(TestCase):
    def test_generates_valid_rsa_key_pair(self) -> None:
        priv_bytes, pub_bytes = _make_rsa_keys()
        priv_key = load_pem_private_key(priv_bytes, password=None)
        pub_key = load_pem_public_key(pub_bytes)
        self.assertIsInstance(priv_key, RSAPrivateKey)
        self.assertIsInstance(pub_key, RSAPublicKey)

    def test_key_pair_matches(self) -> None:
        priv_bytes, pub_bytes = _make_rsa_keys()
        priv_key = load_pem_private_key(priv_bytes, password=None)
        pub_key = load_pem_public_key(pub_bytes)
        self.assertEqual(priv_key.public_key().public_numbers(), pub_key.public_numbers())


class TestMakeEd25519Keys(TestCase):
    def test_generates_valid_ed25519_key_pair(self) -> None:
        priv_bytes, pub_bytes = _make_ed25519_keys()
        priv_key = load_pem_private_key(priv_bytes, password=None)
        pub_key = load_pem_public_key(pub_bytes)
        self.assertIsInstance(priv_key, Ed25519PrivateKey)
        self.assertIsInstance(pub_key, Ed25519PublicKey)


class TestMakeKeysDispatch(TestCase):
    @staticmethod
    def merge_settings(**kwargs: Any) -> dict:
        return {**DEFAULTS, **kwargs}

    def test_defaults_to_rsa(self) -> None:
        private_bytes, _ = make_keys()
        key = load_pem_private_key(private_bytes, password=None)
        self.assertIsInstance(key, RSAPrivateKey)

    def test_rs256_produces_rsa_keys(self) -> None:
        with self.settings(NINJA_SIMPLE_JWT=self.merge_settings(JWT_ALGORITHM="RS256")):
            private_bytes, _ = make_keys()
        key = load_pem_private_key(private_bytes, password=None)
        self.assertIsInstance(key, RSAPrivateKey)

    def test_eddsa_produces_ed25519_keys(self) -> None:
        with self.settings(NINJA_SIMPLE_JWT=self.merge_settings(JWT_ALGORITHM="EdDSA")):
            private_bytes, _ = make_keys()
        key = load_pem_private_key(private_bytes, password=None)
        self.assertIsInstance(key, Ed25519PrivateKey)
