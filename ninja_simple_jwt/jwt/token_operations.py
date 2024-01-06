import time
from datetime import datetime
from enum import Enum
from typing import Any, Tuple, TypedDict
from uuid import uuid4

import jwt
from django.contrib.auth.models import AbstractBaseUser
from django.utils import timezone
from jwt import ExpiredSignatureError, InvalidKeyError, InvalidTokenError
from pydantic import UUID4

from ninja_simple_jwt.jwt.key_retrieval import InMemoryJwtKeyPair
from ninja_simple_jwt.settings import ninja_simple_jwt_settings


class TokenTypes(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenPayload(TypedDict):
    user_id: str
    username: str


class DecodedTokenPayload(TokenPayload):
    token_type: TokenTypes
    jti: UUID4
    exp: int
    iat: int


def get_refresh_token_for_user(user: AbstractBaseUser) -> Tuple[str, dict]:
    return encode_token({"username": user.get_username(), "user_id": user.pk}, TokenTypes.REFRESH)


def get_access_token(user_id: str, user_name: str) -> Tuple[str, dict]:
    return encode_token({"username": user_name, "user_id": user_id}, TokenTypes.ACCESS)


def get_access_token_from_refresh_token(refresh_token: str) -> Tuple[str, dict]:
    decoded = decode_token(refresh_token, token_type=TokenTypes.REFRESH, verify=True)
    return get_access_token(user_id=decoded["user_id"], user_name=decoded["username"])


def encode_token(payload: TokenPayload, token_type: TokenTypes, **additional_headers: Any) -> Tuple[str, dict]:
    now = timezone.now()
    if token_type == TokenTypes.REFRESH:
        expiry = now + ninja_simple_jwt_settings.JWT_REFRESH_TOKEN_LIFETIME
    else:
        expiry = now + ninja_simple_jwt_settings.JWT_ACCESS_TOKEN_LIFETIME

    payload_data = {
        **payload,
        "user_id": str(payload["user_id"]),
        "jti": uuid4().hex,
        "exp": int(time.mktime(expiry.timetuple())),
        "iat": int(time.mktime(now.timetuple())),
        "token_type": token_type,
    }

    return (
        jwt.encode(payload_data, InMemoryJwtKeyPair.private_key, algorithm="RS256", headers=additional_headers),
        payload_data,
    )


def decode_token(token: str, token_type: TokenTypes, verify: bool = True) -> DecodedTokenPayload:
    if verify is True:
        decoded = jwt.decode(token, InMemoryJwtKeyPair.public_key, algorithms=["RS256"])
        _verify_exp(decoded)
        _verify_jti(decoded)
        _verify_token_type(decoded, token_type)
    else:
        decoded = jwt.get_unverified_header(token)
    return decoded


def _verify_exp(payload: dict) -> None:
    now = timezone.now()
    token_expiry_unix_time = payload["exp"]
    token_expiry = timezone.make_aware(datetime.fromtimestamp(token_expiry_unix_time))
    if now >= token_expiry:
        raise ExpiredSignatureError("JWT has expired.")


def _verify_jti(payload: dict) -> None:
    if "jti" not in payload:
        raise InvalidKeyError("Invalid jti claim in JWT.")


def _verify_token_type(payload: dict, token_type: TokenTypes) -> None:
    if "token_type" not in payload:
        raise InvalidKeyError("Missing token type in JWT.")
    if payload["token_type"] != token_type:
        raise InvalidTokenError("Incorrect token type in JWT.")
