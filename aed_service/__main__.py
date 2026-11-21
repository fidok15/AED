"""Start the demo server: python -m aed_service (port from AED_PORT, default 8085).

AED_CYCLE_HOURS: hours between scheduled runs of download + mapper + reminders (default 24, 0 = off).
AED_DEMO_SEED: 0/false/no disables the fictional demo devices (default on).
AED_FEED_DIR, AED_FEED_URL: directory and its public HTTPS address; when both are set, every scheduled cycle rewrites
the dane.gov.pl harvester feed there (see aed_service/feed.py).
"""
import os
from wsgiref.simple_server import WSGIRequestHandler, make_server

from .app import create_app, db_file, start_scheduler

if __name__ == "__main__":
    port = int(os.environ.get("AED_PORT", "8085"))
    demo = os.environ.get("AED_DEMO_SEED", "1").lower() not in ("0", "false", "no")
    app = create_app(demo=demo)
    hours = float(os.environ.get("AED_CYCLE_HOURS", "24"))
    start_scheduler(db_file(), hours)
    print("Seed done, scheduler every %sh, listening on http://localhost:%d/api/aed" % (hours or "off", port), flush=True)
    # ponytail: single-threaded wsgiref, enough for a demo; use gunicorn/waitress for load.
    with make_server("", port, app, handler_class=WSGIRequestHandler) as srv:
        srv.serve_forever()
