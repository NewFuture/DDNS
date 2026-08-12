# -*- coding: utf-8 -*-
"""Offline process-level end-to-end tests for the DDNS CLI and dashboard."""

from __future__ import unicode_literals

import io
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time

from __init__ import unittest

try:
    from http.client import HTTPConnection
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn
    from urllib.parse import parse_qs, urlparse
except ImportError:  # Python 2
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from httplib import HTTPConnection
    from SocketServer import ThreadingMixIn
    from urlparse import parse_qs, urlparse


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
RUN_SCRIPT = os.path.join(PROJECT_ROOT, "run.py")
E2E_EXECUTABLE = os.environ.get("DDNS_E2E_EXECUTABLE")
if E2E_EXECUTABLE:
    E2E_EXECUTABLE = os.path.abspath(E2E_EXECUTABLE)
PROCESS_TIMEOUT = 60 if E2E_EXECUTABLE else 20
STARTUP_TIMEOUT = 60 if E2E_EXECUTABLE else 10
TEST_IPV4 = "192.0.2.44"
TEST_IPV6 = "2001:db8::44"
PROXY_ENVIRONMENT_KEYS = {"ALL_PROXY", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY"}


class _ProcessResult(object):
    """Captured result from a completed DDNS process."""

    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _FixtureState(object):
    """Thread-safe configuration and request state for the local HTTP fixture."""

    def __init__(self):
        self._lock = threading.Lock()
        self.reset()

    def reset(self):
        with self._lock:
            self._requests = []
            self._remote_documents = {}

    def record(self, request):
        with self._lock:
            self._requests.append(request)

    def set_remote_document(self, path, document):
        with self._lock:
            self._remote_documents[path] = document

    def remote_document(self, path):
        with self._lock:
            return self._remote_documents.get(path)

    def requests_for(self, path):
        with self._lock:
            return [request.copy() for request in self._requests if request["path"] == path]


class _ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    """Small concurrent HTTP server used by subprocess-based tests."""

    daemon_threads = True


class _FixtureHandler(BaseHTTPRequestHandler):
    """Serve deterministic IP, remote config, and callback endpoints."""

    protocol_version = "HTTP/1.1"

    def log_message(self, format_string, *args):
        pass

    def _read_body(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length) if content_length else b""
        return body.decode("utf-8")

    def _record(self, body=""):
        parsed = urlparse(self.path)
        self.server.state.record(
            {
                "method": self.command,
                "path": parsed.path,
                "query": parse_qs(parsed.query, keep_blank_values=True),
                "headers": dict(self.headers.items()),
                "body": body,
            }
        )
        return parsed.path

    def _send(self, status, body, content_type="text/plain; charset=utf-8"):
        if not isinstance(body, bytes):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self._record()
        remote_document = self.server.state.remote_document(path)
        if remote_document is not None:
            body = (
                remote_document
                if isinstance(remote_document, str)
                else json.dumps(remote_document, ensure_ascii=False, separators=(",", ":"))
            )
            self._send(200, body, "application/json; charset=utf-8")
        elif path == "/ip/invalid":
            self._send(200, "address unavailable")
        elif path == "/ip/v4":
            self._send(200, "current address: {}\n".format(TEST_IPV4))
        elif path == "/ip/v6":
            self._send(200, "{}\n".format(TEST_IPV6))
        elif path == "/callback/fail":
            self._send(400, "callback rejected")
        elif path.startswith("/callback/"):
            self._send(200, "callback accepted")
        else:
            self._send(404, "not found")

    def do_POST(self):
        body = self._read_body()
        path = self._record(body)
        if path == "/callback/fail":
            self._send(400, "callback rejected")
        elif path.startswith("/callback/"):
            self._send(200, "callback accepted")
        else:
            self._send(404, "not found")


class _BackgroundProcess(object):
    """Run and continuously drain a long-lived child process."""

    def __init__(self, command, cwd, env):
        self.process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0,
        )
        self._lock = threading.Lock()
        self._stdout = []
        self._stderr = []
        self._threads = [
            threading.Thread(target=self._drain, args=(self.process.stdout, self._stdout)),
            threading.Thread(target=self._drain, args=(self.process.stderr, self._stderr)),
        ]
        for thread in self._threads:
            thread.daemon = True
            thread.start()

    def _drain(self, stream, output):
        for line in iter(stream.readline, ""):
            with self._lock:
                output.append(line)
        stream.close()

    @property
    def stdout(self):
        with self._lock:
            return "".join(self._stdout)

    @property
    def stderr(self):
        with self._lock:
            return "".join(self._stderr)

    def wait_for_stdout(self, text, timeout=10):
        deadline = time.time() + timeout
        while time.time() < deadline:
            output = self.stdout
            if text in output:
                return output
            if self.process.poll() is not None:
                break
            time.sleep(0.05)
        raise AssertionError(
            "Process did not write {!r}.\nstdout:\n{}\nstderr:\n{}".format(text, self.stdout, self.stderr)
        )

    def stop(self, timeout=5):
        if self.process.poll() is None:
            if os.name == "nt":
                try:
                    self.process.send_signal(signal.CTRL_C_EVENT)
                except (AttributeError, OSError):
                    self.process.terminate()
            else:
                self.process.send_signal(signal.SIGINT)
        deadline = time.time() + timeout
        while self.process.poll() is None and time.time() < deadline:
            time.sleep(0.05)
        if self.process.poll() is None:
            self.process.terminate()
            deadline = time.time() + 2
            while self.process.poll() is None and time.time() < deadline:
                time.sleep(0.05)
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait()
        for thread in self._threads:
            thread.join(2)
        return self.process.returncode


