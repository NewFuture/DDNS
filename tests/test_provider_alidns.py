# coding=utf-8
"""
Unit tests for AlidnsProvider

@author: Github Copilot
"""

from base_test import BaseProviderTestCase, unittest, patch
from ddns.provider.alidns import AlidnsProvider


class TestAlidnsProvider(BaseProviderTestCase):
    """Test cases for AlidnsProvider"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestAlidnsProvider, self).setUp()
        self.id = "test_access_key_id"
        self.token = "test_access_key_secret"

    def test_class_constants(self):
        """Test AlidnsProvider class constants"""
        self.assertEqual(AlidnsProvider.endpoint, "https://alidns.aliyuncs.com")
        self.assertEqual(AlidnsProvider.content_type, "application/x-www-form-urlencoded")
        self.assertTrue(AlidnsProvider.decode_response)

    def test_init_with_basic_config(self):
        """Test AlidnsProvider initialization with basic configuration"""
        provider = AlidnsProvider(self.id, self.token)
        self.assertEqual(provider.id, self.id)
        self.assertEqual(provider.token, self.token)
        self.assertEqual(provider.endpoint, "https://alidns.aliyuncs.com")

    def test_request_basic(self):
        """Test _request method with basic parameters"""
        provider = AlidnsProvider(self.id, self.token)

        # Only mock the HTTP call to avoid actual network requests
        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {"Success": True}

            result = provider._request("TestAction", DomainName="example.com")

            # Verify HTTP call was made with correct method and path
            mock_http.assert_called_once()
            call_args = mock_http.call_args
            self.assertEqual(call_args[0], ("POST", "/"))

            # Verify body and headers are present
            self.assertIn("body", call_args[1])
            self.assertIn("headers", call_args[1])

            # Verify headers contain required v3 signature fields
            headers = call_args[1]["headers"]
            self.assertIn("Authorization", headers)
            self.assertIn("x-acs-action", headers)
            self.assertIn("x-acs-date", headers)
            self.assertIn("x-acs-version", headers)
            self.assertEqual(headers["x-acs-action"], "TestAction")

            # Verify body is form-encoded
            body = call_args[1]["body"]
            self.assertIn("DomainName=example.com", body)

            self.assertEqual(result, {"Success": True})

    def test_request_filters_none_params(self):
        """Test _request method filters out None parameters"""
        provider = AlidnsProvider(self.id, self.token)

        # Only mock the HTTP call
        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {}

            provider._request("TestAction", DomainName="example.com", TTL=None, Line=None)

            # Verify HTTP call was made
            mock_http.assert_called_once()

            # Body should not contain None parameters
            call_args = mock_http.call_args[1]
            body = call_args.get("body", "")
            self.assertNotIn("TTL=None", body)
            self.assertNotIn("Line=None", body)
            self.assertIn("DomainName=example.com", body)

    def test_split_zone_and_sub_success(self):
        """Test _split_zone_and_sub method with successful response"""
        provider = AlidnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {"DomainName": "example.com", "RR": "sub"}

            main, sub, zone_id = provider._split_zone_and_sub("sub.example.com")

            mock_http.assert_called_once()
            # Verify GetMainDomainName API was called via headers
            call_headers = mock_http.call_args[1]["headers"]
            self.assertEqual(call_headers["x-acs-action"], "GetMainDomainName")

            # Verify the input parameter in body
            call_body = mock_http.call_args[1]["body"]
            self.assertIn("InputString=sub.example.com", call_body)

            self.assertEqual(main, "example.com")
            self.assertEqual(sub, "sub")
            self.assertEqual(zone_id, "example.com")

    def test_split_zone_and_sub_not_found(self):
        """Test _split_zone_and_sub method when domain is not found"""
        provider = AlidnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {}

            main, sub, zone_id = provider._split_zone_and_sub("notfound.com")

            mock_http.assert_called_once()
            self.assertIsNone(main)
            self.assertIsNone(sub)
            self.assertEqual(zone_id, "notfound.com")

    def test_query_record_success_single(self):
        """Test _query_record method with single record found"""
        provider = AlidnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {
                "DomainRecords": {"Record": [{"RR": "www", "RecordId": "123", "Value": "1.2.3.4", "Type": "A"}]}
            }

            result = provider._query_record("example.com", "www", "example.com", "A", None, {})

            mock_http.assert_called_once()
            # Verify DescribeSubDomainRecords API was called via headers
            call_headers = mock_http.call_args[1]["headers"]
            self.assertEqual(call_headers["x-acs-action"], "DescribeSubDomainRecords")

            # Verify parameters in body
            call_body = mock_http.call_args[1]["body"]
            self.assertIn("SubDomain=www.example.com", call_body)
            self.assertIn("DomainName=example.com", call_body)
            self.assertIn("Type=A", call_body)

            self.assertIsNotNone(result)
            if result:  # Type narrowing for mypy
                self.assertEqual(result["RecordId"], "123")
                self.assertEqual(result["RR"], "www")

    def test_query_record_not_found(self):
        """Test _query_record method when no matching record is found"""
        provider = AlidnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {"DomainRecords": {"Record": []}}

            result = provider._query_record("example.com", "www", "example.com", "A", None, {})

            self.assertIsNone(result)

    def test_query_record_empty_response(self):
        """Test _query_record method with empty records response"""
        provider = AlidnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {"DomainRecords": {"Record": []}}

            result = provider._query_record("example.com", "www", "example.com", "A", None, {})

            self.assertIsNone(result)

    def test_query_record_with_extra_params(self):
        """Test _query_record method with extra parameters"""
        provider = AlidnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            mock_http.return_value = {"DomainRecords": {"Record": []}}

            extra = {"Lang": "en", "Status": "Enable"}
            provider._query_record("example.com", "www", "example.com", "A", "default", extra)

            mock_http.assert_called_once()
            # Verify extra parameters are included in the request
            call_body = mock_http.call_args[1]["body"]
            self.assertIn("Lang=en", call_body)
            self.assertIn("Status=Enable", call_body)
            self.assertIn("Line=default", call_body)

    def test_create_record_success(self):
        """Test _create_record method with successful creation"""
        provider = AlidnsProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", 300, "default", {})

            mock_request.assert_called_once_with(
                "AddDomainRecord",
                DomainName="example.com",
                RR="www",
                Value="1.2.3.4",
                Type="A",
                TTL=300,
                Line="default",
            )
            self.assertTrue(result)

    def test_create_record_failure(self):
        """Test _create_record method with failed creation"""
        provider = AlidnsProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"Error": "Invalid domain"}

            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", None, None, {})

            self.assertFalse(result)

    def test_create_record_with_extra_params(self):
        """Test _create_record method with extra parameters"""
        provider = AlidnsProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            extra = {"Priority": 10, "Remark": "Test record"}
            result = provider._create_record("t.com", "www", "t.com", "1.2.3.4", "A", 300, "default", extra)

            mock_request.assert_called_once_with(
                "AddDomainRecord",
                DomainName="t.com",
                RR="www",
                Value="1.2.3.4",
                Type="A",
                TTL=300,
                Line="default",
                Priority=10,
                Remark="Test record",
            )
            self.assertTrue(result)

    def test_update_record_success(self):
        """Test _update_record method with successful update"""
        provider = AlidnsProvider(self.id, self.token)

        old_record = {"RecordId": "123456", "RR": "www", "Line": "default"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", 600, "unicom", {})

            mock_request.assert_called_once_with(
                "UpdateDomainRecord", RecordId="123456", Value="5.6.7.8", RR="www", Type="A", TTL=600, Line="unicom"
            )
            self.assertTrue(result)

    def test_update_record_with_fallback_line(self):
        """Test _update_record method uses old record's line when line is None"""
        provider = AlidnsProvider(self.id, self.token)

        old_record = {"RecordId": "123456", "RR": "www", "Line": "default"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", None, None, {})

            mock_request.assert_called_once_with(
                "UpdateDomainRecord",
                RecordId="123456",
                Value="5.6.7.8",
                RR="www",
                Type="A",
                TTL=None,
                Line="default",  # Should use old record's line
            )
            self.assertTrue(result)

    def test_update_record_failure(self):
        """Test _update_record method with failed update"""
        provider = AlidnsProvider(self.id, self.token)

        old_record = {"RecordId": "123456", "RR": "www", "Line": "default"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"Error": "Record not found"}

            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", None, None, {})

            self.assertFalse(result)

    def test_update_record_no_changes(self):
        """Test _update_record method when no changes are detected"""
        provider = AlidnsProvider(self.id, self.token)

        old_record = {"RecordId": "123456", "RR": "www", "Value": "1.2.3.4", "Type": "A", "TTL": 300, "Line": "default"}

        with patch.object(provider, "_request") as mock_request:
            # Same value, type, and TTL should skip update
            result = provider._update_record("example.com", old_record, "1.2.3.4", "A", 300, "default", {})

            # Should return True without making any API calls
            self.assertTrue(result)
            mock_request.assert_not_called()

    def test_update_record_with_extra_params(self):
        """Test _update_record method with extra parameters"""
        provider = AlidnsProvider(self.id, self.token)

        old_record = {"RecordId": "123456", "RR": "www", "Line": "default"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            extra = {"Priority": 20, "Remark": "Updated record"}
            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", 600, "unicom", extra)

            mock_request.assert_called_once_with(
                "UpdateDomainRecord",
                RecordId="123456",
                Value="5.6.7.8",
                RR="www",
                Type="A",
                TTL=600,
                Line="unicom",
                Priority=20,
                Remark="Updated record",
            )
            self.assertTrue(result)

    def test_update_record_extra_priority_over_old_record(self):
        """Test that extra parameters take priority over old_record values"""
        provider = AlidnsProvider(self.id, self.token)

        old_record = {"RecordId": "123456", "RR": "www", "Line": "default", "Priority": 10, "Remark": "Old remark"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            # extra should override old_record's Priority and Remark
            extra = {"Priority": 20, "Remark": "New remark from extra"}
            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", 600, "unicom", extra)

            mock_request.assert_called_once_with(
                "UpdateDomainRecord",
                RecordId="123456",
                Value="5.6.7.8",
                RR="www",
                Type="A",
                TTL=600,
                Line="unicom",
                Priority=20,  # Should use extra, not old_record's 10
                Remark="New remark from extra",  # Should use extra, not old_record's "Old remark"
            )
            self.assertTrue(result)

    def test_line_configuration_support(self):
        """Test that AlidnsProvider supports line configuration"""
        provider = AlidnsProvider(self.id, self.token)

        old_record = {"RecordId": "123456", "RR": "www", "Line": "default"}

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            # Test with custom line parameter
            result = provider._update_record("example.com", old_record, "5.6.7.8", "A", 600, "telecom", {})

            mock_request.assert_called_once_with(
                "UpdateDomainRecord",
                RecordId="123456",
                Value="5.6.7.8",
                RR="www",
                Type="A",
                TTL=600,
                Line="telecom",  # Should use the provided line parameter
            )
            self.assertTrue(result)

    def test_create_record_with_line(self):
        """Test _create_record method with line parameter"""
        provider = AlidnsProvider(self.id, self.token)

        with patch.object(provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            result = provider._create_record("example.com", "www", "example.com", "1.2.3.4", "A", 300, "unicom", {})

            mock_request.assert_called_once_with(
                "AddDomainRecord", DomainName="example.com", RR="www", Value="1.2.3.4", Type="A", TTL=300, Line="unicom"
            )
            self.assertTrue(result)


class TestAlidnsProviderIntegration(BaseProviderTestCase):
    """Integration test cases for AlidnsProvider - testing with minimal mocking"""

    def setUp(self):
        """Set up test fixtures"""
        super(TestAlidnsProviderIntegration, self).setUp()
        self.id = "test_access_key_id"
        self.token = "test_access_key_secret"

    def test_full_workflow_create_new_record(self):
        """Test complete workflow for creating a new record"""
        provider = AlidnsProvider(self.id, self.token)

        # Mock only the HTTP layer to simulate API responses
        with patch.object(provider, "_http") as mock_http:
            # Simulate API responses in order: GetMainDomainName, DescribeSubDomainRecords, AddDomainRecord
            mock_http.side_effect = [
                {"DomainName": "example.com", "RR": "www"},  # _split_zone_and_sub response
                {"DomainRecords": {"Record": []}},  # _query_record response (no existing record)
                {"RecordId": "123456"},  # _create_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300, "default")

            self.assertTrue(result)
            # Verify the actual HTTP calls made - should be 3 calls
            self.assertEqual(mock_http.call_count, 3)

            # Check that proper API actions were called by examining request headers
            call_actions = [call[1]["headers"]["x-acs-action"] for call in mock_http.call_args_list]
            self.assertIn("GetMainDomainName", call_actions)
            self.assertIn("DescribeSubDomainRecords", call_actions)
            self.assertIn("AddDomainRecord", call_actions)

    def test_full_workflow_update_existing_record(self):
        """Test complete workflow for updating an existing record"""
        provider = AlidnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            # Simulate API responses: GetMainDomainName, DescribeSubDomainRecords, UpdateDomainRecord
            mock_http.side_effect = [
                {"DomainName": "example.com", "RR": "www"},  # _split_zone_and_sub response
                {  # _query_record response (existing record found)
                    "DomainRecords": {
                        "Record": [
                            {"RecordId": "123456", "RR": "www", "Value": "5.6.7.8", "Type": "A", "Line": "default"}
                        ]
                    }
                },
                {"RecordId": "123456"},  # _update_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 300, "default")

            self.assertTrue(result)
            # Verify 3 HTTP calls were made
            self.assertEqual(mock_http.call_count, 3)

            # Check that UpdateDomainRecord was called
            call_actions = [call[1]["headers"]["x-acs-action"] for call in mock_http.call_args_list]
            self.assertIn("UpdateDomainRecord", call_actions)

    def test_full_workflow_zone_not_found(self):
        """Test complete workflow when zone is not found"""
        provider = AlidnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            # Simulate API returning empty response for zone query
            mock_http.return_value = {}

            # Should return False when zone not found
            result = provider.set_record("www.nonexistent.com", "1.2.3.4", "A")
            self.assertFalse(result)

    def test_full_workflow_create_failure(self):
        """Test complete workflow when record creation fails"""
        provider = AlidnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            # Simulate responses: zone found, no existing record, creation fails
            mock_http.side_effect = [
                {"DomainName": "example.com", "RR": "www"},  # _split_zone_and_sub response
                {"DomainRecords": {"Record": []}},  # _query_record response (no existing record)
                {"Error": "API error", "Code": "InvalidParameter"},  # _create_record fails
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_update_failure(self):
        """Test complete workflow when record update fails"""
        provider = AlidnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            # Simulate responses: zone found, existing record found, update fails
            mock_http.side_effect = [
                {"DomainName": "example.com", "RR": "www"},  # _split_zone_and_sub response
                {  # _query_record response (existing record found)
                    "DomainRecords": {
                        "Record": [
                            {"RecordId": "123456", "RR": "www", "Value": "5.6.7.8", "Type": "A", "Line": "default"}
                        ]
                    }
                },
                {"Error": "API error", "Code": "InvalidParameter"},  # _update_record fails
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A")

            self.assertFalse(result)

    def test_full_workflow_with_options(self):
        """Test complete workflow with additional options like ttl and line"""
        provider = AlidnsProvider(self.id, self.token)

        with patch.object(provider, "_http") as mock_http:
            # Simulate successful creation with custom options
            mock_http.side_effect = [
                {"DomainName": "example.com", "RR": "www"},  # _split_zone_and_sub response
                {"DomainRecords": {"Record": []}},  # _query_record response (no existing record)
                {"RecordId": "123456"},  # _create_record response
            ]

            result = provider.set_record("www.example.com", "1.2.3.4", "A", 600, "unicom")

            self.assertTrue(result)
            # Verify that extra parameters are passed through correctly
            self.assertEqual(mock_http.call_count, 3)

            # Check that the create call contains the correct parameters
            # Find the AddDomainRecord call (should be the last one)
            add_record_call = None
            for call in mock_http.call_args_list:
                if call[1]["headers"]["x-acs-action"] == "AddDomainRecord":
                    add_record_call = call
                    break

            self.assertIsNotNone(add_record_call)
            if add_record_call:
                create_body = add_record_call[1]["body"]
                self.assertIn("TTL=600", create_body)
                self.assertIn("Line=unicom", create_body)


if __name__ == "__main__":
    unittest.main()
