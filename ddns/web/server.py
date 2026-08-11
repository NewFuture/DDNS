# -*- coding: utf-8 -*-
"""Local-only HTTP server for the embedded DDNS dashboard."""

from __future__ import unicode_literals

import binascii
import json
import logging
import os
import pkgutil
import socket
import sys
import threading
import time
import webbrowser

try:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn
    from urllib.parse import urlparse
except ImportError:  # Python 2
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from SocketServer import ThreadingMixIn
    from urlparse import urlparse

from .service import DashboardError, DashboardService

try:
    text_type = unicode  # type: ignore[name-defined]
except NameError:
    text_type = str


STATIC_ASSETS = {
    "/assets/dashboard.css": ("dashboard.css", "text/css; charset=utf-8"),
    "/assets/dashboard.js": ("dashboard.js", "application/javascript; charset=utf-8"),
    "/assets/ddns.svg": ("ddns.svg", "image/svg+xml"),
}
INDEX_PATHS = ("/", "/index.html", "/dashboard", "/dashboard/")
MAX_BODY_SIZE = 2 * 1024 * 1024
LAUNCH_PATH_PREFIX = "/launch/"
LAUNCH_TOKEN_TTL = 60
SOURCE_ASSET_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "web"))
PACKAGED_ASSET_ROOT = os.path.join(os.path.dirname(__file__), "static")


def _write_stdout(message):
    # type: (str) -> None
    """Write Unicode status text on Python 2 and Python 3."""
    try:
        sys.stdout.write(message)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or sys.getfilesystemencoding() or "utf-8"
        encoded = message.encode(encoding, "replace")
        sys.stdout.write(encoded if sys.version_info[0] < 3 else encoded.decode(encoding))
    sys.stdout.flush()


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """HTTP server that keeps slow dashboard operations isolated."""

    allow_reuse_address = False
    daemon_threads = True

    def server_bind(self):
        # type: () -> None
        if sys.platform.startswith("win") and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        HTTPServer.server_bind(self)

    def issue_launch_token(self):
        # type: () -> str
        """Create a short-lived, single-use browser bootstrap token."""
        token = binascii.hexlify(os.urandom(24)).decode("ascii")
        with self.launch_token_lock:
            self.launch_token = token
            self.launch_token_expires = time.time() + LAUNCH_TOKEN_TTL
        return token

    def consume_launch_token(self, token):
        # type: (str) -> bool
        """Consume the current browser bootstrap token exactly once."""
        with self.launch_token_lock:
            valid = token == self.launch_token and time.time() <= self.launch_token_expires
            if valid:
                self.launch_token = None
                self.launch_token_expires = 0
            return valid


class ThreadingHTTPServerV6(ThreadingHTTPServer):
    """IPv6 loopback variant of the dashboard server."""

    address_family = socket.AF_INET6


def _resource_file_bytes(root, asset_name):
    # type: (str, str) -> bytes | None
    segments = asset_name.split("/")
    if not asset_name or any(segment in ("", ".", "..") for segment in segments):
        raise IOError("Invalid dashboard asset path: {}".format(asset_name))
    asset_path = os.path.join(root, *segments)
    if not os.path.isfile(asset_path):
        return None
    with open(asset_path, "rb") as asset_file:
        return asset_file.read()


def _resource_bytes(asset_name):
    # type: (str) -> bytes
    for asset_root in (SOURCE_ASSET_ROOT, PACKAGED_ASSET_ROOT):
        content = _resource_file_bytes(asset_root, asset_name)
        if content is not None:
            return content
    resource_path = "static/{}".format(asset_name)
    content = pkgutil.get_data("ddns.web", resource_path)
    if content is None:
        raise IOError("Embedded dashboard resource not found: {}".format(resource_path))
    return content


def _json_bytes(payload):
    # type: (dict | list) -> bytes
    content = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if not isinstance(content, bytes):
        content = content.encode("utf-8")
    return content


def _local_hostname(host_header):
    # type: (str) -> bool
    try:
        hostname = urlparse("http://{}".format(host_header)).hostname
    except (AttributeError, TypeError, ValueError):
        return False
    return hostname in ("127.0.0.1", "localhost", "::1")


