from datetime import datetime, timezone

from django.contrib.auth import authenticate
from django.contrib.auth.signals import user_logged_in
from django.http import HttpRequest, HttpResponse
from jwt.exceptions import ExpiredSignatureError, InvalidKeyError, InvalidTokenError, PyJWTError
from ninja import Router
from ninja.errors import AuthenticationError

from ninja_simple_jwt.auth.views.schemas import (
    Empty,
    MobileSignInResponse,
    MobileTokenRefreshRequest,
    MobileTokenRefreshResponse,
    SignInRequest,
    WebSignInResponse,
)
from ninja_simple_jwt.jwt.token_operations import (
    TokenTypes,
    decode_token,
    get_access_token_for_user,
    get_access_token_from_refresh_token,
    get_refresh_token_for_user,
)
from ninja_simple_jwt.settings import ninja_simple_jwt_settings
from ninja_simple_jwt.utils import make_authentication_params

mobile_auth_router = Router()
web_auth_router = Router()


@mobile_auth_router.post("/sign-in", response=MobileSignInResponse, url_name="mobile_signin")
def mobile_sign_in(request: HttpRequest, payload: SignInRequest) -> dict:
    payload_data = payload.dict()
    user = authenticate(**make_authentication_params(payload_data))

    if user is None:
        raise AuthenticationError()

    user_logged_in.send(sender=user.__class__, request=request, user=user)
    refresh_token, _ = get_refresh_token_for_user(user)
    access_token, _ = get_access_token_for_user(user)
    return {"refresh": refresh_token, "access": access_token}


@mobile_auth_router.post("/token-refresh", response=MobileTokenRefreshResponse, url_name="mobile_token_refresh")
def mobile_token_refresh(request: HttpRequest, payload: MobileTokenRefreshRequest) -> dict:
    payload_data = payload.dict()
    try:
        access_token, _ = get_access_token_from_refresh_token(payload_data["refresh"])
    except PyJWTError:
        raise AuthenticationError()

    return {"access": access_token}


@web_auth_router.post("/sign-in", response=WebSignInResponse, url_name="web_signin")
def web_sign_in(request: HttpRequest, payload: SignInRequest, response: HttpResponse) -> dict:
    payload_data = payload.dict()
    user = authenticate(**make_authentication_params(payload_data))

    if user is None:
        raise AuthenticationError()

    user_logged_in.send(sender=user.__class__, request=request, user=user)
    refresh_token, refresh_token_payload = get_refresh_token_for_user(user)
    access_token, _ = get_access_token_for_user(user)
    response.set_cookie(
        key=ninja_simple_jwt_settings.JWT_REFRESH_COOKIE_NAME,
        value=refresh_token,
        expires=datetime.fromtimestamp(refresh_token_payload["exp"], timezone.utc),
        httponly=ninja_simple_jwt_settings.WEB_REFRESH_COOKIE_HTTP_ONLY,
        samesite=ninja_simple_jwt_settings.WEB_REFRESH_COOKIE_SAME_SITE_POLICY,
        secure=ninja_simple_jwt_settings.WEB_REFRESH_COOKIE_SECURE,
        path=ninja_simple_jwt_settings.WEB_REFRESH_COOKIE_PATH,
    )
    return {"access": access_token}


@web_auth_router.post("/token-refresh", response=WebSignInResponse, url_name="web_token_refresh")
def web_token_refresh(request: HttpRequest) -> dict:
    cookie = request.COOKIES.get(ninja_simple_jwt_settings.JWT_REFRESH_COOKIE_NAME)
    if cookie is None:
        raise AuthenticationError()
    access_token, _ = get_access_token_from_refresh_token(cookie)
    return {"access": access_token}


@web_auth_router.post("/sign-out", response={204: Empty}, url_name="web_sign_out")
def web_sign_out(request: HttpRequest, response: HttpResponse) -> tuple[int, str]:
    cookie = request.COOKIES.get(ninja_simple_jwt_settings.JWT_REFRESH_COOKIE_NAME)
    if cookie is None:
        return 204, ""
    try:
        decode_token(cookie, token_type=TokenTypes.REFRESH, verify=True)
    except (ExpiredSignatureError, InvalidKeyError, InvalidTokenError):
        return 204, ""
    response.delete_cookie(
        key=ninja_simple_jwt_settings.JWT_REFRESH_COOKIE_NAME, path=ninja_simple_jwt_settings.WEB_REFRESH_COOKIE_PATH
    )
    return 204, ""
