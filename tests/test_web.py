# coding=utf-8
"""Tests for the embedded DDNS dashboard service and HTTP server."""

from __future__ import unicode_literals

import copy
import io
import json
import logging
import os
import shutil
import sys
import tempfile
import threading
import time

from __init__ import MagicMock, patch, unittest

try:
    from urllib.error import HTTPError
    from urllib.request import Request, urlopen
except ImportError:  # Python 2
    from urllib2 import HTTPError, Request, urlopen

from ddns.provider import get_provider_class
from ddns.web.server import DashboardRequestHandler, _resource_bytes, _write_stdout, create_server, serve
from ddns.web.scheduler import WebScheduler
from ddns.web.service import (
    CONFIG_MODEL,
    ConfigValidationError,
    DashboardOperationError,
    DashboardService,
    _replace_file,
    resolve_config_path,
    validate_document,
)


def _valid_config(line="default"):
    """Return a small valid dashboard configuration."""
    return {
        "$schema": "https://ddns.newfuture.cc/schema/v4.1.json",
        "ssl": "auto",
        "proxy": "DIRECT",
        "cache": True,
        "cache_max_age": 259200,
        "log": {"level": "INFO"},
        "providers": [
            {
                "provider": "debug",
                "id": "",
                "token": "",
                "ipv4": ["home.example.com"],
                "ipv6": [],
                "index4": "public",
                "index6": False,
                "ttl": 300,
                "line": line,
            }
        ],
    }


