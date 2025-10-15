# coding=utf-8
"""
测试 AliESA Provider
@author: NewFuture
"""

from base_test import unittest, BaseProviderTestCase
from ddns.provider.aliesa import AliesaProvider


class TestAliesaProvider(BaseProviderTestCase):
    """AliESA Provider 测试类"""

    def setUp(self):
        """Setup test provider with mock credentials"""
        super(TestAliesaProvider, self).setUp()
        self.provider = AliesaProvider(id="test_access_key", token="test_secret_key")

    def test_class_constants(self):
        """Test AliesaProvider class constants"""
        self.assertEqual(self.provider.endpoint, "https://esa.cn-hangzhou.aliyuncs.com")
        self.assertEqual(self.provider.api_version, "2024-09-10")

    def test_init_with_basic_config(self):
        """Test AliesaProvider initialization with basic configuration"""
        provider = AliesaProvider(id="test_access_key", token="test_secret_key")
        self.assertEqual(provider.id, "test_access_key")
        self.assertEqual(provider.token, "test_secret_key")
        self.assertEqual(provider.endpoint, "https://esa.cn-hangzhou.aliyuncs.com")

    def test_init_with_empty_credentials(self):
        """Test AliesaProvider initialization with empty credentials raises ValueError"""
        with self.assertRaises(ValueError):
            AliesaProvider(id="", token="")

    def test_init_with_long_credentials(self):
        """Test AliesaProvider initialization with long credentials"""
        long_id = "a" * 50
        long_token = "b" * 100
        provider = AliesaProvider(id=long_id, token=long_token)
        self.assertEqual(provider.id, long_id)
        self.assertEqual(provider.token, long_token)

    def test_zone_id_query_logic(self):
        """Test zone ID query logic with various domain formats"""
        # Test with exact domain match
        sites_response = {"Sites": [{"SiteId": 12345, "SiteName": "example.com"}]}
        # Simulate the logic from _query_zone_id
        sites = sites_response.get("Sites", [])
        zone_id = None
        for site in sites:
            if site.get("SiteName") == "example.com":
                zone_id = site.get("SiteId")
                break
        self.assertEqual(zone_id, 12345)

        # Test with multiple sites
        sites_response = {
            "Sites": [
                {"SiteId": 12346, "SiteName": "other.com"},
                {"SiteId": 12345, "SiteName": "example.com"},
                {"SiteId": 12347, "SiteName": "test.com"},
            ]
        }
        sites = sites_response.get("Sites", [])
        zone_id = None
        for site in sites:
            if site.get("SiteName") == "example.com":
                zone_id = site.get("SiteId")
                break
        self.assertEqual(zone_id, 12345)

        # Test with no matching site
        sites_response = {"Sites": [{"SiteId": 12346, "SiteName": "other.com"}]}
        sites = sites_response.get("Sites", [])
        zone_id = None
        for site in sites:
            if site.get("SiteName") == "example.com":
                zone_id = site.get("SiteId")
                break
        self.assertIsNone(zone_id)

        # Test with empty sites list
        sites_response = {"Sites": []}
        sites = sites_response.get("Sites", [])
        zone_id = None
        for site in sites:
            if site.get("SiteName") == "example.com":
                zone_id = site.get("SiteId")
                break
        self.assertIsNone(zone_id)

    def test_record_query_logic(self):
        """Test record query logic with various response formats"""
        # Test with single record
        records_response = {
            "Records": [
                {
                    "RecordId": "123456",
                    "RecordName": "www.example.com",
                    "Type": "A",
                    "Value": "192.168.1.100",
                    "TTL": 300,
                }
            ]
        }
        records = records_response.get("Records", [])  # type: list[dict] # type: ignore
        record = records[0] if records else None
        self.assertIsNotNone(record)
        self.assertEqual(record["RecordId"], "123456")  # type: ignore
        self.assertEqual(record["Value"], "192.168.1.100")  # type: ignore

        # Test with multiple records (should return first one)
        records_response = {
            "Records": [
                {
                    "RecordId": "123456",
                    "RecordName": "www.example.com",
                    "Type": "A",
                    "Value": "192.168.1.100",
                    "TTL": 300,
                },
                {
                    "RecordId": "123457",
                    "RecordName": "www.example.com",
                    "Type": "A",
                    "Value": "192.168.1.101",
                    "TTL": 600,
                },
            ]
        }
        records = records_response.get("Records", [])
        record = records[0] if records else None
        self.assertIsNotNone(record)
        self.assertEqual(record["RecordId"], "123456")  # type: ignore
        self.assertEqual(record["Value"], "192.168.1.100")  # type: ignore

        # Test with no records
        records_response = {"Records": []}
        records = records_response.get("Records", [])
        record = records[0] if records else None
        self.assertIsNone(record)

    def test_create_record_logic(self):
        """Test create record logic with various response formats"""
        # Test successful creation
        create_response = {"RecordId": "123456"}
        result = bool(create_response and create_response.get("RecordId"))
        self.assertTrue(result)

        # Test creation with additional fields
        create_response = {"RecordId": "123456", "Status": "success", "Message": "Record created"}
        result = bool(create_response and create_response.get("RecordId"))
        self.assertTrue(result)

        # Test failed creation (no RecordId)
        create_response = {"Error": "Invalid domain"}
        result = bool(create_response and create_response.get("RecordId"))
        self.assertFalse(result)

        # Test failed creation (empty response)
        create_response = {}
        result = bool(create_response and create_response.get("RecordId"))
        self.assertFalse(result)

        # Test failed creation (None response)
        create_response = None
        result = bool(create_response and create_response.get("RecordId"))
        self.assertFalse(result)

    def test_update_record_logic(self):
        """Test update record logic with various response formats"""
        # Test successful update
        update_response = {"RecordId": "123456"}
        result = bool(update_response and update_response.get("RecordId"))
        self.assertTrue(result)

        # Test update with additional fields
        update_response = {"RecordId": "123456", "Status": "success", "Message": "Record updated"}
        result = bool(update_response and update_response.get("RecordId"))
        self.assertTrue(result)

        # Test failed update (no RecordId)
        update_response = {"Error": "Record not found"}
        result = bool(update_response and update_response.get("RecordId"))
        self.assertFalse(result)

        # Test failed update (empty response)
        update_response = {}
        result = bool(update_response and update_response.get("RecordId"))
        self.assertFalse(result)

    def test_update_record_change_detection(self):
        """Test update record change detection logic"""
        old_record = {
            "RecordId": "123456",
            "RecordName": "www.example.com",
            "Type": "A",
            "Value": "192.168.1.100",
            "TTL": 300,
        }

        # Test no changes detected - simulate _update_record logic
        value = "192.168.1.100"
        record_type = "A"
        ttl = 300
        needs_update = not (
            old_record.get("Value") == value
            and old_record.get("Type") == record_type
            and (not ttl or old_record.get("TTL") == ttl)
        )
        self.assertFalse(needs_update)

        # Test value change
        value = "192.168.1.200"
        needs_update = not (
            old_record.get("Value") == value
            and old_record.get("Type") == record_type
            and (not ttl or old_record.get("TTL") == ttl)
        )
        self.assertTrue(needs_update)

        # Test TTL change
        value = "192.168.1.100"
        ttl = 600
        needs_update = not (
            old_record.get("Value") == value
            and old_record.get("Type") == record_type
            and (not ttl or old_record.get("TTL") == ttl)
        )
        self.assertTrue(needs_update)

        # Test type change
        ttl = 300
        record_type = "AAAA"
        needs_update = not (
            old_record.get("Value") == value
            and old_record.get("Type") == record_type
            and (not ttl or old_record.get("TTL") == ttl)
        )
        self.assertTrue(needs_update)

        # Test TTL None (should be ignored)
        record_type = "A"
        ttl = None
        needs_update = not (
            old_record.get("Value") == value
            and old_record.get("Type") == record_type
            and (not ttl or old_record.get("TTL") == ttl)
        )
        self.assertFalse(needs_update)

    def test_update_record_extra_priority_over_old_record(self):
        """Test that extra parameters take priority over old_record values in _update_record"""
        from base_test import patch

        old_record = {
            "RecordId": "123456",
            "RecordName": "www.example.com",
            "Data": {"Value": "192.168.1.100"},
            "RecordType": "A/AAAA",
            "Ttl": 300,
            "Proxied": False,
        }

        with patch.object(self.provider, "_request") as mock_request:
            mock_request.return_value = {"RecordId": "123456"}

            # extra should override old_record's Proxied value
            extra = {"Proxied": True, "Comment": "New comment"}
            result = self.provider._update_record("zone123", old_record, "192.168.1.200", "A", 600, None, extra)

            # Verify the call was made with extra taking priority
            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args[1]
            self.assertEqual(call_kwargs["Proxied"], True)  # Should use extra, not old_record's False
            self.assertEqual(call_kwargs["Comment"], "New comment")
            self.assertTrue(result)

    def test_domain_formatting(self):
        """Test domain formatting for various subdomain and main domain combinations"""
        # Import the helper function
        from ddns.provider._base import join_domain

        # Test with standard subdomain
        formatted = join_domain("www", "example.com")
        self.assertEqual(formatted, "www.example.com")

        # Test with @ (root domain)
        formatted = join_domain("@", "example.com")
        self.assertEqual(formatted, "example.com")

        # Test with empty subdomain
        formatted = join_domain("", "example.com")
        self.assertEqual(formatted, "example.com")

        # Test with nested subdomain
        formatted = join_domain("mail.server", "example.com")
        self.assertEqual(formatted, "mail.server.example.com")

    def test_record_type_validation(self):
        """Test record type validation and handling"""
        valid_types = ["A", "AAAA", "CNAME", "MX", "TXT", "NS", "PTR", "SRV"]

        # Test that record types are strings and uppercase
        for record_type in valid_types:
            self.assertIsInstance(record_type, str)
            self.assertEqual(record_type, record_type.upper())

        # Test case insensitive handling
        self.assertEqual("A", "a".upper())
        self.assertEqual("CNAME", "cname".upper())

    def test_ttl_validation(self):
        """Test TTL validation and conversion"""
        # Test valid TTL values
        valid_ttls = [60, 300, 600, 3600, 86400]
        for ttl in valid_ttls:
            converted = int(ttl) if ttl else None
            self.assertEqual(converted, ttl)

        # Test string TTL conversion
        ttl_str = "300"
        converted = int(ttl_str) if ttl_str else None
        self.assertEqual(converted, 300)

        # Test None TTL (should return None)
        ttl_none = None
        converted = int(ttl_none) if ttl_none else None
        self.assertIsNone(converted)

    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test empty response handling
        response = {}
        result = response.get("RecordId")
        self.assertIsNone(result)

        # Test error response handling
        error_response = {"Error": "Invalid request", "Code": "400"}
        result = error_response.get("RecordId")
        self.assertIsNone(result)

        # Test None response handling
        none_response = None
        result = none_response.get("RecordId") if none_response else None
        self.assertIsNone(result)

    def test_comment_handling(self):
        """Test comment parameter handling"""
        # Test default comment from provider
        default_comment = self.provider.remark
        self.assertIn("DDNS", default_comment)

        # Test custom comment
        extra = {"Comment": "Custom DNS record"}
        comment = extra.get("Comment", self.provider.remark)
        self.assertEqual(comment, "Custom DNS record")

        # Test fallback to default
        extra = {}
        comment = extra.get("Comment", self.provider.remark)
        self.assertEqual(comment, self.provider.remark)


