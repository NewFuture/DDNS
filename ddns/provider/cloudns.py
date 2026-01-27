# coding=utf-8
"""
ClouDNS API
@author: NewFuture (modifications for ClouDNS)
"""

from ._base import BaseProvider, TYPE_FORM


class CloudnsProvider(BaseProvider):
    """
    ClouDNS API
    ClouDNS 接口解析操作库
    """

    endpoint = "https://api.cloudns.net"
    content_type = TYPE_FORM

    def _request(self, action, **params):
        """
        发送请求数据，自动添加认证参数

        Send request to ClouDNS API.
        """
        # Add authentication
        params["auth-id"] = self.id
        params["auth-password"] = self.token

        # Filter None values
        params = {k: v for k, v in params.items() if v is not None}

        data = self._http("POST", action, body=params)

        # CloudNS API returns different formats:
        # - Success for modifications: {"status": "Success", ...}
        # - Failure: {"status": "Failed", "statusDescription": "..."}
        # - Query success: raw data (e.g., {"id1": {...}, "id2": {...}}) without status field

        # Check for explicit error status
        if data and isinstance(data, dict):
            if data.get("status") == "Failed":
                error_msg = data.get("statusDescription", "Unknown error")
                self.logger.warning("ClouDNS API error: %s", error_msg)
                return None
            # If status is "Success" or no status field (raw data), return as-is
            return data

        return data

    def _query_zone_id(self, domain):
        """
        ClouDNS uses domain name directly as zone identifier
        """
        # ClouDNS uses domain-name directly, no numeric zone ID
        # Return the domain itself as the zone identifier
        return domain

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        """
        Query DNS records
        https://www.cloudns.net/wiki/article/57/
        """
        # For @ (root) records, ClouDNS uses empty string or "@"
        host = subdomain if subdomain != "@" else ""

        params = {
            "domain-name": zone_id,
            "host": host,
            "type": record_type
        }

        data = self._request("/dns/records.json", **params)

        if data and isinstance(data, dict):
            # CloudNS returns records as a dict with record IDs as keys
            # Format: {"id1": {record_data}, "id2": {record_data}}
            # Or error format: {"status": "Failed", ...}

            # Check if it's an error response
            if "status" in data:
                return None

            # Iterate through records (values of the dict)
            for record in data.values():
                # Match host - empty string means root
                record_host = record.get("host", "")
                if (record_host == host or
                    (record_host == "@" and subdomain == "@") or
                    (record_host == "" and subdomain == "@")):
                    if record.get("type") == record_type:
                        return record

        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        """
        Create new DNS record
        https://www.cloudns.net/wiki/article/58/
        """
        # Default TTL if not specified
        if ttl is None:
            ttl = 3600  # 1 hour default

        # For @ (root) records
        host = subdomain if subdomain != "@" else ""

        params = {
            "domain-name": zone_id,
            "record-type": record_type,
            "host": host,
            "record": value,
            "ttl": ttl
        }

        data = self._request("/dns/add-record.json", **params)

        if data and data.get("status") == "Success":
            self.logger.info("Record created successfully")
            return True
        else:
            self.logger.error("Failed to create record: %s", data)
            return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        """
        Update existing DNS record
        https://www.cloudns.net/wiki/article/60/
        """
        # Default TTL if not specified
        if ttl is None:
            ttl = 3600

        record_id = old_record.get("id")
        if not record_id:
            self.logger.error("Record ID not found in old_record")
            return False

        # Get original host
        host = old_record.get("host", "")

        params = {
            "domain-name": zone_id,
            "record-id": record_id,
            "host": host,
            "record": value,
            "ttl": ttl
        }

        data = self._request("/dns/mod-record.json", **params)

        if data and data.get("status") == "Success":
            self.logger.info("Record updated successfully")
            return True
        else:
            self.logger.error("Failed to update record: %s", data)
            return False