class DashboardRequestHandler(BaseHTTPRequestHandler):
    """Serve the dashboard and its same-origin JSON API."""

    protocol_version = "HTTP/1.1"
    server_version = "DDNS"
    sys_version = ""

    @property
    def service(self):
        # type: () -> DashboardService
        return self.server.dashboard_service  # type: ignore[attr-defined]

    @property
    def access_token(self):
        # type: () -> str
        return self.server.access_token  # type: ignore[attr-defined]

    def log_message(self, format_string, *args):
        # type: (str, *object) -> None
        self.server.logger.info("%s - %s", self.address_string(), format_string % args)  # type: ignore[attr-defined]

    def _security_headers(self):
        # type: () -> None
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Permissions-Policy", "camera=(), geolocation=(), microphone=()")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self'; "
            "script-src 'self'; connect-src 'self'; base-uri 'none'; "
            "frame-ancestors 'none'; form-action 'self'; object-src 'none'",
        )

    def _send_bytes(self, status, content, content_type, cache_control="no-store", head_only=False):
        # type: (int, bytes, str, str, bool) -> None
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", cache_control)
        self._security_headers()
        self.end_headers()
        if not head_only:
            self.wfile.write(content)

    def _send_json(self, status, payload, head_only=False):
        # type: (int, dict | list, bool) -> None
        self._send_bytes(status, _json_bytes(payload), "application/json; charset=utf-8", head_only=head_only)

    def _send_redirect(self, location):
        # type: (str) -> None
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.send_header("Cache-Control", "no-store")
        self._security_headers()
        self.end_headers()

    def _send_dashboard_error(self, error):
        # type: (DashboardError) -> None
        self._send_json(error.status, {"error": {"code": error.code, "message": text_type(error)}})

    def _send_not_found(self):
        # type: () -> None
        self._send_json(404, {"error": {"code": "not_found", "message": "Resource not found."}})

    def _request_is_local(self):
        # type: () -> bool
        host_header = self.headers.get("Host", "")
        if _local_hostname(host_header):
            return True
        self._send_json(421, {"error": {"code": "invalid_host", "message": "Dashboard only accepts local hosts."}})
        return False

    def _request_has_token(self):
        # type: () -> bool
        if self.headers.get("X-DDNS-Token") == self.access_token:
            return True
        self._send_json(403, {"error": {"code": "invalid_token", "message": "Dashboard request token is invalid."}})
        return False

    def _read_json(self):
        # type: () -> dict
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            error = DashboardError("Content-Type must be application/json.")
            error.status = 415
            error.code = "unsupported_media_type"
            raise error
        content_length = self.headers.get("Content-Length")
        if content_length is None:
            error = DashboardError("Content-Length is required.")
            error.status = 411
            error.code = "length_required"
            raise error
        try:
            content_length = int(content_length)
        except (TypeError, ValueError):
            error = DashboardError("Content-Length is invalid.")
            error.status = 400
            error.code = "invalid_length"
            raise error
        if content_length < 0 or content_length > MAX_BODY_SIZE:
            error = DashboardError("Request body is too large.")
            error.status = 413
            error.code = "payload_too_large"
            raise error
        content = self.rfile.read(content_length)
        try:
            payload = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, TypeError, ValueError):
            error = DashboardError("Request body must contain valid UTF-8 JSON.")
            error.status = 400
            error.code = "invalid_json"
            raise error
        if not isinstance(payload, dict):
            error = DashboardError("Request body must be a JSON object.")
            error.status = 400
            error.code = "invalid_json"
            raise error
        return payload

    def _handle_get(self, head_only=False):
        # type: (bool) -> None
        if not self._request_is_local():
            return
        path = urlparse(self.path).path
        if path.startswith(LAUNCH_PATH_PREFIX):
            launch_token = path[len(LAUNCH_PATH_PREFIX) :]
            if head_only or not self.server.consume_launch_token(launch_token):  # type: ignore[attr-defined]
                self._send_json(
                    403,
                    {"error": {"code": "invalid_launch_token", "message": "Dashboard launch token is invalid."}},
                    head_only=head_only,
                )
                return
            self._send_redirect("/#token={}&view=overview".format(self.access_token))
            return
        if path in INDEX_PATHS:
            content = _resource_bytes("index.html")
            self._send_bytes(200, content, "text/html; charset=utf-8", head_only=head_only)
            return
        if path in STATIC_ASSETS:
            resource_path, content_type = STATIC_ASSETS[path]
            self._send_bytes(
                200, _resource_bytes(resource_path), content_type, cache_control="no-cache", head_only=head_only
            )
            return
        if path.startswith("/api/") and not self._request_has_token():
            return
        if path == "/api/dashboard":
            self._send_json(200, self.service.dashboard(), head_only=head_only)
            return
        if path == "/api/config":
            self._send_json(200, self.service.config_state(), head_only=head_only)
            return
        self._send_not_found()

    def do_GET(self):
        # type: () -> None
        try:
            self._handle_get()
        except DashboardError as error:
            self._send_dashboard_error(error)
        except (IOError, OSError) as error:
            self.server.logger.exception("Dashboard resource failure")  # type: ignore[attr-defined]
            self._send_json(500, {"error": {"code": "resource_error", "message": text_type(error)}})

    def do_HEAD(self):
        # type: () -> None
        try:
            self._handle_get(head_only=True)
        except DashboardError as error:
            self._send_dashboard_error(error)
        except (IOError, OSError) as error:
            self.server.logger.exception("Dashboard resource failure")  # type: ignore[attr-defined]
            self._send_json(500, {"error": {"code": "resource_error", "message": text_type(error)}}, head_only=True)

    def do_PUT(self):
        # type: () -> None
        if not self._request_is_local() or not self._request_has_token():
            return
        path = urlparse(self.path).path
        if path != "/api/config":
            self._send_not_found()
            return
        try:
            payload = self._read_json()
            self._send_json(200, self.service.save(payload.get("config")))
        except DashboardError as error:
            self._send_dashboard_error(error)
        except (IOError, OSError) as error:
            self.server.logger.exception("Dashboard configuration write failure")  # type: ignore[attr-defined]
            self._send_json(500, {"error": {"code": "write_error", "message": text_type(error)}})

    def do_POST(self):
        # type: () -> None
        if not self._request_is_local() or not self._request_has_token():
            return
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path == "/api/sync":
                self._send_json(200, self.service.sync())
            elif path == "/api/config/validate":
                self._send_json(200, {"config": self.service.validate(payload.get("config"))})
            elif path == "/api/config/restore":
                self._send_json(200, self.service.restore_backup())
            elif path == "/api/scheduler":
                status = self.service.configure_scheduler(
                    payload.get("action", ""), payload.get("scheduler", "auto"), payload.get("interval", 5)
                )
                self._send_json(200, {"scheduler": status})
            else:
                self._send_not_found()
        except DashboardError as error:
            self._send_dashboard_error(error)
        except (IOError, OSError, RuntimeError, ValueError) as error:
            self.server.logger.exception("Dashboard operation failure")  # type: ignore[attr-defined]
            self._send_json(500, {"error": {"code": "operation_failed", "message": text_type(error)}})

    def do_OPTIONS(self):
        # type: () -> None
        self._send_json(405, {"error": {"code": "method_not_allowed", "message": "CORS is not enabled."}})