class TestDashboardAssets(unittest.TestCase):
    """Test the standalone source and packaged asset loading paths."""

    def test_frontend_sources_live_in_top_level_web_directory(self):
        """Keep one canonical frontend source outside the Python package."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        for asset_name in ("index.html", "dashboard.css", "dashboard.js", "ddns.svg"):
            self.assertTrue(os.path.isfile(os.path.join(project_root, "web", asset_name)))
            self.assertFalse(os.path.isfile(os.path.join(project_root, "ddns", "web", "static", asset_name)))

    @patch("ddns.web.server.pkgutil.get_data")
    def test_resource_loader_prefers_standalone_source(self, mock_get_data):
        """Read live frontend sources directly during repository development."""
        self.assertIn(b"<html", _resource_bytes("index.html"))
        mock_get_data.assert_not_called()

    @patch("ddns.web.server.SOURCE_ASSET_ROOT", "source")
    @patch("ddns.web.server.PACKAGED_ASSET_ROOT", "packaged")
    @patch("ddns.web.server._resource_file_bytes")
    def test_resource_loader_prefers_packaged_assets(self, mock_file_bytes):
        """Do not let an unrelated sibling Web directory shadow installed assets."""
        mock_file_bytes.side_effect = lambda root, _name: root.encode("ascii")

        self.assertEqual(_resource_bytes("index.html"), b"packaged")
        mock_file_bytes.assert_called_once_with("packaged", "index.html")

    @patch("ddns.web.server.pkgutil.get_data", return_value=b"packaged asset")
    @patch("ddns.web.server._resource_file_bytes", return_value=None)
    def test_resource_loader_falls_back_to_package_data(self, mock_file_bytes, mock_get_data):
        """Read materialized package data after installation or freezing."""
        self.assertEqual(_resource_bytes("index.html"), b"packaged asset")
        self.assertEqual(mock_file_bytes.call_count, 2)
        mock_get_data.assert_called_once_with("ddns.web", "static/index.html")


class TestDashboardService(unittest.TestCase):
    """Test configuration persistence and runtime projections."""

    def setUp(self):
        """Create an isolated local configuration path."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)
        self.config_path = os.path.join(self.temp_dir, "config.json")
        self.scheduler_patcher = patch("ddns.web.service.get_schedulers")
        self.mock_get_schedulers = self.scheduler_patcher.start()
        self.addCleanup(self.scheduler_patcher.stop)
        self.mock_scheduler = MagicMock()
        self.mock_get_schedulers.return_value = [self.mock_scheduler]
        self.mock_scheduler.get_status.return_value = {"scheduler": "test", "installed": False, "enabled": False}
        self.env_patcher = patch("ddns.web.service.load_env_config", return_value={})
        self.mock_load_env_config = self.env_patcher.start()
        self.addCleanup(self.env_patcher.stop)
        self.service = DashboardService(config_path=self.config_path)

    def test_validate_accepts_supported_compact_values(self):
        """Canonicalize scalar address sources and proxy strings."""
        config = _valid_config()
        config["providers"][0]["ipv4"] = "home.example.com, nas.example.com"
        validated = validate_document(config)

        self.assertEqual(validated["proxy"], ["DIRECT"])
        self.assertEqual(validated["providers"][0]["ipv4"], ["home.example.com", "nas.example.com"])
        self.assertEqual(validated["providers"][0]["index4"], ["public"])
        self.assertFalse(validated["providers"][0]["index6"])

    def test_shared_field_model_matches_public_schema(self):
        """Keep both configuration UIs aligned with schema v4.1."""
        schema_path = os.path.join(os.path.dirname(__file__), "..", "schema", "v4.1.json")
        with io.open(schema_path, "r", encoding="utf-8") as schema_file:
            schema = json.load(schema_file)

        provider_properties = schema["properties"]["providers"]["items"]["properties"]
        provider_ids = [provider["id"] for provider in CONFIG_MODEL["providers"]]
        self.assertEqual(CONFIG_MODEL["schema"]["url"], schema["$id"])
        self.assertEqual(CONFIG_MODEL["schema"]["values"], schema["properties"]["$schema"]["enum"])
        self.assertEqual(provider_ids, provider_properties["provider"]["enum"])
        self.assertEqual(CONFIG_MODEL["rules"]["domainPattern"], schema["properties"]["ipv4"]["items"]["pattern"])
        self.assertEqual(CONFIG_MODEL["rules"]["proxyPattern"], schema["properties"]["proxy"]["items"]["pattern"])
        self.assertEqual(CONFIG_MODEL["rules"]["logLevels"], schema["properties"]["log"]["properties"]["level"]["enum"])
        self.assertTrue(all(get_provider_class(provider_id) is not None for provider_id in provider_ids))

    def test_validate_canonicalizes_runtime_boolean_strings(self):
        """Preserve existing false-source and string-boolean semantics."""
        config = _valid_config()
        config["ssl"] = "false"
        config["cache"] = "no"
        config["providers"][0]["index4"] = "false"
        config["providers"][0]["index6"] = "none"

        validated = validate_document(config)

        self.assertFalse(validated["ssl"])
        self.assertFalse(validated["cache"])
        self.assertFalse(validated["providers"][0]["index4"])
        self.assertFalse(validated["providers"][0]["index6"])

    def test_validate_preserves_zero_interface_index(self):
        """Keep interface index zero as a valid scalar address source."""
        config = _valid_config()
        config["providers"][0]["index4"] = 0

        validated = validate_document(config)

        self.assertEqual(validated["providers"][0]["index4"], [0])

    def test_validate_rejects_malformed_provider_container(self):
        """Do not silently replace an explicit malformed providers value."""
        with self.assertRaises(ConfigValidationError) as context:
            validate_document({"providers": {}})

        self.assertIn("providers must be an array", str(context.exception))

    def test_validate_preserves_ssl_paths_and_null_lines(self):
        """Keep custom CA paths and default DNS-line semantics intact."""
        config = _valid_config(line=None)
        config["ssl"] = "/etc/ssl/private/ddns-ca.pem"

        validated = validate_document(config)

        self.assertEqual(validated["ssl"], "/etc/ssl/private/ddns-ca.pem")
        self.assertIsNone(validated["providers"][0]["line"])

    def test_legacy_provider_extensions_are_migrated(self):
        """Move legacy unknown provider fields into the v4.1 extra object."""
        validated = validate_document(
            {
                "dns": "debug",
                "proxied": True,
                "extra_comment": "managed",
                "custom": {"setting": "value"},
                "ssl": {"verify": True},
            }
        )

        self.assertEqual(validated["providers"][0]["extra"]["proxied"], True)
        self.assertEqual(validated["providers"][0]["extra"]["comment"], "managed")
        self.assertEqual(validated["providers"][0]["extra"]["custom_setting"], "value")
        self.assertTrue(validated["providers"][0]["extra"]["ssl_verify"])

    def test_legacy_single_provider_promotes_global_fields_once(self):
        """Keep promoted legacy settings out of hidden provider overrides."""
        validated = validate_document(
            {
                "dns": "debug",
                "ipv4": ["legacy.example.com"],
                "ssl": False,
                "proxy": "DIRECT",
                "cache": False,
                "cache_max_age": 42,
                "log_level": "ERROR",
            }
        )

        provider = validated["providers"][0]
        for key in ("ssl", "proxy", "cache", "cache_max_age", "log"):
            self.assertNotIn(key, provider)
        self.assertFalse(validated["ssl"])
        self.assertEqual(validated["proxy"], ["DIRECT"])
        self.assertFalse(validated["cache"])
        self.assertEqual(validated["cache_max_age"], 42)
        self.assertEqual(validated["log"], {"level": "ERROR"})

    def test_interval_is_validated_and_kept_global(self):
        """Preserve a bounded root interval without leaking it to providers."""
        config = _valid_config()
        config["interval"] = 7

        validated = validate_document(config)

        self.assertEqual(validated["interval"], 7)
        self.assertNotIn("interval", validated["providers"][0])
        for invalid in (True, 0, 1441, 1.5, "5"):
            config["interval"] = invalid
            with self.assertRaises(ConfigValidationError):
                validate_document(config)

    def test_provider_interval_is_rejected(self):
        """Require scheduling metadata at the document root."""
        config = _valid_config()
        config["providers"][0]["interval"] = 7

        with self.assertRaises(ConfigValidationError):
            validate_document(config)

    def test_runtime_config_uses_existing_v41_inheritance(self):
        """Apply global fields and provider overrides like the normal file loader."""
        config = _valid_config()
        config["ttl"] = 120
        config["index4"] = ["public"]
        config["extra"] = {"proxied": True}
        del config["providers"][0]["ttl"]
        del config["providers"][0]["index4"]
        config["providers"][0]["ssl"] = "/etc/ssl/provider-ca.pem"

        runtime = self.service._runtime_configs(validate_document(config))[0]

        self.assertEqual(runtime.ttl, 120)
        self.assertEqual(runtime.index4, ["public"])
        self.assertEqual(runtime.ssl, "/etc/ssl/provider-ca.pem")
        self.assertTrue(runtime.extra["proxied"])

    def test_runtime_config_inherits_environment_values(self):
        """Use the same environment fallback as the normal configuration loader."""
        config = _valid_config()
        provider = config["providers"][0]
        for key in ("id", "token", "ipv4"):
            del provider[key]
        self.mock_load_env_config.return_value = {
            "id": "environment-id",
            "token": "environment-token",
            "ipv4": "environment.example.com",
        }

        runtime = self.service._runtime_configs(validate_document(config))[0]

        self.assertEqual(runtime.id, "environment-id")
        self.assertEqual(runtime.token, "environment-token")
        self.assertEqual(runtime.ipv4, ["environment.example.com"])

    def test_omitted_global_fields_continue_to_inherit_environment(self):
        """Do not materialize defaults that would override environment values."""
        config = {"providers": [{"provider": "debug", "ipv4": ["home.example.com"]}]}
        self.mock_load_env_config.return_value = {
            "ssl": "false",
            "proxy": "DIRECT",
            "cache": "false",
            "cache_max_age": "42",
            "log_level": "ERROR",
        }

        validated = self.service.validate(config)
        runtime = self.service._runtime_configs(validated)[0]

        for key in ("ssl", "proxy", "cache", "cache_max_age", "log"):
            self.assertNotIn(key, validated)
        self.assertFalse(runtime.ssl)
        self.assertEqual(runtime.proxy, ["DIRECT"])
        self.assertFalse(runtime.cache)
        self.assertEqual(runtime.cache_max_age, 42)
        self.assertEqual(runtime.log_level, 40)

    def test_legacy_config_uses_environment_provider_without_losing_fields(self):
        """Normalize a legacy file whose provider is selected by DDNS_DNS."""
        self.mock_load_env_config.return_value = {"dns": "debug"}
        legacy = {"token": "environment-selected-token", "ipv4": ["legacy.example.com"], "index4": "public"}

        validated = self.service.validate(legacy)

        self.assertEqual(validated["providers"][0]["provider"], "debug")
        self.assertEqual(validated["providers"][0]["token"], "environment-selected-token")
        self.assertEqual(validated["providers"][0]["ipv4"], ["legacy.example.com"])

    def test_legacy_config_without_provider_is_recoverable(self):
        """Report a legacy file that needs DDNS_DNS instead of discarding it."""
        with io.open(self.config_path, "w", encoding="utf-8") as config_file:
            config_file.write(json.dumps({"token": "keep-me", "ipv4": ["legacy.example.com"]}, ensure_ascii=False))

        state = self.service.config_state()

        self.assertIn("DDNS_DNS", state["validation_error"])
        self.assertIn("keep-me", state["raw"])
        self.assertEqual(state["config"]["providers"], [])

    def test_legacy_list_preserves_independent_environment_fallbacks(self):
        """Do not turn the first legacy entry's settings into global overrides."""
        self.mock_load_env_config.return_value = {"dns": "debug", "proxy": "SYSTEM"}
        legacy = [{"ipv4": ["first.example.com"], "proxy": "DIRECT"}, {"ipv4": ["second.example.com"]}]

        validated = self.service.validate(legacy)
        runtime = self.service._runtime_configs(validated)

        self.assertNotIn("proxy", validated)
        self.assertEqual(validated["providers"][0]["proxy"], ["DIRECT"])
        self.assertNotIn("proxy", validated["providers"][1])
        self.assertEqual(runtime[0].proxy, ["DIRECT"])
        self.assertEqual(runtime[1].proxy, ["SYSTEM"])

    def test_legacy_list_rejects_non_object_entries(self):
        """Reject malformed legacy entries rather than silently dropping them."""
        with self.assertRaises(ConfigValidationError) as context:
            validate_document([{"dns": "debug"}, "invalid"])

        self.assertIn("Provider 2", str(context.exception))

    def test_invalid_global_provider_field_is_rejected(self):
        """Reject invalid inherited values before they can break dashboard reads."""
        config = _valid_config()
        config["ttl"] = "not-a-number"

        with self.assertRaises(ConfigValidationError) as context:
            validate_document(config)
        self.assertIn("Global TTL", str(context.exception))

    def test_shared_validation_rules_reject_invalid_values(self):
        """Apply the same domain, proxy, and source rules as Config Studio."""
        invalid_values = [
            ("ipv4", ["not a domain"]),
            ("index4", ["unsupported"]),
            ("proxy", ["socks5://127.0.0.1:1080"]),
        ]
        for key, value in invalid_values:
            config = _valid_config()
            target = config if key == "proxy" else config["providers"][0]
            target[key] = value
            with self.assertRaises(ConfigValidationError):
                validate_document(config)

    def test_providers_reject_global_legacy_fields(self):
        """Prevent top-level provider credentials from leaking across providers."""
        values = {
            "dns": "debug",
            "provider": "debug",
            "id": "global-id",
            "token": "global-token",
            "ipv4": ["global.example.com"],
            "ipv6": ["global.example.com"],
            "endpoint": "https://api.example.com",
        }
        for key, value in values.items():
            config = _valid_config()
            config[key] = value
            with self.assertRaises(ConfigValidationError) as context:
                validate_document(config)
            self.assertIn(key, str(context.exception))

    def test_provider_rejects_hidden_dns_override(self):
        """Prevent a provider entry from overriding its validated provider at runtime."""
        config = _valid_config()
        config["providers"][0]["dns"] = "cloudflare"

        with self.assertRaises(ConfigValidationError) as context:
            validate_document(config)

        self.assertIn("cannot contain dns", str(context.exception))

    def test_reserved_extra_fields_are_rejected(self):
        """Reject custom fields that collide with runtime record arguments."""
        for key in CONFIG_MODEL["rules"]["reservedExtraKeys"]:
            config = _valid_config()
            config["providers"][0]["extra"] = {key: "conflict"}
            with self.assertRaises(ConfigValidationError) as context:
                validate_document(config)
            self.assertIn(key, str(context.exception))

    def test_numeric_validation_does_not_truncate_values(self):
        """Reject fractional cache ages while preserving valid numeric TTL values."""
        config = _valid_config()
        config["cache_max_age"] = 12.5
        with self.assertRaises(ConfigValidationError):
            validate_document(config)

        config = _valid_config()
        config["providers"][0]["ttl"] = 12.5
        validated = validate_document(config)
        self.assertEqual(validated["providers"][0]["ttl"], 12.5)

    def test_save_and_restore_unicode_configuration(self):
        """Write UTF-8 config atomically and swap to its backup."""
        first = self.service.save(_valid_config(line="默认"))
        second = self.service.save(_valid_config(line="telecom"))

        self.assertEqual(first["config"]["providers"][0]["line"], "默认")
        self.assertTrue(second["backup_available"])
        with io.open(self.config_path, "r", encoding="utf-8") as config_file:
            self.assertIn("telecom", config_file.read())

        restored = self.service.restore_backup()

        self.assertEqual(restored["config"]["providers"][0]["line"], "默认")
        with io.open(self.config_path, "r", encoding="utf-8") as config_file:
            self.assertIn("默认", config_file.read())

    def test_failed_save_preserves_current_file_and_previous_backup(self):
        """Roll back both generations when installing the new file fails."""
        self.service.save(_valid_config(line="first"))
        self.service.save(_valid_config(line="second"))
        real_replace = _replace_file

        def fail_new_file(source, destination):
            """Fail only while installing the newly written temporary file."""
            if os.path.basename(source).startswith(".ddns-config-") and destination == self.config_path:
                raise OSError("simulated install failure")
            return real_replace(source, destination)

        with patch("ddns.web.service._replace_file", side_effect=fail_new_file):
            with self.assertRaises(DashboardOperationError):
                self.service.save(_valid_config(line="third"))

        with io.open(self.config_path, "r", encoding="utf-8") as config_file:
            current = json.load(config_file)
        with io.open(self.config_path + ".bak", "r", encoding="utf-8") as backup_file:
            backup = json.load(backup_file)
        self.assertEqual(current["providers"][0]["line"], "second")
        self.assertEqual(backup["providers"][0]["line"], "first")
        self.assertFalse(any(name.startswith(".ddns-backup-") for name in os.listdir(self.temp_dir)))

    def test_save_replaces_active_configuration_without_missing_path(self):
        """Keep the active path readable until the atomic replacement."""
        self.service.save(_valid_config(line="first"))
        observations = []

        def observe_replace(source, destination):
            """Record active-path availability immediately before replacement."""
            if os.path.basename(source).startswith(".ddns-config-") and destination == self.config_path:
                observations.append(os.path.exists(self.config_path))
            return _replace_file(source, destination)

        with patch("ddns.web.service._replace_file", side_effect=observe_replace):
            self.service.save(_valid_config(line="second"))

        self.assertEqual(observations, [True])

    def test_restore_replaces_active_configuration_without_missing_path(self):
        """Keep the active path readable until a backup is restored."""
        self.service.save(_valid_config(line="first"))
        self.service.save(_valid_config(line="second"))
        observations = []

        def observe_replace(source, destination):
            """Record active-path availability immediately before replacement."""
            if os.path.basename(source).startswith(".ddns-restore-") and destination == self.config_path:
                observations.append(os.path.exists(self.config_path))
            return _replace_file(source, destination)

        with patch("ddns.web.service._replace_file", side_effect=observe_replace):
            restored = self.service.restore_backup()

        self.assertEqual(observations, [True])
        self.assertEqual(restored["config"]["providers"][0]["line"], "first")

    def test_restore_valid_backup_over_invalid_active_configuration(self):
        """Allow recovery even when the current file cannot be validated."""
        self.service.save(_valid_config(line="first"))
        self.service.save(_valid_config(line="second"))
        with io.open(self.config_path, "w", encoding="utf-8") as config_file:
            config_file.write("{ invalid")

        restored = self.service.restore_backup()

        self.assertEqual(restored["config"]["providers"][0]["line"], "first")

    def test_save_preserves_configuration_symlink(self):
        """Write through a configuration symlink without replacing the link."""
        if not hasattr(os, "symlink"):
            self.skipTest("Symbolic links are unavailable")
        target_path = os.path.join(self.temp_dir, "target.json")
        link_path = os.path.join(self.temp_dir, "linked.json")
        with io.open(target_path, "w", encoding="utf-8") as config_file:
            config_file.write(json.dumps(_valid_config(line="first"), ensure_ascii=False))
        try:
            os.symlink(target_path, link_path)
        except (IOError, OSError) as error:
            self.skipTest("Cannot create symbolic link: {}".format(error))
        service = DashboardService(config_path=link_path)

        state = service.save(_valid_config(line="second"))

        self.assertTrue(os.path.islink(link_path))
        with io.open(target_path, "r", encoding="utf-8") as config_file:
            self.assertEqual(json.load(config_file)["providers"][0]["line"], "second")
        with io.open(target_path + ".bak", "r", encoding="utf-8") as backup_file:
            self.assertEqual(json.load(backup_file)["providers"][0]["line"], "first")
        self.assertTrue(state["backup_available"])

    def test_non_ascii_byte_config_path_is_normalized(self):
        """Decode command-line paths once before Unicode path operations."""
        unicode_path = os.path.join(self.temp_dir, "配置.json")
        encoded_path = unicode_path.encode(sys.getfilesystemencoding() or "utf-8")

        resolved = resolve_config_path(encoded_path)
        service = DashboardService(config_path=encoded_path)
        service.save(_valid_config())

        self.assertEqual(resolved, unicode_path)
        self.assertEqual(service.config_path, unicode_path)
        self.assertTrue(os.path.exists(unicode_path))

    def test_dashboard_reports_configured_records_without_secrets(self):
        """Project saved providers into dashboard status without exposing secrets."""
        config = _valid_config()
        config["providers"][0]["token"] = "dashboard-secret"
        self.service.save(config)

        dashboard = self.service.dashboard()

        self.assertEqual(dashboard["state"], "ready")
        self.assertEqual(dashboard["providers"][0]["records"], 1)
        self.assertNotIn("provider_catalog", dashboard)
        self.assertNotIn("config_model", dashboard)
        self.assertNotIn("dashboard-secret", json.dumps(dashboard))

    def test_dashboard_filters_records_from_shared_cache_by_provider_domains(self):
        """Do not duplicate or mislabel records from a shared cache file."""
        cache_path = os.path.join(self.temp_dir, "shared.cache")
        config = _valid_config()
        config["cache"] = cache_path
        config["providers"][0]["ipv4"] = ["first.example.com"]
        second_provider = _valid_config()["providers"][0]
        second_provider["provider"] = "callback"
        second_provider["ipv4"] = ["second.example.com"]
        config["providers"].append(second_provider)
        self.service.save(config)
        with io.open(cache_path, "w", encoding="utf-8") as cache_file:
            cache_file.write(
                json.dumps(
                    {
                        "first.example.com:A": "203.0.113.10",
                        "second.example.com:A": "203.0.113.20",
                        "unrelated.example.com:A": "203.0.113.30",
                    },
                    ensure_ascii=False,
                )
            )

        dashboard = self.service.dashboard()

        records = {(record["domain"], record["provider"]) for record in dashboard["records"]}
        self.assertEqual(records, {("first.example.com", "debug"), ("second.example.com", "callback")})

    def test_dashboard_allows_small_cache_mtime_clock_skew(self):
        """Do not hide a freshly written cache when file mtime is slightly ahead."""
        cache_path = os.path.join(self.temp_dir, "shared.cache")
        config = _valid_config()
        config["cache"] = cache_path
        self.service.save(config)
        with io.open(cache_path, "w", encoding="utf-8") as cache_file:
            cache_file.write(json.dumps({"home.example.com:A": "203.0.113.10"}))

        cache_time = os.path.getmtime(cache_path)
        with patch("ddns.web.service.time.time", return_value=cache_time - 0.5):
            dashboard = self.service.dashboard()

        self.assertEqual(
            [(record["domain"], record["provider"]) for record in dashboard["records"]], [("home.example.com", "debug")]
        )

    def test_missing_file_projects_environment_only_configuration(self):
        """Expose an environment-only provider without persisting default fields."""
        self.mock_load_env_config.return_value = {
            "dns": "debug",
            "token": "environment-only-token",
            "ipv4": "environment.example.com",
        }

        document = self.service.load_document()
        runtime = self.service._runtime_configs(document)[0]

        self.assertEqual(document["providers"], [{"provider": "debug"}])
        self.assertEqual(runtime.token, "environment-only-token")
        self.assertEqual(runtime.ipv4, ["environment.example.com"])

    def test_invalid_config_remains_recoverable(self):
        """Return invalid source text for repair instead of breaking config API."""
        with io.open(self.config_path, "w", encoding="utf-8") as config_file:
            config_file.write('{"providers": [{"provider": "missing"}]}')

        state = self.service.config_state()

        self.assertIn("validation_error", state)
        self.assertIn('"missing"', state["raw"])
        self.assertEqual(state["config"]["providers"], [])

    def test_unicode_validation_error_remains_api_safe(self):
        """Keep Unicode validation details intact on Python 2 and Python 3."""
        with io.open(self.config_path, "w", encoding="utf-8") as config_file:
            config_file.write("{}")

        with patch.object(self.service, "_validate_document", side_effect=ConfigValidationError("配置无效")):
            state = self.service.config_state()

        self.assertEqual(state["validation_error"], "配置无效")

    def test_unicode_provider_error_remains_recoverable(self):
        """Treat a non-ASCII unknown provider as a normal validation error."""
        with io.open(self.config_path, "w", encoding="utf-8") as config_file:
            config_file.write(json.dumps({"providers": [{"provider": "未知"}]}, ensure_ascii=False))

        state = self.service.config_state()

        self.assertIn("未知", state["validation_error"])
        self.assertIn("未知", state["raw"])

    @patch("ddns.__main__.run", return_value=True)
    def test_sync_uses_runtime_config(self, mock_run):
        """Run the current normalized configuration through the DDNS engine."""
        self.service.save(_valid_config())

        dashboard = self.service.sync()

        mock_run.assert_called_once()
        runtime_config = mock_run.call_args[0][0]
        self.assertEqual(runtime_config.dns, "debug")
        self.assertEqual(runtime_config.index4, ["public"])
        self.assertEqual(dashboard["activities"][0]["message"], "所有配置同步完成")

    @patch("ddns.__main__.run")
    def test_sync_applies_and_restores_runtime_logging(self, mock_run):
        """Honor persisted log output settings without replacing Web handlers."""
        log_path = os.path.join(self.temp_dir, "runtime.log")
        config = _valid_config()
        config["cache"] = False
        config["log"] = {"level": "WARNING", "file": log_path, "format": "SYNC:%(message)s", "datefmt": "%H:%M"}
        self.service.save(config)
        root_logger = logging.getLogger()
        previous_level = root_logger.level
        previous_handlers = list(root_logger.handlers)
        previous_formatters = [handler.formatter for handler in previous_handlers]

        def emit_runtime_log(_config):
            """Emit one message through the root logger used by providers."""
            logging.getLogger("runtime-test").warning("runtime-message")
            return True

        mock_run.side_effect = emit_runtime_log
        self.service.sync()

        with io.open(log_path, "r", encoding="utf-8") as log_file:
            self.assertIn("SYNC:runtime-message", log_file.read())
        self.assertEqual(root_logger.level, previous_level)
        self.assertEqual(root_logger.handlers, previous_handlers)
        self.assertEqual([handler.formatter for handler in previous_handlers], previous_formatters)

    @patch("ddns.__main__.run", return_value=True)
    def test_sync_rejects_configuration_without_domains(self, mock_run):
        """Keep domain-less providers in first-run and reject a no-op sync."""
        config = _valid_config()
        config["providers"][0]["ipv4"] = []
        config["providers"][0]["ipv6"] = []
        self.service.save(config)

        self.assertEqual(self.service.dashboard()["state"], "unconfigured")
        with self.assertRaises(ConfigValidationError):
            self.service.sync()
        mock_run.assert_not_called()

    @patch("ddns.__main__.run", return_value=True)
    def test_sync_reports_success_when_cache_is_disabled(self, mock_run):
        """Project successful runtime state without inventing cache records."""
        config = _valid_config()
        config["cache"] = False
        self.service.save(config)

        dashboard = self.service.sync()

        mock_run.assert_called_once()
        self.assertEqual(dashboard["state"], "synced")
        self.assertEqual(dashboard["message"], "最近一次同步已完成")
        self.assertEqual(dashboard["providers"][0]["status"], "synced")
        self.assertIsNotNone(dashboard["last_sync"])
        self.assertEqual(dashboard["records"], [])

    @patch("ddns.__main__.run", side_effect=[True, False])
    def test_failed_sync_overrides_previous_success_state(self, mock_run):
        """Report the latest failed attempt instead of stale healthy state."""
        config = _valid_config()
        config["cache"] = False
        self.service.save(config)
        successful = self.service.sync()

        with self.assertRaises(DashboardOperationError):
            self.service.sync()
        dashboard = self.service.dashboard()

        self.assertEqual(mock_run.call_count, 2)
        self.assertEqual(successful["state"], "synced")
        self.assertEqual(dashboard["state"], "error")
        self.assertEqual(dashboard["message"], "最近一次同步失败")
        self.assertEqual(dashboard["providers"][0]["status"], "error")
        self.assertEqual(dashboard["last_sync"], successful["last_sync"])

    @patch("ddns.__main__.run", side_effect=[False, True])
    def test_duplicate_provider_types_keep_independent_sync_status(self, mock_run):
        """Project failures by provider entry instead of provider type."""
        config = _valid_config()
        config["cache"] = False
        second = copy.deepcopy(config["providers"][0])
        second["ipv4"] = ["second.example.com"]
        config["providers"].append(second)
        self.service.save(config)

        with self.assertRaises(DashboardOperationError):
            self.service.sync()
        dashboard = self.service.dashboard()

        self.assertEqual(mock_run.call_count, 2)
        self.assertEqual([provider["status"] for provider in dashboard["providers"]], ["error", "synced"])

    @patch("ddns.__main__.run")
    def test_sync_stops_before_next_provider_when_cancelled(self, mock_run):
        """Stop cooperative synchronization between configured providers."""
        config = _valid_config()
        second = copy.deepcopy(config["providers"][0])
        second["ipv4"] = ["second.example.com"]
        config["providers"].append(second)
        self.service.save(config)
        cancel_event = threading.Event()

        def cancel_after_first(_config, cancelled=None):
            """Cancel after the first provider returns."""
            self.assertTrue(callable(cancelled))
            cancel_event.set()
            return True

        mock_run.side_effect = cancel_after_first

        with self.assertRaises(DashboardOperationError) as context:
            self.service.sync(source="MCP", cancelled=cancel_event.is_set)

        self.assertIn("cancelled", str(context.exception).lower())
        mock_run.assert_called_once()

    def test_scheduler_action_uses_selected_interval(self):
        """Update the interval for the current web process."""
        result = self.service.configure_scheduler("configure", interval=12)

        self.assertEqual(result["interval"], 12)
        self.assertEqual(os.listdir(self.temp_dir), [])

    def test_saving_config_interval_updates_current_scheduler(self):
        """Apply a newly persisted interval to the running Web process."""
        config = _valid_config()
        config["interval"] = 14

        saved = self.service.save(config)

        self.assertEqual(saved["config"]["interval"], 14)
        self.assertEqual(self.service.dashboard()["scheduler"]["interval"], 14)

    def test_scheduler_rejects_fractional_interval(self):
        """Reject intervals that would otherwise be silently truncated."""
        with self.assertRaises(ConfigValidationError):
            self.service.configure_scheduler("configure", interval=1.5)

    def test_scheduler_state_resets_on_service_restart(self):
        """Use CLI startup defaults instead of a runtime sidecar."""
        self.service.configure_scheduler("disable", interval=17)

        restarted = DashboardService(config_path=self.config_path, scheduler_interval=9)
        status = restarted.dashboard()["scheduler"]

        self.assertTrue(status["enabled"])
        self.assertEqual(status["interval"], 9)

    def test_scheduler_reports_external_task_conflict(self):
        """Prevent web and system schedulers from updating the same records."""
        self.mock_scheduler.get_status.return_value = {"scheduler": "test", "installed": True, "enabled": True}

        status = self.service.dashboard()["scheduler"]

        self.assertTrue(status["conflict"])
        self.assertFalse(status["enabled"])
        self.assertEqual(status["external_scheduler"], "test")

    def test_scheduler_takeover_disables_external_task(self):
        """Disable the old system task before enabling web scheduling."""
        self.mock_scheduler.get_status.side_effect = [
            {"scheduler": "test", "installed": True, "enabled": True},
            {"scheduler": "test", "installed": True, "enabled": False},
            {"scheduler": "test", "installed": True, "enabled": False},
        ]
        self.mock_scheduler.disable.return_value = True

        status = self.service.configure_scheduler("takeover", interval=8)

        self.mock_scheduler.disable.assert_called_once_with()
        self.assertTrue(status["enabled"])
        self.assertEqual(status["interval"], 8)

    def test_scheduler_detects_and_disables_all_enabled_backends(self):
        """Guard against explicitly selected backends that differ from auto detection."""
        systemd = MagicMock()
        cron = MagicMock()
        systemd.get_status.side_effect = [
            {"scheduler": "systemd", "installed": True, "enabled": True},
            {"scheduler": "systemd", "installed": True, "enabled": True},
            {"scheduler": "systemd", "installed": True, "enabled": False},
            {"scheduler": "systemd", "installed": True, "enabled": False},
        ]
        cron.get_status.side_effect = [
            {"scheduler": "cron", "installed": True, "enabled": True},
            {"scheduler": "cron", "installed": True, "enabled": True},
            {"scheduler": "cron", "installed": True, "enabled": False},
            {"scheduler": "cron", "installed": True, "enabled": False},
        ]
        systemd.disable.return_value = True
        cron.disable.return_value = True
        self.mock_get_schedulers.return_value = [systemd, cron]

        conflict = self.service.dashboard()["scheduler"]
        status = self.service.configure_scheduler("takeover", interval=8)

        self.assertTrue(conflict["conflict"])
        self.assertEqual(conflict["external_scheduler"], "systemd, cron")
        systemd.disable.assert_called_once_with()
        cron.disable.assert_called_once_with()
        self.assertTrue(status["enabled"])


