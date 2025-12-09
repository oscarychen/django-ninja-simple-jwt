from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest
from django.utils.module_loading import import_string
from jwt import PyJWTError
from ninja.errors import AuthenticationError
from ninja.security import HttpBearer
from ninja.security.http import DecodeError

from ninja_simple_jwt.auth.token_user import PrimaryKey, TokenUser
from ninja_simple_jwt.jwt.token_operations import TokenTypes, decode_token
from ninja_simple_jwt.settings import ninja_simple_jwt_settings

User = get_user_model()  # type: ignore[assignment]
TokenUser = import_string(ninja_simple_jwt_settings.TOKEN_USER_CLS)  # type: ignore[assignment,misc]


class HttpJwtAuth(HttpBearer):
    def authenticate(self, request: HttpRequest, token: str) -> bool:
        token = self.decode_authorization(request.headers["Authorization"])

        try:
            # Decode and verify the JWT token
            decoded_token = decode_token(token, token_type=TokenTypes.ACCESS, verify=True)

            # Extract user_id from the token
            user_id = decoded_token.get("user_id")
            if not user_id:
                raise AuthenticationError(status_code=401, message="Invalid token: missing user_id")

            user: TokenUser | AbstractBaseUser | None
            # Authenticate based on configuration
            if ninja_simple_jwt_settings.USE_STATELESS_AUTH:
                user = self._create_stateless_user(decoded_token)
            else:
                user = self._get_user_from_database(user_id)
                if user is None:
                    raise AuthenticationError(status_code=401, message="Invalid or expired token")

            # Set the authenticated user on the request
            request.user = user  # type: ignore[assignment]

            return True

        except PyJWTError as e:
            raise AuthenticationError(status_code=401, message=f"Invalid or expired token: {e}") from e

    @staticmethod
    def _create_stateless_user(token: dict) -> TokenUser:
        """
        Create a stateless user instance from JWT token claims.

        Args:
            token: The decoded JWT token payload

        Returns:
            TokenUser instance populated with token claims
        """
        user = TokenUser(
            user_id=token.get("user_id"),
            email=token.get("email", None),
            roles=token.get("roles", []),
        )

        # Set the primary key attribute on the TokenUser object
        setattr(user, User._meta.pk.name, token.get("user_id"))  # type: ignore[union-attr]

        # Set all token claims as attributes on the user object
        for claim in ninja_simple_jwt_settings.TOKEN_CLAIM_USER_ATTRIBUTE_MAP.keys():
            if claim in token:
                setattr(user, claim, token.get(claim))

        return user

    @staticmethod
    def _get_user_from_database(user_id: PrimaryKey) -> Optional[AbstractBaseUser]:
        """
        Get user from database using the user_id from token.

        Args:
            user_id: The user ID from the JWT token (can be int, UUID, str, etc.)

        Returns:
            User instance if found, None otherwise
        """
        # Use the primary key field name dynamically to support any PK type
        pk_field_name = User._meta.pk.name  # type: ignore[union-attr]
        return User.objects.filter(**{pk_field_name: user_id}).first()

    def decode_authorization(self, value: str) -> str:
        parts = value.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise DecodeError("Invalid Authorization header")

        token = parts[1]
        return token
