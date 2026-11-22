# --- AED: public demo of the portal fork under one domain (docker-compose.aed-domain.yml) ---
# Appended to mcod/settings/local.py by aed-domain/init-env.sh; DJANGO_SETTINGS_MODULE stays mcod.settings.local.
# Not a separate settings module: mcod/__init__.py reads django settings while it is imported, so a module outside
# the mcod package that imports mcod.settings.local is still half-loaded when `manage.py` needs it
# ("SECRET_KEY must not be empty", "Models aren't loaded yet"). Instruction: docs/wdrozenie-serwer.md.
# Changes only what a public HTTPS domain needs: cookie domain, CSRF origins, no debug pages, login throttling.
AED_DOMAIN = env("AED_DOMAIN")  # noqa: F405

# local.py forces DEBUG=True; debug pages must not be public. AED_DEBUG=yes only while diagnosing.
DEBUG = env.bool("AED_DEBUG", default=False)  # noqa: F405
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG  # noqa: F405

# local.py pins cookies to mcod.local over plain HTTP; the browser would drop them on the real domain.
SESSION_COOKIE_DOMAIN = AED_DOMAIN
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
NO_REPLY_EMAIL = "no-reply@" + AED_DOMAIN  # local.py: no-reply@mcod.local
API_CSRF_COOKIE_DOMAINS = [AED_DOMAIN]
API_CSRF_TRUSTED_ORIGINS = [AED_DOMAIN]

# local.py switches the login lockout off; on the internet the admin panel keeps it (5 attempts, 1 hour).
AXES_ENABLED = COMPONENT in ("admin", "cms")  # noqa: F405
