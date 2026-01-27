# coding=utf-8
"""
Unit tests for CloudnsProvider

@author: Claude
"""

from base_test import BaseProviderTestCase, patch, unittest

from ddns.provider.cloudns import CloudnsProvider


class TestCloudnsProvider(BaseProviderTestCase):
    """Test cases for CloudnsProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestCloudnsProvider, self).setUp()
        self.id = "1234"
        self.token = "test_password"

    def test_class_constants(self):
        """Test CloudnsProvider class constants"""
        self.assertEqual(CloudnsProvider.endpoint, "https://api.cloudns.net")
        self.assertEqual(CloudnsProvider.content_type, "application/x-www-form-urlencoded")
        self.assertTrue(CloudnsProvider.decode_response)

    def test_init(self):
        """Test CloudnsProvider initialization"""
        provider = CloudnsProvider(self.id, self.token)
        self.assertEqual(provider.id, self.id)
        self.assertEqual(provider.token, self.token)
        self.assertEqual(provider.endpoint, "https://api.cloudns.net")

    def test_query_zone_id(self):
        """Test _query_zone_id returns domain itself"""
        provider = CloudnsProvider(self.id, self.token)
        result = provider._query_zone_id("example.com")
        self.assertEqual(result, "example.com")

    def test_query_record_success(self):
        """Test _query_record method with successful response"""
        provider = CloudnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            # CloudNS returns records as dict with record IDs as keys
            mock_http.return_value = {
                "12345": {"id": "12345", "host": "www", "type": "A", "record": "1.2.3.4", "ttl": "3600"}
            }

            result = provider._query_record("example.com", "www", "example.com", "A", None, {})

            self.assertIsNotNone(result)
            self.assertEqual(result["id"], "12345")
            self.assertEqual(result["host"], "www")

    def test_query_record_root(self):
        """Test _query_record for root (@) records"""
        provider = CloudnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {
                "12345": {"id": "12345", "host": "@", "type": "A", "record": "1.2.3.4", "ttl": "3600"}
            }

            result = provider._query_record("example.com", "@", "example.com", "A", None, {})

            self.assertIsNotNone(result)
            self.assertEqual(result["id"], "12345")

    def test_query_record_not_found(self):
        """Test _query_record when no matching record is found"""
        provider = CloudnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            # Empty dict means no records found
            mock_http.return_value = {}

            result = provider._query_record("example.com", "www", "example.com", "A", None, {})

            self.assertIsNone(result)

    def test_create_record_success(self):
        """Test _create_record method with successful creation"""
        provider = CloudnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {
                "status": "Success",
                "statusDescription": "Successfully added"
            }

            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", 3600, None, {})

            self.assertTrue(result)

    def test_create_record_default_ttl(self):
        """Test _create_record uses default TTL when None is provided"""
        provider = CloudnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {
                "status": "Success"
            }

            provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", None, None, {})

            # Verify default TTL was used
            call_args = mock_http.call_args
            body = call_args[1]["body"]
            self.assertEqual(body["ttl"], 60)

    def test_create_record_failure(self):
        """Test _create_record method with failed creation"""
        provider = CloudnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {
                "status": "Failed",
                "statusDescription": "Invalid authentication"
            }

            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", 3600, None, {})

            self.assertFalse(result)

    def test_update_record_success(self):
        """Test _update_record method with successful update"""
        provider = CloudnsProvider(self.id, self.token)

        old_record = {"id": "12345", "host": "www", "type": "A", "record": "5.6.7.8"}

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {
                "status": "Success",
                "statusDescription": "Successfully updated"
            }

            result = provider._update_record("example.com", old_record, "1.2.3.4", "A", 3600, None, {})

            self.assertTrue(result)

    def test_update_record_missing_id(self):
        """Test _update_record when old_record has no id"""
        provider = CloudnsProvider(self.id, self.token)

        old_record = {"host": "www", "type": "A"}  # No id field

        result = provider._update_record("example.com", old_record, "1.2.3.4", "A", 3600, None, {})

        self.assertFalse(result)

    def test_update_record_default_ttl(self):
        """Test _update_record uses default TTL when None is provided"""
        provider = CloudnsProvider(self.id, self.token)

        old_record = {"id": "12345", "host": "www"}

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {
                "status": "Success"
            }

            provider._update_record("example.com", old_record, "1.2.3.4", "A", None, None, {})

            # Verify default TTL was used
            call_args = mock_http.call_args
            body = call_args[1]["body"]
            self.assertEqual(body["ttl"], 60)

    def test_request_adds_auth(self):
        """Test _request method adds authentication parameters"""
        provider = CloudnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {"status": "Success"}

            provider._request("/dns/records.json", **{"domain-name": "example.com"})

            call_args = mock_http.call_args
            body = call_args[1]["body"]
            self.assertEqual(body["auth-id"], self.id)
            self.assertEqual(body["auth-password"], self.token)


class TestCloudnsProviderIntegration(BaseProviderTestCase):
    """Integration test cases for CloudnsProvider - testing with minimal mocking"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestCloudnsProviderIntegration, self).setUp()
        self.id = "1234"
        self.token = "test_password"

    def test_full_workflow_create_new_record(self):
        """Test complete workflow for creating a new record"""
        provider = CloudnsProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate API responses
            mock_request.side_effect = [
                {},  # No existing record (empty dict)
                {"status": "Success"}  # Record created
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 3600)

            self.assertTrue(result)

    def test_full_workflow_update_existing_record(self):
        """Test complete workflow for updating an existing record"""
        provider = CloudnsProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            # Simulate API responses
            existing_record = {"id": "12345", "host": "www", "type": "A", "record": "5.6.7.8"}
            mock_request.side_effect = [
                {"12345": existing_record},  # Existing record found
                {"status": "Success"}  # Record updated
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 3600)

            self.assertTrue(result)

    def test_full_workflow_root_record(self):
        """Test workflow for root (@) record"""
        provider = CloudnsProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.side_effect = [
                {},  # No existing record (empty dict)
                {"status": "Success"}  # Record created
            ]

            result = provider.set_record("example.com", "1.2.3.4", "A", 3600)

            self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
