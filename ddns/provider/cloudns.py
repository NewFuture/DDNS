# coding=utf-8
"""
ClouDNS API
@doc: https://www.cloudns.net/wiki/
@author: NewFuture
"""

from ._base import BaseProvider, TYPE_FORM


class CloudnsProvider(BaseProvider):
    """
    ClouDNS API
    ClouDNS 接口解析操作库
    """

    endpoint = "https://api.cloudns.net"
    content_type = TYPE_FORM
    DEFAULT_TTL = 60  # Minimum TTL (60 seconds) for faster updates

    def _request(self, action, **params):
        # type: (str, **(str | int | None)) -> dict | None
        """
        发送请求数据，自动添加认证参数

        Send request to ClouDNS API with authentication.

        Args:
            action (str): API endpoint path
            params: API parameters

        Returns:
            dict|None: Response data or None on error
        """
        # Add authentication
        params["auth-id"] = self.id
        params["auth-password"] = self.token

        # Filter None values
        params = {k: v for k, v in params.items() if v is not None}

        data = self._http("POST", action, body=params)

        # ClouDNS API returns different formats:
        # - Success: {"status": "Success", ...}
        # - Failure: {"status": "Failed", "statusDescription": "..."}
        # - Query: raw data (e.g., {"id1": {...}, "id2": {...}}) without status field

        # Check for explicit error status
        if data and isinstance(data, dict) and data.get("status") == "Failed":
            error_msg = data.get("statusDescription", "Unknown error")
            self.logger.warning("ClouDNS API error: %s", error_msg)
            return None

        return data

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """
        查询域名区域ID

        Query zone ID for domain.
        ClouDNS uses domain name directly as zone identifier.

        Args:
            domain (str): Domain name

        Returns:
            str: Domain name (used as zone ID)
        """
        # ClouDNS uses domain-name directly, no numeric zone ID
        return domain

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict | None) -> dict | None
        """
        查询DNS记录

        Query DNS record.
        https://www.cloudns.net/wiki/article/57/

        Args:
            zone_id (str): Zone ID (domain name for ClouDNS)
            subdomain (str): Subdomain
            main_domain (str): Main domain
            record_type (str): Record type (A, AAAA, etc.)
            line (str|None): Line (not used by ClouDNS)
            extra (dict|None): Extra parameters

        Returns:
            dict|None: Record data or None if not found
        """
        # For @ (root) records, ClouDNS uses empty string
        host = "" if subdomain == "@" else subdomain

        params = {"domain-name": zone_id, "host": host, "type": record_type}
        data = self._request("/dns/records.json", **params)

        if not data or not isinstance(data, dict):
            return None

        # Check if it's an error response (has status field)
        if "status" in data:
            return None

        # ClouDNS returns records as dict: {"id1": {record_data}, "id2": {record_data}}
        # Find matching record
        for record in data.values():
            record_host = record.get("host", "")
            # Match host (handle both "" and "@" for root records)
            if record_host == host or (subdomain == "@" and record_host in ("", "@")):
                if record.get("type") == record_type:
                    return record

        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int | None, str | None, dict | None) -> bool
        """
        创建DNS记录

        Create new DNS record.
        https://www.cloudns.net/wiki/article/58/

        Args:
            zone_id (str): Zone ID (domain name)
            subdomain (str): Subdomain
            main_domain (str): Main domain
            value (str): Record value (IP address)
            record_type (str): Record type (A, AAAA, etc.)
            ttl (int|None): TTL in seconds
            line (str|None): Line (not used by ClouDNS)
            extra (dict|None): Extra parameters

        Returns:
            bool: True if successful, False otherwise
        """
        # Use default TTL if not specified
        if ttl is None:
            ttl = self.DEFAULT_TTL

        # For @ (root) records, use empty string
        host = "" if subdomain == "@" else subdomain

        params = {"domain-name": zone_id, "record-type": record_type, "host": host, "record": value, "ttl": ttl}
        data = self._request("/dns/add-record.json", **params)

        if data and data.get("status") == "Success":
            self.logger.info("Record created successfully")
            return True

        self.logger.error("Failed to create record: %s", data)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | None, str | None, dict | None) -> bool
        """
        更新DNS记录

        Update existing DNS record.
        https://www.cloudns.net/wiki/article/60/

        Args:
            zone_id (str): Zone ID (domain name)
            old_record (dict): Existing record data
            value (str): New record value (IP address)
            record_type (str): Record type (A, AAAA, etc.)
            ttl (int|None): TTL in seconds
            line (str|None): Line (not used by ClouDNS)
            extra (dict|None): Extra parameters

        Returns:
            bool: True if successful, False otherwise
        """
        # Use default TTL if not specified
        if ttl is None:
            ttl = self.DEFAULT_TTL

        record_id = old_record.get("id")
        if not record_id:
            self.logger.error("Record ID not found in old_record")
            return False

        # Get original host from record
        host = old_record.get("host", "")

        params = {"domain-name": zone_id, "record-id": record_id, "host": host, "record": value, "ttl": ttl}
        data = self._request("/dns/mod-record.json", **params)

        if data and data.get("status") == "Success":
            self.logger.info("Record updated successfully")
            return True

        self.logger.error("Failed to update record: %s", data)
        return False
