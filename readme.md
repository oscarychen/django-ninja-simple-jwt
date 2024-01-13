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
see [`WEB_REFRESH_COOKIE_PATH`](#WEB_REFRESH_COOKIE_PATH) setting regarding web auth token refresh path._

_See more regarding the web auth endpoint design in [documentation below](#why-are-the-web-endpoints-designed-to-handle-access-and-refresh-tokens-like-this)._


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

aws_s3_key_storage = S3Boto3Storage(bucket_name="MySecretJwtKeysStorage")
```
and provide the above storage instance in Django settings:
```python
# settings.py

NINJA_SIMPLE_JWT = {
    "JWT_KEY_STORAGE": "some_project_dir.my_jwt_key_storage.aws_s3_key_storage",
    ...
}
```
You can provide any custom storage implementation in this setting provided that they follow Django's Storage API.

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
    "acess": "..."
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

##### Why are the web endpoints designed to handle access and refresh tokens like this?

The short answer is security in depth.

- Web storage (local storage and session storage) is accessible through Javascript on the same domain, this presents an
opportunity for malicious scripts running on your site to carry out XSS against your user clients, which makes web
storage not ideal for storing either access or refresh tokens. There are a large number of scenarios where XSS can take
place, and a number of ways to mitigate them. you can read more about XSS [here](https://gist.github.com/oscarychen/352d60c1a2e3727d444c94b5959bb6f6).
- Cookies with `HttpOnly` flag are not accessible by Javascript and therefore not vulnerable to XSS, however they may be
the target of CSRF attack because of ambient authority, where cookies may be attached to requests automatically. Even
though a malicious website carrying out a CSRF has no way of reading the response of the request which is made on behalf
of a user, they may be able to make changes to user data resources if such endpoints exist. This makes `HttpOnly`
cookies unsuited for storing access token. There are several ways to mitigate CSRF, such as setting the `SameSite`
attribute of a cookie to "Lax" or "Strict", and using anti-CSRF token. You can read more about CSRF [here](https://gist.github.com/oscarychen/ce189b2fef1f8ff7eac51a72fed34960).

In addition to various XSS and CSRF mitigation techniques, this package deploys access token and refresh token for web
apps in a specific way that broadly hardens application security against these attacks:
- Access tokens, are as usual, send back to clients in response body. It is expected that you would design your frontend
application to not persist access tokens anywhere. They are short-lived and only used by the SPA in memory, and are
tossed as soon as the user close the browser tab. This way, the access token cannot be utilized in a CSRF attack against
your application.
- Refresh tokens, are sent back to client in a `HttpOnly` cookie header that the client browser sees but inaccessible
by your own frontend application. This way, the refresh token is not subject to any XSS attack against your application.
While CSRF is possible, the attacker cannot use this mechanism to make modification to your resources even is a CSRF
attack is successfully carried out. It is important to note that in CSRF, the attacker cannot read the response even
when they successfully make the malicious request to your API endpoint; the worst they can do is to refresh the token
on user's behalf, and no damage can be done. The refresh token cookie would also typically have `domain` and `path`
attributes specified, so that browsers should only attach them with request to your domain and specific url path
used for refreshing the tokens, therefore reducing attack surfaces further.

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
#### Serializing user attribute into JWT claim
If the model attribute is not by default serializeable, you can specify how to serialize it by providing a custom
implementation of json encoder class. Ie:
```python
# some_directory/custom_encoders.py

from ninja_simple_jwt.jwt.json_encode import TokenUserEncoder

class CustomTokenUserEncoder(TokenUserEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, SomeCustomClass):
            return str(o)  # custom serialization implementation here

        return super().default(o)
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

All settings specific for this library is stored as key-value pairs under Django setting `NINJA_SIMPLE_JWT`, ie:

```python
# settings.py
NINJA_SIMPLE_JWT = {
    ...
}
```

### JWT_KEY_STORAGE
Storage class instance used to store JWT key pairs. Defaults to `"ninja_simple_jwt.jwt.key_store.local_disk_key_storage"`.

### JWT_PRIVATE_KEY_PATH
Path to the private key, defaults to `"jwt-signing.pem"`.

### JWT_PUBLIC_KEY_PATH
Path to the public key, defaults to `"jwt-signing.pub"`.

### JWT_REFRESH_COOKIE_NAME
Name of the refresh cookie (used only by web auth endpoints), defaults to `"refresh"`.


### JWT_REFRESH_TOKEN_LIFETIME
Defaults to `timedelta(days=30)`.

### JWT_ACCESS_TOKEN_LIFETIME
Defaults to `timedelta(minutes=15)`

### WEB_REFRESH_COOKIE_SECURE
Whether to use secure cookie for refresh token, defaults to `not settings.DEBUG`.

### WEB_REFRESH_COOKIE_HTTP_ONLY
Whether to use httponly cookie for refresh token, defaults to `True`.

### WEB_REFRESH_COOKIE_SAME_SITE_POLICY
Same-site policy to be used for refresh token cookie, defaults to `"Strict"`.

### WEB_REFRESH_COOKIE_PATH
This is the path set on the cookie for refresh token, this path needs to match the url endpoint you are exposing for
web token refresh. Defaults to `"/api/auth/web/token-refresh"`.

### TOKEN_CLAIM_USER_ATTRIBUTE_MAP
A dictionary mapping token claims to corresponding User model attributes. Defaults to the following:
```python
{
    "user_id": "id",
    "username": "username",
    "last_login": "last_login",
}
```
See [Customizing token claims for user](#customizing-token-claims-for-user).

### TOKEN_USER_ENCODER_CLS
JSON encoder class used to serializing User attributes to JWT claims.
See [Serializing user attribute into JWT claim](#serializing-user-attribute-into-jwt-claim)
