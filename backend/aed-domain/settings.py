# --- AED: public demo of the portal fork under one domain (docker-compose.aed-domain.yml) ---
# Appended to mcod/settings/local.py by aed-domain/init-env.sh; DJANGO_SETTINGS_MODULE stays mcod.settings.local.
# Not a separate settings module: mcod/__init__.py reads django settings while it is imported, so a module outside
# the mcod package that imports mcod.settings.local is still half-loaded when `manage.py` needs it
# ("SECRET_KEY must not be empty", "Models aren't loaded yet"). Instruction: docs/wdrozenie-serwer.md.
# Changes only what a public HTTPS domain needs: cookie domain, CSRF origins, no debug pages, login throttling.
AED_DOMAIN = env("AED_DOMAIN")  # noqa: F405
# Host names default to api./admin./cms.<AED_DOMAIN>. A flat scheme (aed-api.example.pl, ...) sets them explicitly:
# a free Cloudflare certificate covers one level of subdomains only (docs/wdrozenie-pve.md).
AED_API_HOST = env("AED_API_HOST", default="") or "api." + AED_DOMAIN  # noqa: F405
AED_ADMIN_HOST = env("AED_ADMIN_HOST", default="") or "admin." + AED_DOMAIN  # noqa: F405
AED_CMS_HOST = env("AED_CMS_HOST", default="") or "cms." + AED_DOMAIN  # noqa: F405

# local.py forces DEBUG=True; debug pages must not be public. AED_DEBUG=yes only while diagnosing.
DEBUG = env.bool("AED_DEBUG", default=False)  # noqa: F405
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG  # noqa: F405

# local.py pins cookies to mcod.local over plain HTTP; the browser would drop them on the real domain.
# The shared parent domain stays: the frontend logs in through the API and writes the admin panel's sessionid
# for the whole domain (frontend/src/app/services/rest.service.ts setToken), which is how the panel sees that login.
# With flat host names the hosts share no parent but the whole zone: AED_COOKIE_DOMAIN="" keeps cookies host-only.
SESSION_COOKIE_DOMAIN = env("AED_COOKIE_DOMAIN", default=AED_DOMAIN) or None  # noqa: F405
SESSION_COOKIE_SECURE = True
# base.py: False. Django's own session cookie is not readable by scripts on sibling hosts. Not tested under a real
# domain: the frontend's logout deletes sessionid from JS, which a browser refuses for an HttpOnly cookie.
SESSION_COOKIE_HTTPONLY = True
ALLOWED_HOSTS = [AED_DOMAIN, AED_API_HOST, AED_ADMIN_HOST, AED_CMS_HOST] + [
    "mcod-local-api", "mcod-local-admin", "mcod-local-cms", "localhost",  # container-to-container calls
]
CSRF_COOKIE_SECURE = True
NO_REPLY_EMAIL = "no-reply@" + AED_DOMAIN  # local.py: no-reply@mcod.local
API_CSRF_COOKIE_DOMAINS = [AED_DOMAIN]
API_CSRF_TRUSTED_ORIGINS = [AED_DOMAIN]

# local.py switches the login lockout off; on the internet the admin panel keeps it (5 attempts, 1 hour).
AXES_ENABLED = COMPONENT in ("admin", "cms")  # noqa: F405
