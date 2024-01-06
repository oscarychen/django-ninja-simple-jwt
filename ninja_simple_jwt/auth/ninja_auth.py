from django.http import HttpRequest
from jwt import PyJWTError
from ninja.errors import AuthenticationError
from ninja.security import HttpBearer
from ninja.security.http import DecodeError

from ninja_simple_jwt.jwt.token_operations import TokenTypes, decode_token


class HttpJwtAuth(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> bool:
        token = self.decode_authorization(request.headers["Authorization"])

        try:
            access_token = decode_token(token, token_type=TokenTypes.ACCESS, verify=True)
        except PyJWTError as e:
            raise AuthenticationError(e)

        setattr(request.user, "id", access_token["user_id"])
        setattr(request.user, "username", access_token["username"])

        return True

    def decode_authorization(self, value: str) -> str:
        parts = value.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise DecodeError("Invalid Authorization header")

        token = parts[1]
        return token