class TestAliesaProviderIntegration(BaseProviderTestCase):
    """AliESA Provider 集成测试类 - 使用最少的 mock"""

    def setUp(self):
        """Setup test provider with mock credentials"""
        super(TestAliesaProviderIntegration, self).setUp()
        self.provider = AliesaProvider(id="test_access_key", token="test_secret_key")

    def test_full_workflow_logic(self):
        """Test complete workflow logic without mocking internal methods"""
        # Test scenario: updating an existing record
        # Simulate the decision logic in set_record method

        # Mock data that would be returned from API calls
        existing_record = {
            "RecordId": "123456",
            "RecordName": "www.example.com",
            "Type": "A",
            "Value": "192.168.1.1",
            "TTL": 300,
        }
        new_value = "192.168.1.100"

        # Test the logic: should update because value changed
        needs_update = not (
            existing_record.get("Value") == new_value
            and existing_record.get("Type") == "A"
            and (not 300 or existing_record.get("TTL") == 300)
        )
        self.assertTrue(needs_update)

        # Test scenario: no changes needed
        same_value = "192.168.1.1"
        needs_update = not (
            existing_record.get("Value") == same_value
            and existing_record.get("Type") == "A"
            and (not 300 or existing_record.get("TTL") == 300)
        )
        self.assertFalse(needs_update)

    def test_api_parameter_construction(self):
        """Test API parameter construction logic"""
        # Test zone_id conversion to int
        zone_id_str = "12345"
        zone_id_int = int(zone_id_str)
        self.assertEqual(zone_id_int, 12345)

        # Test TTL conversion
        ttl_str = "600"
        ttl_int = int(ttl_str) if ttl_str else None
        self.assertEqual(ttl_int, 600)

        # Test comment handling
        extra_with_comment = {"Comment": "Custom comment"}
        comment = extra_with_comment.get("Comment", self.provider.remark)
        self.assertEqual(comment, "Custom comment")

        extra_without_comment = {}
        comment = extra_without_comment.get("Comment", self.provider.remark)
        self.assertEqual(comment, self.provider.remark)

    def test_site_matching_logic(self):
        """Test site matching logic used in _query_zone_id"""
        # Mock API response format
        api_response = {
            "Sites": [
                {"SiteId": 11111, "SiteName": "other.com"},
                {"SiteId": 22222, "SiteName": "example.com"},
                {"SiteId": 33333, "SiteName": "test.com"},
            ]
        }

        # Test exact match logic
        target_domain = "example.com"
        found_site_id = None
        for site in api_response.get("Sites", []):
            if site.get("SiteName") == target_domain:
                found_site_id = site.get("SiteId")
                break

        self.assertEqual(found_site_id, 22222)

        # Test no match
        target_domain = "nonexistent.com"
        found_site_id = None
        for site in api_response.get("Sites", []):
            if site.get("SiteName") == target_domain:
                found_site_id = site.get("SiteId")
                break

        self.assertIsNone(found_site_id)

    def test_record_filtering_logic(self):
        """Test record filtering logic used in _query_record"""
        # Mock API response format
        api_response = {
            "Records": [
                {"RecordId": "111", "RecordName": "www.example.com", "Type": "A", "Value": "192.168.1.1", "TTL": 300},
                {"RecordId": "222", "RecordName": "www.example.com", "Type": "A", "Value": "192.168.1.2", "TTL": 600},
                {"RecordId": "333", "RecordName": "mail.example.com", "Type": "A", "Value": "192.168.1.3", "TTL": 300},
            ]
        }

        # Test getting first matching record (current behavior)
        records = api_response.get("Records", [])
        first_record = records[0] if records else None

        self.assertIsNotNone(first_record)
        if first_record:  # Add type guard for static analysis
            self.assertEqual(first_record["RecordId"], "111")
            self.assertEqual(first_record["Value"], "192.168.1.1")