def create_server(service=None, host="127.0.0.1", port=9876, logger=None):
    # type: (DashboardService | None, str, int, logging.Logger | None) -> ThreadingHTTPServer
    """Create a local dashboard server without starting its loop."""
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("Dashboard host must be a loopback address.")
    logger = (logger or logging.getLogger()).getChild("web.server")
    server_class = ThreadingHTTPServerV6 if host == "::1" else ThreadingHTTPServer
    server = server_class((host, port), DashboardRequestHandler)
    server.dashboard_service = service or DashboardService(logger=logger)
    server.access_token = binascii.hexlify(os.urandom(24)).decode("ascii")
    server.launch_token_lock = threading.Lock()
    server.launch_token = None
    server.launch_token_expires = 0
    server.logger = logger
    return server


def serve(config_path=None, host="127.0.0.1", port=9876, open_browser=False, logger=None, interval=5):
    # type: (str | None, str, int, bool, logging.Logger | None, int) -> None
    """Run the embedded dashboard until interrupted."""
    logger = logger or logging.getLogger()
    service = DashboardService(config_path=config_path, logger=logger, scheduler_interval=interval)
    server = create_server(service=service, host=host, port=port, logger=logger)
    bound_host, bound_port = server.server_address[:2]
    display_host = "127.0.0.1" if bound_host == "0.0.0.0" else bound_host
    if ":" in display_host:
        display_host = "[{}]".format(display_host)
    origin = "http://{}:{}".format(display_host, bound_port)
    url = "{}/launch/{}".format(origin, server.issue_launch_token())
    try:
        service.start_scheduler()
        _write_stdout("DDNS dashboard: {}\n".format(url))
        _write_stdout("Config file: {}\n".format(service.config_path))
        if open_browser:
            webbrowser.open(url)
        server.serve_forever()
    except KeyboardInterrupt:
        _write_stdout("\nStopping DDNS dashboard...\n")
    finally:
        service.stop_scheduler()
        server.server_close()