class OfflineE2ETestCase(unittest.TestCase):
    """Shared isolated process and HTTP helpers."""

    @classmethod
    def setUpClass(cls):
        if E2E_EXECUTABLE and not os.path.isfile(E2E_EXECUTABLE):
            raise RuntimeError("DDNS E2E executable does not exist: {}".format(E2E_EXECUTABLE))
        cls.fixture_state = _FixtureState()
        cls.fixture_server = _ThreadingHTTPServer(("127.0.0.1", 0), _FixtureHandler)
        cls.fixture_server.state = cls.fixture_state
        cls.fixture_thread = threading.Thread(target=cls.fixture_server.serve_forever)
        cls.fixture_thread.daemon = True
        cls.fixture_thread.start()
        cls.fixture_url = "http://127.0.0.1:{}".format(cls.fixture_server.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.fixture_server.shutdown()
        cls.fixture_server.server_close()
        cls.fixture_thread.join(2)

    def setUp(self):
        self.fixture_state.reset()
        self.temp_dir = tempfile.mkdtemp(prefix="ddns-e2e-")
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)

    def _environment(self, overrides=None):
        env = os.environ.copy()
        for key in list(env):
            upper_key = key.upper()
            if (
                upper_key.startswith("DDNS_")
                or upper_key in PROXY_ENVIRONMENT_KEYS
                or upper_key in ("PYTHONHOME", "PYTHONPATH")
            ):
                del env[key]
        env.update(
            {
                "HOME": self.temp_dir,
                "USERPROFILE": self.temp_dir,
                "TMPDIR": self.temp_dir,
                "TEMP": self.temp_dir,
                "TMP": self.temp_dir,
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUNBUFFERED": "1",
            }
        )
        if not E2E_EXECUTABLE:
            env["PYTHONPATH"] = PROJECT_ROOT
        if overrides:
            env.update(overrides)
        return env

    def _command(self, arguments, entrypoint="module"):
        if E2E_EXECUTABLE:
            return [E2E_EXECUTABLE] + arguments
        if entrypoint == "script":
            return [sys.executable, RUN_SCRIPT] + arguments
        return [sys.executable, "-m", "ddns"] + arguments

    def _run(self, arguments, entrypoint="module", env=None, timeout=PROCESS_TIMEOUT):
        process = subprocess.Popen(
            self._command(arguments, entrypoint),
            cwd=self.temp_dir,
            env=env or self._environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding="utf-8",
            errors="replace",
        )
        timed_out = threading.Event()

        def kill_on_timeout():
            if process.poll() is None:
                timed_out.set()
                process.kill()

        timer = threading.Timer(timeout, kill_on_timeout)
        timer.daemon = True
        timer.start()
        try:
            stdout, stderr = process.communicate()
        finally:
            timer.cancel()
        if timed_out.is_set():
            self.fail("DDNS process timed out.\nstdout:\n{}\nstderr:\n{}".format(stdout, stderr))
        return _ProcessResult(process.returncode, stdout, stderr)

    def _start(self, arguments, env=None):
        process = _BackgroundProcess(self._command(arguments), self.temp_dir, env or self._environment())
        self.addCleanup(process.stop)
        return process

    def _write_config(self, name, config):
        path = os.path.join(self.temp_dir, name)
        with io.open(path, "w", encoding="utf-8") as config_file:
            json.dump(config, config_file, ensure_ascii=False, indent=2)
        return path

    def _callback_config(
        self, callback_path, domains=None, ipv6_domains=None, cache=False, token="", ttl=300, line="default"
    ):
        return {
            "dns": "callback",
            "id": self.fixture_url + callback_path,
            "token": token,
            "ipv4": domains or [],
            "index4": ["url:" + self.fixture_url + "/ip/v4"] if domains else False,
            "ipv6": ipv6_domains or [],
            "index6": ["url:" + self.fixture_url + "/ip/v6"] if ipv6_domains else False,
            "ttl": ttl,
            "line": line,
            "proxy": ["DIRECT"],
            "cache": cache,
            "ssl": False,
        }

    def assert_process_success(self, result):
        self.assertEqual(
            result.returncode,
            0,
            "Process failed with {}.\nstdout:\n{}\nstderr:\n{}".format(result.returncode, result.stdout, result.stderr),
        )

    def _unused_port(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]
        finally:
            sock.close()

    def _http_request(self, port, path, method="GET", payload=None, headers=None):
        request_headers = dict(headers or {})
        body = None
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
        connection = HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            connection.request(method, path, body=body, headers=request_headers)
            response = connection.getresponse()
            content = response.read().decode("utf-8")
            return response.status, dict(response.getheaders()), content
        finally:
            connection.close()


