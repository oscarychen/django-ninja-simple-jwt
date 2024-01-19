##### Why are the web endpoints designed to handle access and refresh tokens like this?

The short answer is security in depth.

- Web storage (local storage and session storage) is accessible through Javascript on the same domain, this presents an
opportunity for malicious scripts running on your site to carry out XSS against your user clients, which makes web
storage not ideal for storing either access or refresh tokens. There are a large number of scenarios where XSS can take
place, and a number of ways to mitigate them.
you can read more about XSS [here](https://gist.github.com/oscarychen/352d60c1a2e3727d444c94b5959bb6f6).
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
- Refresh tokens, by default are sent back to client in a `HttpOnly` cookie header that the client browser sees but
inaccessible by your own frontend application. This way, the refresh token is not subject to any XSS attack against
your application. While CSRF is possible, the attacker cannot use this mechanism to make modification to your resources
even is a CSRF attack is successfully carried out. It is important to note that in CSRF, the attacker cannot read the
response even when they successfully make the malicious request to your API endpoint; the worst they can do is to
refresh the token on user's behalf, and no damage can be done on user resources. The refresh token cookie by default
also have `path` attributes specified using the [`WEB_REFRESH_COOKIE_PATH`](settings.md#webrefreshcookiepath) setting, so that browsers should only attach
them with request to your specific url path used for refreshing the tokens, therefore reducing attack surfaces further.
