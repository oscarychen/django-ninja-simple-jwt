from datetime import datetime
from enum import Enum
from json import JSONEncoder
from typing import Any, Optional, Tuple
from uuid import uuid4

import jwt
from django.contrib.auth.models import AbstractBaseUser
from django.utils import timezone
from django.utils.module_loading import import_string
from jwt import ExpiredSignatureError, InvalidKeyError, InvalidTokenError

from ninja_simple_jwt.jwt.key_retrieval import InMemoryJwtKeyPair
from ninja_simple_jwt.settings import ninja_simple_jwt_settings


class TokenTypes(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


TokenUserJsonEncoder = import_string(ninja_simple_jwt_settings.TOKEN_USER_ENCODER_CLS)


def get_refresh_token_for_user(user: AbstractBaseUser) -> Tuple[str, dict]:
    payload = get_token_payload_for_user(user)
    return encode_token(payload, TokenTypes.REFRESH, json_encoder=TokenUserJsonEncoder)


def get_access_token_for_user(user: AbstractBaseUser) -> Tuple[str, dict]:
    payload = get_token_payload_for_user(user)
    return encode_token(payload, TokenTypes.ACCESS, json_encoder=TokenUserJsonEncoder)


def get_token_payload_for_user(user: AbstractBaseUser) -> dict:
    return {
        claim: getattr(user, user_attr)
        for claim, user_attr in ninja_simple_jwt_settings.TOKEN_CLAIM_USER_ATTRIBUTE_MAP.items()
    }


def get_access_token_from_refresh_token(refresh_token: str) -> Tuple[str, dict]:
    decoded = decode_token(refresh_token, token_type=TokenTypes.REFRESH, verify=True)
    payload = {claim: decoded.get(claim) for claim in ninja_simple_jwt_settings.TOKEN_CLAIM_USER_ATTRIBUTE_MAP}
    return encode_token(payload, TokenTypes.ACCESS)


def encode_token(
    payload: dict, token_type: TokenTypes, json_encoder: Optional[type[JSONEncoder]] = None, **additional_headers: Any
) -> Tuple[str, dict]:
    now = timezone.now()
    if token_type == TokenTypes.REFRESH:
        expiry = now + ninja_simple_jwt_settings.JWT_REFRESH_TOKEN_LIFETIME
    else:
        expiry = now + ninja_simple_jwt_settings.JWT_ACCESS_TOKEN_LIFETIME

    payload_data = {
        **payload,
        "jti": uuid4().hex,
        "exp": int(expiry.timestamp()),
        "iat": int(now.timestamp()),
        "token_type": token_type,
    }

    return (
        jwt.encode(
            payload_data,
            InMemoryJwtKeyPair.private_key,
            algorithm="RS256",
            headers=additional_headers,
            json_encoder=json_encoder,
        ),
        payload_data,
    )


def decode_token(token: str, token_type: TokenTypes, verify: bool = True) -> dict:
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