class TestCliE2E(OfflineE2ETestCase):
    """Exercise complete DDNS update flows through public process entrypoints."""

    def test_cli_only_dual_stack_and_rule_fallback(self):
        """Resolve both address families and fall back after an unusable rule."""
        result = self._run(
            [
                "--dns",
                "debug",
                "--no-cache",
                "--proxy",
                "DIRECT",
                "--index4",
                "url:" + self.fixture_url + "/ip/invalid",
                "url:" + self.fixture_url + "/ip/v4",
                "--ipv4",
                "First.Example.com",
                "second.example.com",
                "--index6",
                "url:" + self.fixture_url + "/ip/v6",
                "--ipv6",
                "v6.example.com",
            ],
            entrypoint="script",
        )

        self.assert_process_success(result)
        self.assertEqual(result.stdout.count("[IPv4] {}".format(TEST_IPV4)), 2)
        self.assertEqual(result.stdout.count("[IPv6] {}".format(TEST_IPV6)), 1)
        self.assertIn("first.example.com", result.stderr)
        self.assertIn("second.example.com", result.stderr)
        self.assertEqual(len(self.fixture_state.requests_for("/ip/invalid")), 1)
        self.assertEqual(len(self.fixture_state.requests_for("/ip/v4")), 1)
        self.assertEqual(len(self.fixture_state.requests_for("/ip/v6")), 1)

    def test_local_config_callback_post_and_cli_precedence(self):
        """Send a real callback request with CLI values overriding file values."""
        token = json.dumps(
            {
                "domain": "__DOMAIN__",
                "ip": "__IP__",
                "record_type": "__RECORDTYPE__",
                "ttl": "__TTL__",
                "line": "__LINE__",
            },
            separators=(",", ":"),
        )
        config = self._callback_config("/callback/local", ["file.example.com"], token=token, ttl=300, line="file")
        config_path = self._write_config("local.json", config)

        result = self._run(["-c", config_path, "--ipv4", "CLI.Example.com", "--ttl", "600"])

        self.assert_process_success(result)
        requests = self.fixture_state.requests_for("/callback/local")
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["method"], "POST")
        self.assertEqual(
            json.loads(requests[0]["body"]),
            {"domain": "cli.example.com", "ip": TEST_IPV4, "record_type": "A", "ttl": "600", "line": "file"},
        )
        self.assertNotIn("file.example.com", requests[0]["body"])

    def test_environment_configuration_with_cli_override(self):
        """Load a callback entirely from DDNS_* variables and override its domain."""
        callback_path = "/callback/environment"
        env = self._environment(
            {
                "DDNS_DNS": "callback",
                "DDNS_ID": self.fixture_url
                + callback_path
                + "?domain=__DOMAIN__&ip=__IP__&type=__RECORDTYPE__&ttl=__TTL__",
                "DDNS_TOKEN": "",
                "DDNS_IPV4": '["env.example.com"]',
                "DDNS_INDEX4": '["url:' + self.fixture_url + '/ip/v4"]',
                "DDNS_IPV6": "false",
                "DDNS_INDEX6": "false",
                "DDNS_TTL": "120",
                "DDNS_PROXY": '["DIRECT"]',
                "DDNS_CACHE": "false",
                "DDNS_SSL": "false",
            }
        )

        result = self._run(["--ipv4", "cli-env.example.com"], env=env)

        self.assert_process_success(result)
        requests = self.fixture_state.requests_for(callback_path)
        self.assertEqual(len(requests), 1)
        self.assertEqual(
            requests[0]["query"], {"domain": ["cli-env.example.com"], "ip": [TEST_IPV4], "type": ["A"], "ttl": ["120"]}
        )

    def test_remote_multi_provider_configuration(self):
        """Load a remote v4.1 document and execute every expanded provider."""
        second_token = json.dumps(
            {
                "domain": "__DOMAIN__",
                "ip": "__IP__",
                "record_type": "__RECORDTYPE__",
                "ttl": "__TTL__",
                "line": "__LINE__",
            },
            separators=(",", ":"),
        )
        remote_config = {
            "$schema": "https://ddns.newfuture.cc/schema/v4.1.json",
            "proxy": ["DIRECT"],
            "ssl": False,
            "cache": False,
            "ttl": 300,
            "line": "global",
            "providers": [
                {
                    "provider": "callback",
                    "id": self.fixture_url
                    + "/callback/remote-v4?domain=__DOMAIN__&ip=__IP__&type=__RECORDTYPE__&ttl=__TTL__&line=__LINE__",
                    "token": "",
                    "ipv4": ["remote-v4.example.com"],
                    "index4": ["url:" + self.fixture_url + "/ip/v4"],
                    "ipv6": [],
                    "index6": False,
                },
                {
                    "provider": "callback",
                    "id": self.fixture_url + "/callback/remote-v6",
                    "token": second_token,
                    "ipv4": [],
                    "index4": False,
                    "ipv6": ["remote-v6.example.com"],
                    "index6": ["url:" + self.fixture_url + "/ip/v6"],
                    "ttl": 600,
                    "line": "provider",
                },
            ],
        }
        remote_path = "/config/multi.json"
        self.fixture_state.set_remote_document(remote_path, remote_config)

        result = self._run(["-c", self.fixture_url + remote_path, "--proxy", "DIRECT"])

        self.assert_process_success(result)
        self.assertEqual(len(self.fixture_state.requests_for(remote_path)), 1)
        first = self.fixture_state.requests_for("/callback/remote-v4")
        second = self.fixture_state.requests_for("/callback/remote-v6")
        self.assertEqual(len(first), 1)
        self.assertEqual(
            first[0]["query"],
            {"domain": ["remote-v4.example.com"], "ip": [TEST_IPV4], "type": ["A"], "ttl": ["300"], "line": ["global"]},
        )
        self.assertEqual(len(second), 1)
        self.assertEqual(
            json.loads(second[0]["body"]),
            {
                "domain": "remote-v6.example.com",
                "ip": TEST_IPV6,
                "record_type": "AAAA",
                "ttl": "600",
                "line": "provider",
            },
        )

    def test_cache_skips_unchanged_callback_on_second_process(self):
        """Persist an address and avoid a duplicate provider update."""
        cache_path = os.path.join(self.temp_dir, "records.cache")
        config = self._callback_config(
            "/callback/cache?domain=__DOMAIN__&ip=__IP__&type=__RECORDTYPE__", ["cache.example.com"], cache=cache_path
        )
        config["cache_max_age"] = 3600
        config_path = self._write_config("cache.json", config)

        first = self._run(["-c", config_path])
        second = self._run(["-c", config_path])

        self.assert_process_success(first)
        self.assert_process_success(second)
        self.assertEqual(len(self.fixture_state.requests_for("/callback/cache")), 1)
        self.assertIn("using cache", second.stderr)
        with io.open(cache_path, "r", encoding="utf-8") as cache_file:
            self.assertEqual(json.load(cache_file), {"cache.example.com:A": TEST_IPV4})

    def test_multiple_configs_continue_after_failure_and_exit_nonzero(self):
        """Run all configurations but fail the process when one callback fails."""
        success_path = self._write_config(
            "success.json",
            self._callback_config(
                "/callback/success?domain=__DOMAIN__&ip=__IP__", ["success.example.com"], cache=False
            ),
        )
        failure_path = self._write_config(
            "failure.json",
            self._callback_config("/callback/fail?domain=__DOMAIN__&ip=__IP__", ["failure.example.com"], cache=False),
        )

        result = self._run(["-c", success_path, "-c", failure_path])

        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(self.fixture_state.requests_for("/callback/success")), 1)
        self.assertEqual(len(self.fixture_state.requests_for("/callback/fail")), 1)
        self.assertIn("Configuration 2 failed", result.stderr)
        self.assertIn("Some configurations failed", result.stderr)