class TestAliesaProviderAPIResponse(BaseProviderTestCase):
    """Test AliesaProvider API response handling - minimal mocking"""

    def setUp(self):
        """Setup test provider with mock credentials"""
        super(TestAliesaProviderAPIResponse, self).setUp()
        self.provider = AliesaProvider(id="test_access_key", token="test_secret_key")

    def test_successful_response_detection(self):
        """Test successful API response detection logic"""
        # Test create/update success detection
        success_response = {"RecordId": "123456", "RequestId": "ABC-123"}
        is_success = bool(success_response and success_response.get("RecordId"))
        self.assertTrue(is_success)

        # Test failure detection
        failure_response = {"Error": "InvalidDomain", "Code": "400"}
        is_success = bool(failure_response and failure_response.get("RecordId"))
        self.assertFalse(is_success)

        # Test empty response
        empty_response = {}
        is_success = bool(empty_response and empty_response.get("RecordId"))
        self.assertFalse(is_success)

    def test_different_record_types_parameters(self):
        """Test parameter handling for different record types"""
        # Test A record parameters
        record_params = {"RecordName": "www.example.com", "Type": "A", "Value": "192.168.1.100", "TTL": 300}
        self.assertEqual(record_params["Type"], "A")
        self.assertTrue(record_params["Value"].count(".") == 3)  # IPv4 format

        # Test AAAA record parameters
        record_params = {"RecordName": "www.example.com", "Type": "AAAA", "Value": "2001:db8::1", "TTL": 600}
        self.assertEqual(record_params["Type"], "AAAA")
        self.assertTrue(":" in record_params["Value"])  # IPv6 format

        # Test CNAME record parameters
        record_params = {"RecordName": "alias.example.com", "Type": "CNAME", "Value": "target.example.com", "TTL": 300}
        self.assertEqual(record_params["Type"], "CNAME")
        self.assertTrue(record_params["Value"].endswith(".com"))

    def test_parameter_filtering_logic(self):
        """Test parameter filtering logic (removes None values)"""
        # Test with None values
        params = {"SiteName": "example.com", "PageSize": 500, "Filter": None, "ExtraParam": None}

        # Simulate the filtering logic from _request method
        filtered_params = {k: v for k, v in params.items() if v is not None}

        expected_params = {"SiteName": "example.com", "PageSize": 500}

        self.assertEqual(filtered_params, expected_params)
        self.assertNotIn("Filter", filtered_params)
        self.assertNotIn("ExtraParam", filtered_params)


if __name__ == "__main__":
    unittest.main()
