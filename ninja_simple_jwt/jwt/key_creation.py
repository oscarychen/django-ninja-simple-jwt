from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.core.files.base import ContentFile
from django.utils.module_loading import import_string

from ninja_simple_jwt.jwt.key_retrieval import InMemoryJwtKeyPair
from ninja_simple_jwt.settings import ninja_simple_jwt_settings


def make_and_save_key_pair() -> tuple[str, str]:
    jwt_private_key_storage = import_string(ninja_simple_jwt_settings.JWT_PRIVATE_KEY_STORAGE)
    jwt_public_key_storage = import_string(ninja_simple_jwt_settings.JWT_PUBLIC_KEY_STORAGE)
    pem_private_key, pem_public_key = make_keys()
    private_key_path = jwt_private_key_storage.save(
        name=ninja_simple_jwt_settings.JWT_PRIVATE_KEY_PATH, content=ContentFile(pem_private_key)
    )
    public_key_path = jwt_public_key_storage.save(
        name=ninja_simple_jwt_settings.JWT_PUBLIC_KEY_PATH, content=ContentFile(pem_public_key)
    )
    InMemoryJwtKeyPair.clear()
    return private_key_path, public_key_path


def make_keys() -> tuple[bytes, bytes]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    pem_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    pem_public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return pem_private_key, pem_public_key