class TestWebScheduler(unittest.TestCase):
    """Test the dashboard-owned scheduler thread."""

    @patch("ddns.web.scheduler.MINUTE_SECONDS", 0.01)
    def test_runs_callback_and_stops_cleanly(self):
        """Run periodic work without an external task process."""
        called = threading.Event()
        scheduler = WebScheduler(called.set, interval=1)

        scheduler.start()
        self.assertTrue(called.wait(1))
        scheduler.stop()

        self.assertFalse(scheduler.status()["active"])

    @patch("ddns.web.scheduler.MINUTE_SECONDS", 0.01)
    def test_paused_scheduler_waits_until_enabled(self):
        """Keep a paused scheduler idle until explicitly resumed."""
        called = threading.Event()
        scheduler = WebScheduler(called.set, interval=1, enabled=False)
        scheduler.start()
        self.addCleanup(scheduler.stop)

        time.sleep(0.05)
        self.assertFalse(called.is_set())
        scheduler.configure(enabled=True)

        self.assertTrue(called.wait(1))

    @patch("ddns.web.scheduler.MINUTE_SECONDS", 0.01)
    def test_guard_blocks_duplicate_scheduler(self):
        """Skip runs while an external scheduler owns synchronization."""
        called = threading.Event()
        scheduler = WebScheduler(called.set, interval=1, guard=lambda: (False, "external task"))
        scheduler.start()
        self.addCleanup(scheduler.stop)

        deadline = time.time() + 1
        while not scheduler.status()["blocked_reason"] and time.time() < deadline:
            time.sleep(0.01)

        self.assertFalse(called.is_set())
        self.assertEqual(scheduler.status()["blocked_reason"], "external task")


