# django-ninja-simple-jwt

Provides simple JWT based stateless authentication for Django-ninja

## Quick start

Install package:
```commandline
pip install django-ninja-simple-jwt
```
add `ninja_simple_jwt` to list of `INSTALLED_APPS` in Django settings:
```python
# settings.py

INSTALLED_APPS = [
    ...,
    "ninja_simple_jwt"
]
```

Expose `Django-ninja`'s API and add `ninja_simple_jwt`;s auth API endpoint router to the API, ie:
```python
# urls.py

from ninja import NinjaAPI
from ninja_simple_jwt.auth.views.api import auth_router
from django.urls import path

api = NinjaAPI()
api.add_router("/auth/", auth_router)

urlpatterns = [path("api/", api.urls)]
```
This would provide 4 available auth API endpoints for mobile and web sign in and token refresh:
- {{server_url}}/api/auth/mobile/sign-in
- {{server_url}}/api/auth/mobile/token-refresh
- {{server_url}}/api/auth/web/sign-in
- {{server_url}}/api/auth/web/token-refresh

Finally, to provide a resource API, you can use the `HttpJwtAuth` as the auth argument when instantiating a Router, ie:
```python
# views.py

from ninja_simple_jwt.auth.ninja_auth import HttpJwtAuth
from ninja import Router

some_resource_router = Router(auth=HttpJwtAuth())

@some_resource_router.get("/hello")
def hello(request):
    return "Hello world"
```
