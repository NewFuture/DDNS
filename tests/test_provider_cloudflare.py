# coding=utf-8
"""
Unit tests for CloudflareProvider

@author: GitHub Copilot
"""

from base_test import BaseProviderTestCase, unittest, patch
from ddns.provider.cloudflare import CloudflareProvider


class TestCloudflareProvider(BaseProviderTestCase):
    """Test cases for CloudflareProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestCloudflareProvider, self).setUp()
        self.auth_id = "test@example.com"
        self.auth_token = "test_api_key_or_token"

    def test_class_constants(self):
        """Test CloudflareProvider class constants"""
        self.assertEqual(CloudflareProvider.API, "https://api.cloudflare.com")
        self.assertEqual(CloudflareProvider.content_type, "application/json")
        self.assertTrue(CloudflareProvider.decode_response)

    def test_init_with_basic_config(self):
        """Test CloudflareProvider initialization with basic configuration"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)
        self.assertEqual(provider.auth_id, self.auth_id)
        self.assertEqual(provider.auth_token, self.auth_token)
        self.assertEqual(provider.API, "https://api.cloudflare.com")

    def test_init_with_token_only(self):
        """Test CloudflareProvider initialization with token only (Bearer auth)"""
        provider = CloudflareProvider("", self.auth_token)
        self.assertEqual(provider.auth_id, "")
        self.assertEqual(provider.auth_token, self.auth_token)

    def test_validate_success_with_email(self):
        """Test _validate method with valid email"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)
        # Should not raise any exception
        provider._validate()

    def test_validate_success_with_token_only(self):
        """Test _validate method with token only (no email)"""
        provider = CloudflareProvider("", self.auth_token)
        # Should not raise any exception
        provider._validate()

    def test_validate_failure_no_token(self):
        """Test _validate method with missing token"""
        with self.assertRaises(ValueError) as cm:
            CloudflareProvider(self.auth_id, "")
        self.assertIn("token must be configured", str(cm.exception))

    def test_validate_failure_invalid_email(self):
        """Test _validate method with invalid email format"""
        with self.assertRaises(ValueError) as cm:
            CloudflareProvider("invalid_email", self.auth_token)
        self.assertIn("ID must be a valid email or Empty", str(cm.exception))

    def test_request_with_email_auth(self):
        """Test _request method using email + API key authentication"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {"success": True, "result": {"id": "zone123"}}

            result = provider._request("GET", "/test", param1="value1")

            mock_http.assert_called_once_with(
                "GET",
                "/client/v4/zones/test",
                headers={"X-Auth-Email": self.auth_id, "X-Auth-Key": self.auth_token},
                params={"param1": "value1"},
            )
            self.assertEqual(result, {"id": "zone123"})

    def test_request_with_bearer_auth(self):
        """Test _request method using Bearer token authentication"""
        provider = CloudflareProvider("", self.auth_token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {"success": True, "result": {"id": "zone123"}}

            result = provider._request("GET", "/test", param1="value1")

            mock_http.assert_called_once_with(
                "GET",
                "/client/v4/zones/test",
                headers={"Authorization": "Bearer " + self.auth_token},
                params={"param1": "value1"},
            )
            self.assertEqual(result, {"id": "zone123"})

    def test_request_failure(self):
        """Test _request method with failed response"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {"success": False, "errors": ["Invalid API key"]}

            result = provider._request("GET", "/test")

            self.assertEqual(result, {"success": False, "errors": ["Invalid API key"]})

    def test_request_filters_none_params(self):
        """Test _request method filters out None parameters"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {"success": True, "result": {}}

            provider._request("GET", "/test", param1="value1", param2=None, param3="value3")

            # Verify None parameters were filtered out
            call_args = mock_http.call_args
            params = call_args[1]["params"]
            self.assertEqual(params, {"param1": "value1", "param3": "value3"})

    def test_query_zone_id_success(self):
        """Test _query_zone_id method with successful response"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = [
                {"id": "zone123", "name": "example.com"},
                {"id": "zone456", "name": "other.com"},
            ]

            result = provider._query_zone_id("example.com")

            mock_request.assert_called_once_with("GET", "", **{"name.exact": "example.com", "per_page": 50})
            self.assertEqual(result, "zone123")

    def test_query_zone_id_not_found(self):
        """Test _query_zone_id method when domain is not found"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = [{"id": "zone456", "name": "other.com"}]

            result = provider._query_zone_id("notfound.com")

            self.assertIsNone(result)

    def test_query_zone_id_empty_response(self):
        """Test _query_zone_id method with empty response"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = []

            result = provider._query_zone_id("example.com")

            self.assertIsNone(result)

    def test_query_record_success(self):
        """Test _query_record method with successful response"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = [
                {"id": "rec123", "name": "www.example.com", "type": "A", "content": "1.2.3.4"},
                {"id": "rec456", "name": "mail.example.com", "type": "A", "content": "5.6.7.8"},
            ]

            result = provider._query_record(
                "zone123", "www", "example.com", "A", None, {}
            )  # type: dict # type: ignore

            self.assertEqual(result["id"], "rec123")
            self.assertEqual(result["name"], "www.example.com")

            params = {"name.exact": "www.example.com"}
            mock_request.assert_called_once_with("GET", "/zone123/dns_records", type="A", per_page=10000, **params)

    def test_query_record_not_found(self):
        """Test _query_record method when no matching record is found"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch("ddns.provider.cloudflare.join_domain", autospec=True) as mock_join, patch.object(
            provider, "_request", autospec=True
        ) as mock_request:

            mock_join.return_value = "www.example.com"
            mock_request.return_value = [
                {"id": "rec456", "name": "mail.example.com", "type": "A", "content": "5.6.7.8"}
            ]

            result = provider._query_record("zone123", "www", "example.com", "A", None, {})

            self.assertIsNone(result)

    def test_query_record_with_proxy_option(self):
        """Test _query_record method with proxy option in extra parameters"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch("ddns.provider.cloudflare.join_domain") as mock_join, patch.object(
            provider, "_request"
        ) as mock_request:

            mock_join.return_value = "www.example.com"
            mock_request.return_value = []

            extra = {"proxied": True}
            provider._query_record("zone123", "www", "example.com", "A", None, extra)

            mock_request.assert_called_once_with(
                "GET",
                "/zone123/dns_records",
                type="A",
                per_page=10000,
                **{"name.exact": "www.example.com", "proxied": True}
            )

    def test_create_record_success(self):
        """Test _create_record method with successful creation"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch("ddns.provider.cloudflare.join_domain", autospec=True) as mock_join, patch.object(
            provider, "_request"
        ) as mock_request:

            mock_join.return_value = "www.example.com"
            mock_request.return_value = {"id": "rec123", "name": "www.example.com"}

            result = provider._create_record("zone123", "www", "example.com", "1.2.3.4", "A", 300, None, {})

            mock_join.assert_called_once_with("www", "example.com")
            mock_request.assert_called_once_with(
                "POST",
                "/zone123/dns_records",
                name="www.example.com",
                type="A",
                content="1.2.3.4",
                ttl=300,
                comment=provider.remark,
            )
            self.assertTrue(result)

    def test_create_record_failure(self):
        """Test _create_record method with failed creation"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch("ddns.provider.cloudflare.join_domain") as mock_join, patch.object(
            provider, "_request"
        ) as mock_request:

            mock_join.return_value = "www.example.com"
            mock_request.return_value = None  # API request failed

            result = provider._create_record("zone123", "www", "example.com", "1.2.3.4", "A", None, None, {})

            self.assertFalse(result)

    def test_create_record_with_extra_params(self):
        """Test _create_record method with extra parameters"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch("ddns.provider.cloudflare.join_domain") as mock_join, patch.object(
            provider, "_request"
        ) as mock_request:

            mock_join.return_value = "www.example.com"
            mock_request.return_value = {"id": "rec123"}

            extra = {"proxied": True, "comment": "Custom comment", "priority": 10}
            result = provider._create_record("zone123", "www", "example.com", "1.2.3.4", "A", 300, None, extra)

            mock_request.assert_called_once_with(
                "POST",
                "/zone123/dns_records",
                name="www.example.com",
                type="A",
                content="1.2.3.4",
                ttl=300,
                proxied=True,
                comment="Custom comment",
                priority=10,
            )
            self.assertTrue(result)

    def test_update_record_success(self):
        """Test _update_record method with successful update"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        old_record = {
            "id": "rec123",
            "name": "www.example.com",
            "comment": "Old comment",
            "proxied": False,
            "tags": ["tag1"],
            "settings": {"ttl": 300},
        }

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": "rec123", "content": "5.6.7.8"}

            result = provider._update_record("zone123", old_record, "5.6.7.8", "A", 600, None, {})

            mock_request.assert_called_once_with(
                "PUT",
                "/zone123/dns_records/rec123",
                type="A",
                name="www.example.com",
                content="5.6.7.8",
                ttl=600,
                comment="Managed by [DDNS v0.0.0](https://ddns.newfuture.cc)",  # Default Remark since extra is empty
                proxied=False,
                tags=["tag1"],
                settings={"ttl": 300},
            )
            self.assertTrue(result)

    def test_update_record_failure(self):
        """Test _update_record method with failed update"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        old_record = {"id": "rec123", "name": "www.example.com"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = None  # API request failed

            result = provider._update_record("zone123", old_record, "5.6.7.8", "A", None, None, {})

            self.assertFalse(result)

    def test_update_record_with_extra_params(self):
        """Test _update_record method with extra parameters overriding defaults"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        old_record = {"id": "rec123", "name": "www.example.com", "comment": "Old comment", "proxied": False}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": "rec123"}

            extra = {"comment": "New comment", "proxied": True, "priority": 20}
            result = provider._update_record("zone123", old_record, "5.6.7.8", "A", 600, None, extra)

            mock_request.assert_called_once_with(
                "PUT",
                "/zone123/dns_records/rec123",
                type="A",
                name="www.example.com",
                content="5.6.7.8",
                ttl=600,
                comment="New comment",  # extra.get("comment", self.remark)
                proxied=False,  # old_record.get("proxied", extra.get("proxied"))
                priority=20,  # From extra
                tags=None,
                settings=None,
            )
            self.assertTrue(result)

    def test_update_record_preserves_old_values(self):
        """Test _update_record method preserves proxied/tags/settings from old record, uses default comment"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        old_record = {
            "id": "rec123",
            "name": "www.example.com",
            "comment": "Preserve this",
            "proxied": True,
            "tags": ["important"],
            "settings": {"ttl": 300},
        }

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": "rec123"}

            # No extra parameters provided
            result = provider._update_record("zone123", old_record, "5.6.7.8", "A", 600, None, {})

            mock_request.assert_called_once_with(
                "PUT",
                "/zone123/dns_records/rec123",
                type="A",
                name="www.example.com",
                content="5.6.7.8",
                ttl=600,
                comment="Managed by [DDNS v0.0.0](https://ddns.newfuture.cc)",  # Default Remark
                proxied=True,  # Preserved from old record
                tags=["important"],  # Preserved from old record
                settings={"ttl": 300},  # Preserved from old record
            )
            self.assertTrue(result)


class TestCloudflareProviderIntegration(BaseProviderTestCase):
    """Integration test cases for CloudflareProvider - testing with minimal mocking"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestCloudflareProviderIntegration, self).setUp()
        self.auth_id = "test@example.com"
        self.auth_token = "test_api_key"

    def test_full_workflow_create_new_record(self):
        """Test complete workflow for creating a new record"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        # Mock only the HTTP layer to simulate API responses
        with patch.object(provider, "_request") as mock_request:
            # Simulate API responses in order: zone query, record query, record creation
            mock_request.side_effect = [
                [{"id": "zone123", "name": "example.com"}],  # _query_zone_id response
                [],  # _query_record response (no existing record)
                {"id": "rec123", "name": "www.example.com"},  # _create_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300)

            self.assertTrue(result)
            # Verify the actual API calls made
            self.assertEqual(mock_request.call_count, 3)
            mock_request.assert_any_call("GET", "", **{"name.exact": "example.com", "per_page": 50})
            mock_request.assert_any_call(
                "GET", "/zone123/dns_records", type="A", per_page=10000, **{"name.exact": "www.example.com"}
            )
            mock_request.assert_any_call(
                "POST",
                "/zone123/dns_records",
                name="www.example.com",
                type="A",
                content="1.2.3.4",
                ttl=300,
                comment="Managed by [DDNS v0.0.0](https://ddns.newfuture.cc)",
            )

    def test_full_workflow_update_existing_record(self):
        """Test complete workflow for updating an existing record"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate API responses
            mock_request.side_effect = [
                [{"id": "zone123", "name": "example.com"}],  # _query_zone_id response
                [  # _query_record response (existing record found)
                    {"id": "rec123", "name": "www.example.com", "type": "A", "content": "5.6.7.8", "proxied": False}
                ],
                {"id": "rec123", "content": "1.2.3.4"},  # _update_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300)

            self.assertTrue(result)
            # Verify the update call was made
            mock_request.assert_any_call(
                "PUT",
                "/zone123/dns_records/rec123",
                type="A",
                name="www.example.com",
                content="1.2.3.4",
                ttl=300,
                comment="Managed by [DDNS v0.0.0](https://ddns.newfuture.cc)",
                proxied=False,
                tags=None,
                settings=None,
            )

    def test_full_workflow_zone_not_found(self):
        """Test complete workflow when zone is not found"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate API returning empty array for zone query
            mock_request.return_value = []

            result = provider.set_record("www.nonexistent.com", "1.2.3.4", "A")
            self.assertFalse(result)

    def test_full_workflow_create_failure(self):
        """Test complete workflow when record creation fails"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate responses: zone found, no existing record, creation fails
            mock_request.side_effect = [
                [{"id": "zone123", "name": "example.com"}],  # _query_zone_id response
                [],  # _query_record response (no existing record)
                None,  # _create_record fails (API returns None)
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_update_failure(self):
        """Test complete workflow when record update fails"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate responses: zone found, existing record found, update fails
            mock_request.side_effect = [
                [{"id": "zone123", "name": "example.com"}],  # _query_zone_id response
                [  # _query_record response (existing record found)
                    {"id": "rec123", "name": "www.example.com", "type": "A", "content": "5.6.7.8"}
                ],
                None,  # _update_record fails (API returns None)
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_with_proxy_options(self):
        """Test complete workflow with proxy and other Cloudflare-specific options"""
        provider = CloudflareProvider(self.auth_id, self.auth_token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate successful creation with custom options
            mock_request.side_effect = [
                [{"id": "zone123", "name": "example.com"}],  # _query_zone_id response
                [],  # _query_record response (no existing record)
                {"id": "rec123", "name": "www.example.com"},  # _create_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300, None, proxied=True, priority=10)

            self.assertTrue(result)
            # Verify that extra parameters are passed through correctly
            mock_request.assert_any_call(
                "POST",
                "/zone123/dns_records",
                name="www.example.com",
                type="A",
                content="1.2.3.4",
                ttl=300,
                comment="Managed by [DDNS v0.0.0](https://ddns.newfuture.cc)",
                proxied=True,
                priority=10,
            )

    def test_full_workflow_bearer_token_auth(self):
        """Test complete workflow using Bearer token authentication"""
        provider = CloudflareProvider("", self.auth_token)  # No email, Bearer token only

        with patch.object(provider, "_request") as mock_request:
            # Simulate successful workflow
            mock_request.side_effect = [
                [{"id": "zone123", "name": "example.com"}],  # _query_zone_id response
                [],  # _query_record response (no existing record)
                {"id": "rec123", "name": "www.example.com"},  # _create_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertTrue(result)
            # The workflow should work the same regardless of auth method


if __name__ == "__main__":
    unittest.main()
