"""Django settings for the public demo of the portal fork under one domain (docker-compose.aed-domain.yml).

Mounted into the portal containers as /usr/src/mcod_backend/aed_domain_settings.py and selected with
DJANGO_SETTINGS_MODULE=aed_domain_settings. Builds on mcod.settings.local (copy local.py.sample first) and changes
only what a public HTTPS domain needs: cookie domain, CSRF origins, no debug pages, login throttling.
Instruction: docs/wdrozenie-serwer.md.
"""
from mcod.settings.local import *  # noqa: F401,F403
from mcod.settings.local import COMPONENT, TEMPLATES, env

AED_DOMAIN = env("AED_DOMAIN")

# local.py forces DEBUG=True; debug pages must not be public. AED_DEBUG=yes only while diagnosing.
DEBUG = env.bool("AED_DEBUG", default=False)
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG

# local.py pins cookies to mcod.local over plain HTTP; the browser would drop them on the real domain.
SESSION_COOKIE_DOMAIN = AED_DOMAIN
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
API_CSRF_COOKIE_DOMAINS = [AED_DOMAIN]
API_CSRF_TRUSTED_ORIGINS = [AED_DOMAIN]

# local.py switches the login lockout off; on the internet the admin panel keeps it (5 attempts, 1 hour).
AXES_ENABLED = COMPONENT in ("admin", "cms")
