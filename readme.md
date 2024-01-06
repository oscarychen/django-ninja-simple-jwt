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
from ninja_simple_jwt.auth.views.api import mobile_auth_router, web_auth_router
from django.urls import path

api = NinjaAPI()
api.add_router("/auth/mobile/", mobile_auth_router)
api.add_router("/auth/web/", web_auth_router)

urlpatterns = [path("api/", api.urls)]
```
This would provide 4 available auth API endpoints for mobile and web sign in and token refresh:
- {{server_url}}/api/auth/mobile/sign-in
- {{server_url}}/api/auth/mobile/token-refresh
- {{server_url}}/api/auth/web/sign-in
- {{server_url}}/api/auth/web/token-refresh

To provide a resource API, you can use the `HttpJwtAuth` as the auth argument when instantiating a Router, ie:
```python
# views.py

from ninja_simple_jwt.auth.ninja_auth import HttpJwtAuth
from ninja import Router

some_resource_router = Router(auth=HttpJwtAuth())

@some_resource_router.get("/hello")
def hello(request):
    return "Hello world"
```

Finally, before starting up the server, create a key pair to be used by the server for signing and verifying JWT:
```commandline
python manage.py make_rsa
```
You should see two files created in the root of project repository:
- jwt-signing.pem  # this is the private key used to sign a JWT, keep this secret, store appropriately
- jwt-signing.pub  # this is the public key used to verify a JWT
