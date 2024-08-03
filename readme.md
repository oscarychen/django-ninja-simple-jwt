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

Expose `Django-ninja`'s API and add `ninja_simple_jwt`'s auth API endpoint router to the API, ie:
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

_If you are not exposing the API and routers at the exact path as the example above,
see [`WEB_REFRESH_COOKIE_PATH`](docs/settings.md#webrefreshcookiepath) setting regarding web auth token refresh path._

To protect a resource API, you can use the `HttpJwtAuth` as the auth argument when instantiating a Router, ie:
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


## Documentation

### Customizing JWT key storage
By default, the management command `make_rsa` will create and store the JWT key pairs in the root of your project
directory, this is only intended for development.

Here is an example how you can store the keys in a S3 bucket somewhere only your application has access to, assuming
you are using `django-storages` to access AWS S3.

```python
# some_project_dir/my_jwt_key_storage.py

from storages.backends.s3boto3 import S3Boto3Storage

aws_s3_private_key_storage = S3Boto3Storage(bucket_name="MySecretJwtKeysStorage")
aws_s3_public_key_storage = S3Boto3Storage(bucket_name="MyPublicJwtKeysStorage")
```
and provide the above storage instances in Django settings:
```python
# settings.py

NINJA_SIMPLE_JWT = {
    "JWT_PRIVATE_KEY_STORAGE": "some_project_dir.my_jwt_key_storage.aws_s3_private_key_storage",
    "JWT_PUBLIC_KEY_STORAGE": "some_project_dir.my_jwt_key_storage.aws_s3_public_key_storage",
    ...
}
```
You can provide any custom storage implementation in this setting provided that they follow Django's Storage API.

_You should make sure that the private key storage is only accessible by the auth service application.
The public key storage may be made accessible by other services that need to verify the JWT issued by the auth service._


### Enabling auth API endpoints

#### Mobile
You can enable the mobile auth end points by adding a provided router to the ninja API class:
```python
# urls.py

from ninja import NinjaAPI
from ninja_simple_jwt.auth.views.api import mobile_auth_router
from django.urls import path

api = NinjaAPI()
api.add_router("/auth/mobile/", mobile_auth_router)


urlpatterns = [path("api/", api.urls)]
```
In the above example with the `mobile_auth_router`, you would gain the following endpoints:
- /api/auth/mobile/sign-in

```commandline
curl --location 'http://127.0.0.1:8000/api/auth/mobile/sign-in' \
--header 'Content-Type: application/json' \
--data '{
    "username": "my-username",
    "password": "my-password"
}'
```
The response would contain refresh and access JWT in the body:
```json
{
    "refresh": "...",
    "access": "..."
}
```

- /api/auth/mobile/token-refresh

```commandline
curl --location 'http://127.0.0.1:8000/api/auth/mobile/token-refresh' \
--header 'Content-Type: application/json' \
--data '{
    "refresh": "..."
}'
```
The response would contain an access JWT in the body:
```json
{
  "access": "..."
}
```

#### Web
_See also: [web auth endpoint design](docs/auth_api_design.md#why-are-the-web-endpoints-designed-to-handle-access-and-refresh-tokens-like-this)._

Similarly to the Mobile auth end point example above,
you can enable the web auth endpoints by adding it to the ninja API class:
```python
# urls.py

from ninja import NinjaAPI
from ninja_simple_jwt.auth.views.api import web_auth_router
from django.urls import path

api = NinjaAPI()
api.add_router("/auth/web/", web_auth_router)

urlpatterns = [path("api/", api.urls)]
```
You would gain the following endpoints:
- /api/auth/web/sign-in
```commandline
curl --location 'http://127.0.0.1:8000/api/auth/web/sign-in' \
--header 'Content-Type: application/json' \
--data '{
    "username": "my-username",
    "password": "my-password"
}'
```
The response would contain the access JWT in the body, however the refresh JWT is only in a cookie:
```
refresh=...; expires=Fri, 09 Feb 2024 03:49:33 GMT; HttpOnly; Max-Age=2591999; Path=/api/auth/web/token-refresh; SameSite=Strict
```
By default, this refresh cookie is only used when calling the token refresh endpoint (below).
- /api/auth/web/token-refresh
```commandline
curl --location --request POST 'http://127.0.0.1:8000/api/auth/web/token-refresh' \
--header 'Cookie: refresh=...'
```
The response would contain an access token in the body.

### Customizing token claims for user
You can specify a claim on the JWT and what User model attribute to get the claim value from using the
setting `TOKEN_CLAIM_USER_ATTRIBUTE_MAP`.
By default, this setting has the following value:
```python
{
    # claim: model attribute
    "user_id": "id",
    "username": "username",
    "last_login": "last_login",
}
```
The mapping can also take a function as the value, ie:
```python
{
    "full_name": lambda user: user.first_name + " " + user.last_name,
}
```
#### Serializing user attribute into JWT claim
If the model attribute is not by default serializeable, you can specify how to serialize it by providing a custom
implementation of json encoder class. Ie:
```python
# some_directory/custom_encoders.py

from ninja_simple_jwt.jwt.json_encode import TokenUserEncoder

class CustomTokenUserEncoder(TokenUserEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, SomeCustomClass):
            return self.serialize_some_custom_class(o)

        return super().default(o)

    def serialize_some_custom_class(self, o: SomeCustomClass) -> str:
        # custom serialization implementation here
        return "serialized value"
```
And then provide the import string for this class in Django setting:
```python
# settings.py

NINJA_SIMPLE_JWT = {
    ...,
    "TOKEN_USER_ENCODER_CLS": "some_directory.custom_encoders.CustomTokenUserEncoder"
}
```

## Settings

All settings specific for this library are stored as key-value pairs under Django setting `NINJA_SIMPLE_JWT`, ie:

```python
# settings.py
NINJA_SIMPLE_JWT = {
    ...
}
```

See [list of all available settings](docs/settings.md).
