"""Start the demo server: python -m aed_service (port from AED_PORT, default 8085)."""
import os
from wsgiref.simple_server import WSGIRequestHandler, make_server

from .app import create_app

if __name__ == "__main__":
    port = int(os.environ.get("AED_PORT", "8085"))
    app = create_app()
    print("Seed done, listening on http://localhost:%d/api/aed" % port, flush=True)
    # ponytail: single-threaded wsgiref, enough for a demo; use gunicorn/waitress for load.
    with make_server("", port, app, handler_class=WSGIRequestHandler) as srv:
        srv.serve_forever()
