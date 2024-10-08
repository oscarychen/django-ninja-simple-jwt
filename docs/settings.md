# ninja_simple_jwt settings

### JWT_PRIVATE_KEY_STORAGE
Storage class instance used to store JWT private signing key. Defaults to `"ninja_simple_jwt.jwt.key_store.local_disk_key_storage"`.

### JWT_PUBLIC_KEY_STORAGE
Storage class instance used to store JWT public verification key. Defaults to `"ninja_simple_jwt.jwt.key_store.local_disk_key_storage"`.

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
This is the path set on the cookie for refresh token, this path needs to match the url endpoints you are exposing for
web token refresh and web sign out. Defaults to `"/api/auth/web"`.

### USERNAME_FIELD
This is the field on the User model that is used as the username. Defaults to `"username"`.

### TOKEN_CLAIM_USER_ATTRIBUTE_MAP
A dictionary mapping token claims to corresponding User model attributes. Defaults to the following which are part
of Django's default User model:
```python
{
    "user_id": "id",
    "username": "username",
    "first_name": "first_name",
    "last_name": "last_name",
    "email": "email",
    "is_staff": "is_staff",
    "is_superuser": "is_superuser",
    "last_login": "last_login",
    "date_joined": "date_joined",
    "is_active": "is_active",
}
```
If you changed any of these attributes in your Django user model, you will need to update this dictionary accordingly.

See also: [Customizing token claims for user](../readme.md#customizing-token-claims-for-user).

### TOKEN_USER_ENCODER_CLS
JSON encoder class used to serializing User attributes to JWT claims.
See [Serializing user attribute into JWT claim](../readme.md#serializing-user-attribute-into-jwt-claim)