class TestWebE2E(OfflineE2ETestCase):
    """Exercise the dashboard process and protected JSON API."""

    def test_dashboard_config_sync_and_scheduler_lifecycle(self):
        """Start the real dashboard, synchronize, and manage its scheduler."""
        port = self._unused_port()
        config_path = os.path.join(self.temp_dir, "dashboard.json")
        process = self._start(
            ["web", "--config", config_path, "--host", "127.0.0.1", "--port", str(port), "--interval", "30"]
        )
        output = process.wait_for_stdout("DDNS dashboard:", timeout=STARTUP_TIMEOUT)
        launch_url = next(
            line.split("DDNS dashboard:", 1)[1].strip() for line in output.splitlines() if "DDNS dashboard:" in line
        )
        launch_path = urlparse(launch_url).path

        status, _, index = self._http_request(port, "/")
        asset_status, _, script = self._http_request(port, "/assets/dashboard.js")
        unauthorized_status, _, unauthorized_body = self._http_request(port, "/api/dashboard")
        launch_status, launch_headers, _ = self._http_request(port, launch_path)
        reused_status, _, reused_body = self._http_request(port, launch_path)

        self.assertEqual(status, 200)
        self.assertIn("<html", index)
        self.assertEqual(asset_status, 200)
        self.assertIn("/api/dashboard", script)
        self.assertEqual(unauthorized_status, 403)
        self.assertEqual(json.loads(unauthorized_body)["error"]["code"], "invalid_token")
        self.assertEqual(launch_status, 302)
        self.assertEqual(reused_status, 403)
        self.assertEqual(json.loads(reused_body)["error"]["code"], "invalid_launch_token")

        location = launch_headers["Location"]
        access_token = parse_qs(urlparse(location).fragment)["token"][0]
        api_headers = {"X-DDNS-Token": access_token}
        config_headers = {"X-DDNS-Token": access_token, "Content-Type": "application/json"}
        callback_token = json.dumps(
            {
                "domain": "__DOMAIN__",
                "ip": "__IP__",
                "record_type": "__RECORDTYPE__",
                "ttl": "__TTL__",
                "line": "__LINE__",
            },
            separators=(",", ":"),
        )
        config = {
            "$schema": "https://ddns.newfuture.cc/schema/v4.1.json",
            "ssl": False,
            "proxy": ["DIRECT"],
            "cache": True,
            "cache_max_age": 3600,
            "interval": 30,
            "log": {"level": "INFO"},
            "providers": [
                {
                    "provider": "callback",
                    "id": self.fixture_url + "/callback/web",
                    "token": callback_token,
                    "ipv4": ["web.example.com"],
                    "index4": ["url:" + self.fixture_url + "/ip/v4"],
                    "ipv6": [],
                    "index6": False,
                    "ttl": 180,
                    "line": "web",
                }
            ],
        }

        validate_status, _, validate_body = self._http_request(
            port, "/api/config/validate", method="POST", payload={"config": config}, headers=config_headers
        )
        save_status, _, save_body = self._http_request(
            port, "/api/config", method="PUT", payload={"config": config}, headers=config_headers
        )
        sync_status, _, sync_body = self._http_request(
            port, "/api/sync", method="POST", payload={}, headers=config_headers
        )
        dashboard_status, _, dashboard_body = self._http_request(port, "/api/dashboard", headers=api_headers)

        self.assertEqual(validate_status, 200, validate_body)
        self.assertEqual(
            json.loads(validate_body)["config"]["providers"][0]["index4"], ["url:" + self.fixture_url + "/ip/v4"]
        )
        self.assertEqual(save_status, 200, save_body)
        self.assertTrue(os.path.isfile(config_path))
        self.assertEqual(sync_status, 200, sync_body)
        dashboard = json.loads(dashboard_body)
        self.assertEqual(dashboard_status, 200)
        self.assertEqual(dashboard["state"], "synced")
        self.assertEqual(dashboard["providers"][0]["status"], "synced")
        self.assertEqual(dashboard["records"][0]["domain"], "web.example.com")
        self.assertEqual(dashboard["records"][0]["value"], TEST_IPV4)

        callback_requests = self.fixture_state.requests_for("/callback/web")
        self.assertEqual(len(callback_requests), 1)
        self.assertEqual(
            json.loads(callback_requests[0]["body"]),
            {"domain": "web.example.com", "ip": TEST_IPV4, "record_type": "A", "ttl": "180", "line": "web"},
        )

        config["cache"] = False
        cache_disable_status, _, cache_disable_body = self._http_request(
            port, "/api/config", method="PUT", payload={"config": config}, headers=config_headers
        )
        self.assertEqual(cache_disable_status, 200, cache_disable_body)

        configure_status, _, configure_body = self._http_request(
            port,
            "/api/scheduler",
            method="POST",
            payload={"action": "configure", "scheduler": "web", "interval": 1},
            headers=config_headers,
        )
        disable_status, _, disable_body = self._http_request(
            port,
            "/api/scheduler",
            method="POST",
            payload={"action": "disable", "scheduler": "web", "interval": 1},
            headers=config_headers,
        )
        enable_status, _, enable_body = self._http_request(
            port,
            "/api/scheduler",
            method="POST",
            payload={"action": "enable", "scheduler": "web", "interval": 1},
            headers=config_headers,
        )

        self.assertEqual(configure_status, 200, configure_body)
        self.assertEqual(json.loads(configure_body)["scheduler"]["interval"], 1)
        self.assertEqual(disable_status, 200, disable_body)
        self.assertFalse(json.loads(disable_body)["scheduler"]["enabled"])
        self.assertEqual(enable_status, 200, enable_body)
        self.assertTrue(json.loads(enable_body)["scheduler"]["enabled"])

        deadline = time.time() + 75
        scheduled_dashboard = None
        while time.time() < deadline:
            time.sleep(1)
            dashboard_status, _, dashboard_body = self._http_request(port, "/api/dashboard", headers=api_headers)
            dashboard = json.loads(dashboard_body)
            if (
                dashboard_status == 200
                and dashboard["scheduler"]["last_run"] is not None
                and len(self.fixture_state.requests_for("/callback/web")) >= 2
            ):
                scheduled_dashboard = dashboard
                break
        self.assertIsNotNone(
            scheduled_dashboard,
            "Web scheduler did not synchronize.\nstdout:\n{}\nstderr:\n{}".format(process.stdout, process.stderr),
        )
        self.assertEqual(len(self.fixture_state.requests_for("/callback/web")), 2)
        self.assertEqual(scheduled_dashboard["state"], "synced")
        self.assertIsNone(scheduled_dashboard["scheduler"]["last_error"])

        returncode = process.stop()
        if os.name == "nt":
            self.assertIsNotNone(returncode)
        else:
            self.assertEqual(returncode, 0, "Dashboard did not stop cleanly.\nstderr:\n{}".format(process.stderr))


if __name__ == "__main__":
    unittest.main()