class TestDashboardStartup(unittest.TestCase):
    """Test safe dashboard process startup."""

    @patch("ddns.web.server.sys.stdout")
    def test_status_output_is_flushed(self, mock_stdout):
        """Expose the launch URL immediately for long-running processes."""
        _write_stdout("ready\n")

        mock_stdout.write.assert_called_once_with("ready\n")
        mock_stdout.flush.assert_called_once_with()

    @patch("ddns.web.server.webbrowser.open")
    @patch("ddns.web.server._write_stdout")
    @patch("ddns.web.server.create_server")
    @patch("ddns.web.server.DashboardService")
    def test_startup_prints_single_use_launch_url(self, mock_service_class, mock_create_server, mock_stdout, mock_open):
        """Keep the long-lived API token out of terminal output."""
        service = MagicMock()
        service.config_path = "dashboard.json"
        mock_service_class.return_value = service
        server = MagicMock()
        server.server_address = ("127.0.0.1", 4321)
        server.access_token = "long-lived-secret"
        server.issue_launch_token.return_value = "single-use-token"
        server.serve_forever.side_effect = KeyboardInterrupt
        mock_create_server.return_value = server

        serve(config_path="dashboard.json", open_browser=True)

        output = "".join(call[0][0] for call in mock_stdout.call_args_list)
        launch_url = "http://127.0.0.1:4321/launch/single-use-token"
        self.assertIn(launch_url, output)
        self.assertNotIn(server.access_token, output)
        server.issue_launch_token.assert_called_once_with()
        mock_open.assert_called_once_with(launch_url)
        service.start_scheduler.assert_called_once_with()
        service.stop_scheduler.assert_called_once_with()
        server.server_close.assert_called_once_with()


