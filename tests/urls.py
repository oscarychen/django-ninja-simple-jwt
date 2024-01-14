from django.urls import path
from ninja import NinjaAPI

from ninja_simple_jwt.auth.views.api import mobile_auth_router, web_auth_router

api = NinjaAPI()
api.add_router("/auth/mobile/", mobile_auth_router)
api.add_router("/auth/web/", web_auth_router)


urlpatterns = [path("api/", api.urls)]
