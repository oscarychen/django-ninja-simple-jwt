from ninja_simple_jwt.settings import ninja_simple_jwt_settings


def make_authentication_params(params: dict) -> dict:
    return {ninja_simple_jwt_settings.USERNAME_FIELD: params["username"], "password": params["password"]}
