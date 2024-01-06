from datetime import UTC, datetime

from django.contrib.auth import authenticate
from django.http import HttpRequest, HttpResponse
from jwt.exceptions import PyJWTError
from ninja import Router
from ninja.errors import AuthenticationError

from ninja_simple_jwt.auth.views.schemas import (
    MobileSignInResponse,
    MobileTokenRefreshRequest,
    MobileTokenRefreshResponse,
    SignInRequest,
    WebSignInResponse,
)
from ninja_simple_jwt.jwt.token_operations import (
    get_access_token,
    get_access_token_from_refresh_token,
    get_refresh_token_for_user,
)
from ninja_simple_jwt.settings import ninja_simple_jwt_settings

mobile_auth_router = Router()
web_auth_router = Router()


@mobile_auth_router.post("/sign-in", response=MobileSignInResponse)
def mobile_sign_in(request: HttpRequest, payload: SignInRequest) -> dict:
    payload_data = payload.dict()
    user = authenticate(username=payload_data["username"], password=payload_data["password"])
    if user is None:
        raise AuthenticationError()
    refresh_token, _ = get_refresh_token_for_user(user)
    access_token, _ = get_access_token(str(user.pk), user.get_username())
    return {"refresh": refresh_token, "access": access_token}


@mobile_auth_router.post("/token-refresh", response=MobileTokenRefreshResponse)
def mobile_token_refresh(request: HttpRequest, payload: MobileTokenRefreshRequest) -> dict:
    payload_data = payload.dict()
    try:
        access_token, _ = get_access_token_from_refresh_token(payload_data["refresh"])
    except PyJWTError:
        raise AuthenticationError()

    return {"access": access_token}


@web_auth_router.post("/sign-in", response=WebSignInResponse)
def web_sign_in(request: HttpRequest, payload: SignInRequest, response: HttpResponse) -> dict:
    payload_data = payload.dict()
    user = authenticate(username=payload_data["username"], password=payload_data["password"])
    if user is None:
        raise AuthenticationError()
    refresh_token, refresh_token_payload = get_refresh_token_for_user(user)
    access_token, _ = get_access_token(str(user.pk), user.get_username())
    response.set_cookie(
        key=ninja_simple_jwt_settings.JWT_REFRESH_COOKIE_NAME,
        value=refresh_token,
        expires=datetime.fromtimestamp(refresh_token_payload["exp"], UTC),
        httponly=ninja_simple_jwt_settings.WEB_REFRESH_COOKIE_HTTP_ONLY,
        samesite=ninja_simple_jwt_settings.WEB_REFRESH_COOKIE_SAME_SITE_POLICY,
        secure=ninja_simple_jwt_settings.WEB_REFRESH_COOKIE_SECURE,
        path=ninja_simple_jwt_settings.WEB_REFRESH_COOKIE_PATH,
    )
    return {"access": access_token}


@web_auth_router.post("/token-refresh", response=WebSignInResponse)
def web_token_refresh(request: HttpRequest) -> dict:
    cookie = request.COOKIES.get(ninja_simple_jwt_settings.JWT_REFRESH_COOKIE_NAME)
    if cookie is None:
        raise AuthenticationError()
    access_token, _ = get_access_token_from_refresh_token(cookie)
    return {"access": access_token}
