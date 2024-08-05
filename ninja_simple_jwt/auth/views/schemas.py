from ninja import Schema


class SignInRequest(Schema):
    username: str
    password: str


class MobileSignInResponse(Schema):
    refresh: str
    access: str


class MobileTokenRefreshRequest(Schema):
    refresh: str


class MobileTokenRefreshResponse(Schema):
    access: str


class WebSignInResponse(Schema):
    access: str


class Empty(Schema):
    pass
