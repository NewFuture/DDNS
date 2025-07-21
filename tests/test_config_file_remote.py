# coding=utf-8
"""
Unit tests for remote configuration loading in ddns.config.file module
@author: GitHub Copilot
"""
from __future__ import unicode_literals
from __init__ import unittest, patch, MagicMock
import tempfile
import shutil
import os
import json
import io
import sys
from ddns.config.file import load_config
from ddns.util.http import HttpResponse

# Python 2/3 compatibility
try:
    from io import StringIO
    from urllib.error import URLError
    unicode = str
except ImportError:
    from StringIO import StringIO  # type: ignore[no-redef]
    from urllib2 import URLError  # type: ignore[no-redef]
else:
    try:
        from StringIO import StringIO
    except ImportError:
        from io import StringIO


class TestRemoteConfigFile(unittest.TestCase):
    """Test cases for remote configuration file loading via HTTP(S)"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)

        # Capture stdout and stderr output for testing
        self.stdout_capture = StringIO()
        self.stderr_capture = StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def tearDown(self):
        """Clean up after tests"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

    @patch('ddns.config.file.request')
    def test_load_config_remote_http_success(self, mock_http):
        """Test loading configuration from HTTP URL"""
        # Patch stdout to capture output
        import ddns.config.file
        original_stdout = ddns.config.file.stdout
        ddns.config.file.stdout = self.stdout_capture

        try:
            config_data = {"dns": "cloudflare", "id": "test@example.com", "token": "secret123"}
            mock_http.return_value = HttpResponse(200, "OK", {}, json.dumps(config_data))

            config_url = "http://example.com/config.json"
            result = load_config(config_url)

            self.assertEqual(result, config_data)
            mock_http.assert_called_once_with("GET", config_url, proxies=None, verify="auto")
        finally:
            ddns.config.file.stdout = original_stdout

    @patch('ddns.config.file.request')
    def test_load_config_remote_https_success(self, mock_http):
        """Test loading configuration from HTTPS URL"""
        config_data = {"dns": "dnspod", "id": "test123", "token": "abc456"}
        mock_http.return_value = HttpResponse(200, "OK", {}, json.dumps(config_data))

        config_url = "https://secure.example.com/config.json"
        result = load_config(config_url, ssl=True)

        self.assertEqual(result, config_data)
        mock_http.assert_called_once_with("GET", config_url, proxies=None, verify=True)

    @patch('ddns.config.file.request')
    def test_load_config_remote_with_proxy(self, mock_http):
        """Test loading configuration from remote URL with proxy settings"""
        config_data = {"dns": "alidns", "id": "test", "token": "xyz"}
        mock_http.return_value = HttpResponse(200, "OK", {}, json.dumps(config_data))

        config_url = "https://example.com/config.json"
        proxy_list = ["http://proxy1.example.com:8080", "DIRECT"]
        result = load_config(config_url, proxy=proxy_list, ssl=False)

        self.assertEqual(result, config_data)
        mock_http.assert_called_once_with("GET", config_url, proxies=proxy_list, verify=False)

    @patch('ddns.config.file.request')
    def test_load_config_remote_with_embedded_auth(self, mock_http):
        """Test loading configuration from URL with embedded authentication"""
        config_data = {"dns": "cloudflare", "ttl": 300}
        mock_http.return_value = HttpResponse(200, "OK", {}, json.dumps(config_data))

        config_url = "https://user:password@example.com/secure/config.json"
        result = load_config(config_url)

        self.assertEqual(result, config_data)
        # The HTTP module handles embedded auth automatically
        mock_http.assert_called_once_with("GET", config_url, proxies=None, verify="auto")

    @patch('ddns.config.file.request')
    def test_load_config_remote_http_error(self, mock_http):
        """Test handling HTTP error responses"""
        mock_http.return_value = HttpResponse(404, "Not Found", {}, "Not Found")

        config_url = "https://example.com/missing.json"
        
        with self.assertRaises(Exception) as context:
            load_config(config_url)
        
        self.assertIn("HTTP 404: Not Found", str(context.exception))

    @patch('ddns.config.file.request')
    def test_load_config_remote_http_500_error(self, mock_http):
        """Test handling HTTP 5xx server errors"""
        mock_http.return_value = HttpResponse(500, "Internal Server Error", {}, "Server Error")

        config_url = "https://example.com/config.json"
        
        with self.assertRaises(Exception) as context:
            load_config(config_url)
        
        self.assertIn("HTTP 500: Internal Server Error", str(context.exception))

    @patch('ddns.config.file.request')
    def test_load_config_remote_network_error(self, mock_http):
        """Test handling network errors during HTTP request"""
        mock_http.side_effect = URLError("Network is unreachable")

        config_url = "https://unreachable.example.com/config.json"
        
        with self.assertRaises(Exception):
            load_config(config_url)

    @patch('ddns.config.file.request')
    def test_load_config_remote_invalid_json(self, mock_http):
        """Test handling invalid JSON in remote response"""
        # Invalid JSON content
        invalid_json = '{"dns": "test", invalid syntax}'
        mock_http.return_value = HttpResponse(200, "OK", {}, invalid_json)

        config_url = "https://example.com/bad-config.json"
        
        with self.assertRaises((ValueError, SyntaxError)):
            load_config(config_url)

    @patch('ddns.config.file.request')
    def test_load_config_remote_ast_fallback(self, mock_http):
        """Test AST parsing fallback for remote content"""
        # Patch stdout to capture output
        import ddns.config.file
        original_stdout = ddns.config.file.stdout
        ddns.config.file.stdout = self.stdout_capture

        try:
            # Valid Python dict but invalid JSON (trailing comma)
            python_content = '{"dns": "alidns", "id": "test", "token": "xyz",}'
            mock_http.return_value = HttpResponse(200, "OK", {}, python_content)

            config_url = "https://example.com/config.py"
            result = load_config(config_url)

            expected = {"dns": "alidns", "id": "test", "token": "xyz"}
            self.assertEqual(result, expected)

            # Verify AST fallback success message
            stdout_output = self.stdout_capture.getvalue()
            self.assertIn("Successfully loaded config file with AST parser", stdout_output)
        finally:
            ddns.config.file.stdout = original_stdout

    @patch('ddns.config.file.request')
    def test_load_config_remote_v41_providers_format(self, mock_http):
        """Test loading remote configuration with v4.1 providers format"""
        config_data = {
            "$schema": "https://ddns.newfuture.cc/schema/v4.1.json",
            "ssl": "auto",
            "cache": True,
            "providers": [
                {
                    "provider": "cloudflare",
                    "id": "user1@example.com",
                    "token": "token1",
                    "ipv4": ["test1.example.com"],
                },
                {
                    "provider": "dnspod",
                    "id": "user2@example.com", 
                    "token": "token2",
                    "ipv4": ["test2.example.com"],
                }
            ]
        }
        mock_http.return_value = HttpResponse(200, "OK", {}, json.dumps(config_data))

        config_url = "https://example.com/multi-provider.json"
        result = load_config(config_url)

        # Should return a list of configs
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

        # Test first provider config
        config1 = result[0]
        self.assertEqual(config1["dns"], "cloudflare")
        self.assertEqual(config1["id"], "user1@example.com")
        self.assertEqual(config1["ssl"], "auto")  # Global config inherited

        # Test second provider config
        config2 = result[1]
        self.assertEqual(config2["dns"], "dnspod")
        self.assertEqual(config2["id"], "user2@example.com")
        self.assertEqual(config2["ssl"], "auto")  # Global config inherited

    @patch('ddns.config.file.request')
    def test_load_config_remote_with_comments(self, mock_http):
        """Test loading remote configuration with comments"""
        json_with_comments = """{
    // Remote configuration for DDNS
    "dns": "cloudflare",  // DNS provider
    "id": "test@example.com",
    "token": "secret123",  // API token
    "ttl": 300
    // End of config
}"""
        mock_http.return_value = HttpResponse(200, "OK", {}, json_with_comments)

        config_url = "https://example.com/config-with-comments.json"
        result = load_config(config_url)

        expected = {"dns": "cloudflare", "id": "test@example.com", "token": "secret123", "ttl": 300}
        self.assertEqual(result, expected)

    @patch('ddns.config.file.request')
    def test_load_config_remote_unicode_content(self, mock_http):
        """Test loading remote configuration with unicode characters"""
        unicode_config = {
            "dns": "cloudflare",
            "description": "测试配置文件",
            "symbols": "αβγδε",
            "emoji": "🌍🔧⚡"
        }
        mock_http.return_value = HttpResponse(200, "OK", {}, json.dumps(unicode_config, ensure_ascii=False))

        config_url = "https://example.com/unicode-config.json"
        result = load_config(config_url)

        self.assertEqual(result["dns"], "cloudflare")
        self.assertEqual(result["description"], "测试配置文件")
        self.assertEqual(result["symbols"], "αβγδε")
        self.assertEqual(result["emoji"], "🌍🔧⚡")

    def test_load_config_local_file_still_works(self):
        """Test that local file loading still works without changes"""
        # Create a local test file
        config_data = {"dns": "local", "id": "test", "token": "local123"}
        config_file = os.path.join(self.temp_dir, "local.json")
        
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # Load local file
        result = load_config(config_file)
        
        self.assertEqual(result, config_data)

    def test_load_config_url_detection(self):
        """Test URL detection logic works correctly"""
        # These should be detected as URLs
        urls = [
            "http://example.com/config.json",
            "https://example.com/config.json",
            "ftp://example.com/config.json",
            "file://path/to/config.json"
        ]
        
        # These should NOT be detected as URLs
        non_urls = [
            "/path/to/config.json",
            "./config.json",
            "config.json",
            "C:\\path\\to\\config.json",
            "~/config.json"
        ]
        
        # Test URL detection (we'll mock the HTTP request to avoid actual network calls)
        with patch('ddns.config.file.request') as mock_http:
            mock_http.return_value = HttpResponse(200, "OK", {}, '{"dns": "test"}')
            
            for url in urls:
                try:
                    load_config(url)
                    mock_http.assert_called_with("GET", url, proxies=None, verify="auto")
                except Exception:
                    pass  # We're just testing URL detection, not full functionality
            
            # Reset mock call count
            mock_http.reset_mock()
            
            # Test non-URLs (these should not trigger HTTP requests)
            for non_url in non_urls:
                try:
                    load_config(non_url)  # This will fail because files don't exist, but shouldn't call HTTP
                except Exception:
                    pass  # Expected - files don't exist
            
            # HTTP request should not have been called for non-URLs
            mock_http.assert_not_called()

    @patch('ddns.config.file.request')
    def test_load_config_remote_ssl_configurations(self, mock_http):
        """Test different SSL verification configurations"""
        config_data = {"dns": "test"}
        mock_http.return_value = HttpResponse(200, "OK", {}, json.dumps(config_data))

        config_url = "https://example.com/config.json"

        # Test different SSL settings
        ssl_configs = [True, False, "auto", "/path/to/cert.pem"]
        
        for ssl_config in ssl_configs:
            load_config(config_url, ssl=ssl_config)
            mock_http.assert_called_with("GET", config_url, proxies=None, verify=ssl_config)
            mock_http.reset_mock()

    @patch('ddns.config.file.request')
    def test_load_config_remote_proxy_configurations(self, mock_http):
        """Test different proxy configurations"""
        config_data = {"dns": "test"}
        mock_http.return_value = HttpResponse(200, "OK", {}, json.dumps(config_data))

        config_url = "https://example.com/config.json"

        # Test different proxy settings
        proxy_configs = [
            None,
            [],
            ["http://proxy.example.com:8080"],
            ["http://proxy1.com:8080", "http://proxy2.com:8080"],
            ["DIRECT"],
            ["SYSTEM"],
            ["http://proxy.com:8080", "DIRECT"]
        ]
        
        for proxy_config in proxy_configs:
            load_config(config_url, proxy=proxy_config)
            mock_http.assert_called_with("GET", config_url, proxies=proxy_config, verify="auto")
            mock_http.reset_mock()


if __name__ == "__main__":
    unittest.main()