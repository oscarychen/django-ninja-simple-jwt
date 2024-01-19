# ninja_simple_jwt settings

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
See [Customizing token claims for user](../readme.md#customizing-token-claims-for-user).

### TOKEN_USER_ENCODER_CLS
JSON encoder class used to serializing User attributes to JWT claims.
See [Serializing user attribute into JWT claim](../readme.md#serializing-user-attribute-into-jwt-claim)
