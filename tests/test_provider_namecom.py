# coding=utf-8
"""
Unit tests for NamecomProvider

@author: GitHub Copilot
"""

from base_test import BaseProviderTestCase, MagicMock, patch, unittest

from ddns.provider.namecom import NamecomProvider


class TestNamecomProvider(BaseProviderTestCase):
    """Test cases for NamecomProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestNamecomProvider, self).setUp()
        self.id = "test_username"
        self.token = "test_api_token"

    def test_class_constants(self):
        """Test NamecomProvider class constants"""
        self.assertEqual(NamecomProvider.endpoint, "https://api.name.com")
        self.assertEqual(NamecomProvider.content_type, "application/json")
        self.assertTrue(NamecomProvider.decode_response)

    def test_init_with_basic_config(self):
        """Test NamecomProvider initialization with basic configuration"""
        provider = NamecomProvider(self.id, self.token)
        self.assertEqual(provider.id, self.id)
        self.assertEqual(provider.token, self.token)
        self.assertEqual(provider.endpoint, "https://api.name.com")

    def test_validate_success(self):
        """Test _validate method with valid credentials"""
        provider = NamecomProvider(self.id, self.token)
        # Should not raise any exception
        provider._validate()

    def test_validate_failure_no_id(self):
        """Test _validate method with missing id (username)"""
        with self.assertRaises(ValueError) as cm:
            NamecomProvider("", self.token)
        self.assertIn("id (username) must be configured", str(cm.exception))

    def test_validate_failure_no_token(self):
        """Test _validate method with missing token"""
        with self.assertRaises(ValueError) as cm:
            NamecomProvider(self.id, "")
        self.assertIn("token (API token) must be configured", str(cm.exception))

    def test_get_auth_header(self):
        """Test _get_auth_header generates correct Basic Auth header"""
        provider = NamecomProvider(self.id, self.token)
        auth_header = provider._get_auth_header()

        # Basic auth should be base64 encoded "username:token"
        import base64

        expected = "Basic " + base64.b64encode("{}:{}".format(self.id, self.token).encode()).decode()
        self.assertEqual(auth_header, expected)

    def test_request_success(self):
        """Test _request method with successful response"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {"records": [], "totalCount": 0}

            result = provider._request("GET", "/core/v1/domains/example.com/records")

            mock_http.assert_called_once()
            call_args = mock_http.call_args
            self.assertEqual(call_args[0][0], "GET")
            self.assertEqual(call_args[0][1], "/core/v1/domains/example.com/records")
            self.assertIn("Authorization", call_args[1]["headers"])
            self.assertTrue(call_args[1]["headers"]["Authorization"].startswith("Basic "))
            self.assertEqual(result, {"records": [], "totalCount": 0})

    def test_request_with_body(self):
        """Test _request method with body for POST/PUT"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {"id": 123, "host": "www"}

            body = {"host": "www", "type": "A", "answer": "1.2.3.4"}
            provider._request("POST", "/core/v1/domains/example.com/records", body)

            mock_http.assert_called_once()
            call_args = mock_http.call_args
            self.assertEqual(call_args[0][0], "POST")
            self.assertEqual(call_args[1]["body"], body)

    def test_query_zone_id_success(self):
        """Test _query_zone_id method with successful response"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"records": [], "totalCount": 0}

            result = provider._query_zone_id("example.com")

            mock_request.assert_called_once_with("GET", "/core/v1/domains/example.com/records")
            self.assertEqual(result, "example.com")

    def test_query_zone_id_not_found(self):
        """Test _query_zone_id method when domain is not found"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = None

            result = provider._query_zone_id("notfound.com")

            self.assertIsNone(result)

    def test_query_zone_id_auth_error(self):
        """Test _query_zone_id method with authentication error"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.side_effect = RuntimeError("认证失败 [401]")

            with self.assertRaises(RuntimeError):
                provider._query_zone_id("example.com")

    def test_query_record_success(self):
        """Test _query_record method with successful response"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "records": [
                    {"id": 123, "host": "www", "type": "A", "answer": "1.2.3.4", "ttl": 300},
                    {"id": 124, "host": "mail", "type": "A", "answer": "5.6.7.8", "ttl": 300},
                ]
            }

            result = provider._query_record("example.com", "www", "example.com", "A", None, {})

            mock_request.assert_called_once_with("GET", "/core/v1/domains/example.com/records")
            self.assertIsNotNone(result)
            self.assertEqual(result["id"], 123)
            self.assertEqual(result["host"], "www")

    def test_query_record_not_found(self):
        """Test _query_record method when no matching record is found"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "records": [{"id": 124, "host": "mail", "type": "A", "answer": "5.6.7.8", "ttl": 300}]
            }

            result = provider._query_record("example.com", "www", "example.com", "A", None, {})

            self.assertIsNone(result)

    def test_query_record_type_mismatch(self):
        """Test _query_record method when record type doesn't match"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "records": [{"id": 123, "host": "www", "type": "CNAME", "answer": "other.com", "ttl": 300}]
            }

            result = provider._query_record("example.com", "www", "example.com", "A", None, {})

            self.assertIsNone(result)

    def test_query_record_root_domain(self):
        """Test _query_record method for root domain (@)"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "records": [
                    {"id": 123, "host": "", "type": "A", "answer": "1.2.3.4", "ttl": 300},
                    {"id": 124, "host": "www", "type": "A", "answer": "5.6.7.8", "ttl": 300},
                ]
            }

            result = provider._query_record("example.com", "@", "example.com", "A", None, {})

            self.assertIsNotNone(result)
            self.assertEqual(result["id"], 123)
            self.assertEqual(result["host"], "")

    def test_query_record_empty_response(self):
        """Test _query_record method with empty response"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"records": []}

            result = provider._query_record("example.com", "www", "example.com", "A", None, {})

            self.assertIsNone(result)

    def test_create_record_success(self):
        """Test _create_record method with successful creation"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": 123, "host": "www", "type": "A", "answer": "1.2.3.4", "ttl": 300}

            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", 300, None, {})

            mock_request.assert_called_once_with(
                "POST",
                "/core/v1/domains/example.com/records",
                {"host": "www", "type": "A", "answer": "1.2.3.4", "ttl": 300},
            )
            self.assertTrue(result)

    def test_create_record_failure(self):
        """Test _create_record method with failed creation"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = None

            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", None, None, {})

            self.assertFalse(result)

    def test_create_record_root_domain(self):
        """Test _create_record method for root domain"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": 123, "host": "", "type": "A", "answer": "1.2.3.4"}

            result = provider._create_record("example.com", "@", "example.com", "1.2.3.4", "A", None, None, {})

            call_args = mock_request.call_args
            self.assertEqual(call_args[0][2]["host"], "")  # Empty string for root
            self.assertTrue(result)

    def test_create_record_with_priority(self):
        """Test _create_record method with priority for MX records"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {
                "id": 123,
                "host": "",
                "type": "MX",
                "answer": "mail.example.com",
                "priority": 10,
            }

            extra = {"priority": 10}
            result = provider._create_record(
                "example.com", "@", "example.com", "mail.example.com", "MX", 300, None, extra
            )

            call_args = mock_request.call_args
            self.assertEqual(call_args[0][2]["priority"], 10)
            self.assertTrue(result)

    def test_create_record_ttl_minimum(self):
        """Test _create_record method enforces minimum TTL of 300"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": 123}

            # Try to set TTL less than 300
            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", 60, None, {})

            call_args = mock_request.call_args
            self.assertEqual(call_args[0][2]["ttl"], 300)  # Should be enforced to minimum 300
            self.assertTrue(result)

    def test_update_record_success(self):
        """Test _update_record method with successful update"""
        provider = NamecomProvider(self.id, self.token)

        old_record = {"id": 123, "host": "www", "type": "A", "answer": "1.2.3.4", "ttl": 300}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": 123, "host": "www", "type": "A", "answer": "5.6.7.8", "ttl": 600}

            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", 600, None, {})

            mock_request.assert_called_once_with(
                "PUT",
                "/core/v1/domains/example.com/records/123",
                {"host": "www", "type": "A", "answer": "5.6.7.8", "ttl": 600},
            )
            self.assertTrue(result)

    def test_update_record_failure(self):
        """Test _update_record method with failed update"""
        provider = NamecomProvider(self.id, self.token)

        old_record = {"id": 123, "host": "www"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = None

            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", None, None, {})

            self.assertFalse(result)

    def test_update_record_preserves_ttl(self):
        """Test _update_record method preserves existing TTL if not specified"""
        provider = NamecomProvider(self.id, self.token)

        old_record = {"id": 123, "host": "www", "type": "A", "answer": "1.2.3.4", "ttl": 600}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": 123}

            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", None, None, {})

            call_args = mock_request.call_args
            self.assertEqual(call_args[0][2]["ttl"], 600)  # Preserved from old_record
            self.assertTrue(result)

    def test_update_record_preserves_priority(self):
        """Test _update_record method preserves existing priority if not specified"""
        provider = NamecomProvider(self.id, self.token)

        old_record = {"id": 123, "host": "", "type": "MX", "answer": "mail.example.com", "ttl": 300, "priority": 10}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": 123}

            result = provider._update_record("example.com", old_record, "mail2.example.com", "MX", None, None, {})

            call_args = mock_request.call_args
            self.assertEqual(call_args[0][2]["priority"], 10)  # Preserved from old_record
            self.assertTrue(result)

    def test_update_record_override_priority(self):
        """Test _update_record method allows overriding priority via extra"""
        provider = NamecomProvider(self.id, self.token)

        old_record = {"id": 123, "host": "", "type": "MX", "answer": "mail.example.com", "priority": 10}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"id": 123}

            extra = {"priority": 20}
            result = provider._update_record("example.com", old_record, "mail2.example.com", "MX", None, None, extra)

            call_args = mock_request.call_args
            self.assertEqual(call_args[0][2]["priority"], 20)  # Overridden by extra
            self.assertTrue(result)

    def test_update_record_no_id(self):
        """Test _update_record method fails if old_record has no id"""
        provider = NamecomProvider(self.id, self.token)

        old_record = {"host": "www", "type": "A"}  # Missing id

        with patch.object(provider, "_request") as mock_request:
            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", None, None, {})

            mock_request.assert_not_called()
            self.assertFalse(result)