class TestDashboardServer(unittest.TestCase):
    """Test local HTTP routing and write protections."""

    def setUp(self):
        """Start an ephemeral dashboard server."""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)
        config_path = os.path.join(self.temp_dir, "config.json")
        self.scheduler_patcher = patch("ddns.web.service.get_schedulers")
        self.mock_get_schedulers = self.scheduler_patcher.start()
        self.addCleanup(self.scheduler_patcher.stop)
        self.mock_scheduler = MagicMock()
        self.mock_get_schedulers.return_value = [self.mock_scheduler]
        self.mock_scheduler.get_status.return_value = {"scheduler": "test", "installed": False, "enabled": False}
        self.env_patcher = patch("ddns.web.service.load_env_config", return_value={})
        self.mock_load_env_config = self.env_patcher.start()
        self.addCleanup(self.env_patcher.stop)
        self.service = DashboardService(config_path=config_path)
        self.server = create_server(service=self.service, host="127.0.0.1", port=0, logger=MagicMock())
        self.assertFalse(self.server.allow_reuse_address)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        self.addCleanup(self._stop_server)
        self.base_url = "http://127.0.0.1:{}".format(self.server.server_address[1])
        status, _, index = self._request("/")
        self.assertEqual(status, 200)
        self.token = self.server.access_token
        self.assertNotIn(self.token, index)

    def _stop_server(self):
        """Stop the ephemeral HTTP server."""
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)

    def _request(self, path, method="GET", payload=None, headers=None):
        """Issue an HTTP request and return status, headers, and text body."""
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(self.base_url + path, data=body, headers=headers or {})
        request.get_method = lambda: method
        try:
            response = urlopen(request, timeout=5)
            content = response.read().decode("utf-8")
            return response.getcode(), response.headers, content
        except HTTPError as error:
            return error.code, error.headers, error.read().decode("utf-8")

    def test_head_never_writes_response_body(self):
        """Suppress bodies centrally for HEAD errors and helper responses."""
        handler = MagicMock()
        handler.command = "HEAD"
        send_bytes = getattr(DashboardRequestHandler._send_bytes, "im_func", DashboardRequestHandler._send_bytes)

        send_bytes(handler, 403, b"error", "application/json")

        handler.wfile.write.assert_not_called()

    def test_serves_embedded_page_and_assets(self):
        """Serve the standalone dashboard without a documentation runtime."""
        status, headers, index = self._request("/")
        asset_status, _, script = self._request("/assets/dashboard.js")

        self.assertEqual(status, 200)
        self.assertIn("frame-ancestors 'none'", headers.get("Content-Security-Policy"))
        self.assertIn("配置管理", index)
        self.assertNotIn(self.server.access_token, index)
        self.assertEqual(asset_status, 200)
        self.assertIn('api("/api/dashboard")', script)

    def test_read_api_requires_launch_token(self):
        """Protect status and credentials from other loopback users."""
        status, _, content = self._request("/api/config")

        self.assertEqual(status, 403)
        self.assertEqual(json.loads(content)["error"]["code"], "invalid_token")

    def test_dashboard_reports_invalid_runtime_environment(self):
        """Return a structured error when inherited environment values are invalid."""
        config = _valid_config()
        del config["cache_max_age"]
        headers = {"Content-Type": "application/json", "X-DDNS-Token": self.token}
        put_status, _, _ = self._request("/api/config", method="PUT", payload={"config": config}, headers=headers)
        self.mock_load_env_config.return_value = {"cache_max_age": "not-a-number"}

        status, _, content = self._request("/api/dashboard", headers={"X-DDNS-Token": self.token})

        self.assertEqual(put_status, 200)
        self.assertEqual(status, 400)
        self.assertEqual(json.loads(content)["error"]["code"], "invalid_config")

    def test_browser_bootstrap_token_is_single_use(self):
        """Exchange a short-lived launcher token without exposing the API token."""
        launch_token = self.server.issue_launch_token()

        status, _, index = self._request("/launch/" + launch_token)
        reused_status, _, reused_content = self._request("/launch/" + launch_token)

        self.assertEqual(status, 200)
        self.assertIn("配置管理", index)
        self.assertEqual(reused_status, 403)
        self.assertEqual(json.loads(reused_content)["error"]["code"], "invalid_launch_token")

    def test_write_requires_session_token(self):
        """Reject configuration writes without the page session token."""
        status, _, content = self._request(
            "/api/config",
            method="PUT",
            payload={"config": _valid_config()},
            headers={"Content-Type": "application/json"},
        )

        self.assertEqual(status, 403)
        self.assertEqual(json.loads(content)["error"]["code"], "invalid_token")

    def test_rejects_nonlocal_host_header(self):
        """Reject requests carrying a non-loopback Host header."""
        status, _, content = self._request("/", headers={"Host": "dashboard.example.com"})

        self.assertEqual(status, 421)
        self.assertEqual(json.loads(content)["error"]["code"], "invalid_host")

    def test_config_api_saves_and_reads_normalized_document(self):
        """Persist configuration through the protected JSON API."""
        headers = {"Content-Type": "application/json", "X-DDNS-Token": self.token}
        put_status, _, put_content = self._request(
            "/api/config", method="PUT", payload={"config": _valid_config()}, headers=headers
        )
        get_status, _, get_content = self._request("/api/config", headers=headers)

        self.assertEqual(put_status, 200)
        self.assertEqual(json.loads(put_content)["config"]["proxy"], ["DIRECT"])
        self.assertEqual(get_status, 200)
        get_payload = json.loads(get_content)
        self.assertEqual(get_payload["config"]["providers"][0]["index4"], ["public"])
        self.assertEqual(get_payload["model"]["defaults"]["provider"], "debug")


if __name__ == "__main__":
    unittest.main()