class TestNamecomProviderIntegration(BaseProviderTestCase):
    """Integration test cases for NamecomProvider - testing with minimal mocking"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestNamecomProviderIntegration, self).setUp()
        self.id = "test_username"
        self.token = "test_api_token"

    def test_full_workflow_create_new_record(self):
        """Test complete workflow for creating a new record"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate API responses: zone query, record query, record creation
            mock_request.side_effect = [
                {"records": [], "totalCount": 0},  # _query_zone_id response
                {"records": []},  # _query_record response (no existing record)
                {"id": 123, "host": "www", "type": "A", "answer": "1.2.3.4"},  # _create_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300)

            self.assertTrue(result)
            self.assertEqual(mock_request.call_count, 3)

    def test_full_workflow_update_existing_record(self):
        """Test complete workflow for updating an existing record"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate API responses: zone query, record query, record update
            mock_request.side_effect = [
                {"records": []},  # _query_zone_id response
                {
                    "records": [{"id": 123, "host": "www", "type": "A", "answer": "1.2.3.4", "ttl": 300}]
                },  # _query_record
                {"id": 123, "host": "www", "type": "A", "answer": "5.6.7.8"},  # _update_record response
            ]

            result = provider.set_record("www.example.com", "5.6.7.8", "A", 600)

            self.assertTrue(result)
            self.assertEqual(mock_request.call_count, 3)

    def test_full_workflow_zone_not_found(self):
        """Test complete workflow when zone is not found"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate zone not found
            mock_request.return_value = None

            result = provider.set_record("www.nonexistent.com", "1.2.3.4", "A")
            self.assertFalse(result)

    def test_full_workflow_create_failure(self):
        """Test complete workflow when record creation fails"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.side_effect = [
                {"records": []},  # _query_zone_id response
                {"records": []},  # _query_record response (no existing record)
                None,  # _create_record fails
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_update_failure(self):
        """Test complete workflow when record update fails"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.side_effect = [
                {"records": []},  # _query_zone_id response
                {"records": [{"id": 123, "host": "www", "type": "A", "answer": "1.2.3.4"}]},  # _query_record
                None,  # _update_record fails
            ]

            result = provider.set_record("www.example.com", "5.6.7.8", "A")

            self.assertFalse(result)

    def test_full_workflow_auth_error(self):
        """Test complete workflow when authentication fails"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.side_effect = RuntimeError("认证失败 [401]")

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_ipv6_record(self):
        """Test complete workflow for IPv6 AAAA record"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.side_effect = [
                {"records": []},  # _query_zone_id response
                {"records": []},  # _query_record response (no existing record)
                {"id": 123, "host": "www", "type": "AAAA", "answer": "2001:db8::1"},  # _create_record response
            ]

            result = provider.set_record("www.example.com", "2001:db8::1", "AAAA", 300)

            self.assertTrue(result)
            # Verify AAAA type was used
            create_call = mock_request.call_args_list[2]
            self.assertEqual(create_call[0][2]["type"], "AAAA")

    def test_full_workflow_root_domain(self):
        """Test complete workflow for root domain record"""
        provider = NamecomProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.side_effect = [
                {"records": []},  # _query_zone_id response
                {"records": []},  # _query_record response (no existing record)
                {"id": 123, "host": "", "type": "A", "answer": "1.2.3.4"},  # _create_record response
            ]

            result = provider.set_record("example.com", "1.2.3.4", "A", 300)

            self.assertTrue(result)
            # Verify host is empty string for root domain
            create_call = mock_request.call_args_list[2]
            self.assertEqual(create_call[0][2]["host"], "")

    def test_custom_endpoint(self):
        """Test provider with custom endpoint (e.g., sandbox)"""
        sandbox_endpoint = "https://api.dev.name.com"
        provider = NamecomProvider(self.id, self.token, endpoint=sandbox_endpoint)

        self.assertEqual(provider.endpoint, sandbox_endpoint)


if __name__ == "__main__":
    unittest.main()
