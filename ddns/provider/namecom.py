# coding=utf-8
"""
Name.com DNS API Provider
@author: GitHub Copilot

API Documentation: https://docs.name.com/

Authentication: HTTP Basic Auth with username:api_token
Base URL: https://api.name.com

API Endpoints:
- List Records: GET /core/v1/domains/{domainName}/records
- Create Record: POST /core/v1/domains/{domainName}/records
- Update Record: PUT /core/v1/domains/{domainName}/records/{id}
"""

from base64 import b64encode

from ._base import TYPE_JSON, BaseProvider


class NamecomProvider(BaseProvider):
    """
    Name.com DNS Provider using the Core API.

    Inherits from BaseProvider for full CRUD DNS record management.

    Authentication uses HTTP Basic Auth with username and API token.
    """

    endpoint = "https://api.name.com"
    content_type = TYPE_JSON

    def _validate(self):
        # type: () -> None
        """
        Validate authentication credentials.

        Both username (id) and API token are required for Name.com API.
        """
        if not self.id:
            raise ValueError("id (username) must be configured for Name.com")
        if not self.token:
            raise ValueError("token (API token) must be configured for Name.com")

    def _get_auth_header(self):
        # type: () -> str
        """
        Generate HTTP Basic Auth header value.

        Returns:
            str: Base64 encoded "username:token" string
        """
        credentials = "{}:{}".format(self.id, self.token)
        encoded = b64encode(credentials.encode("utf-8")).decode("ascii")
        return "Basic " + encoded

    def _request(self, method, path, body=None):
        # type: (str, str, dict | None) -> dict | None
        """
        Send authenticated request to Name.com API.

        Args:
            method (str): HTTP method (GET, POST, PUT, DELETE)
            path (str): API path (e.g., /core/v1/domains/example.com/records)
            body (dict | None): Request body for POST/PUT requests

        Returns:
            dict | None: Parsed JSON response on success, None on failure

        Raises:
            RuntimeError: When authentication fails (401/403)
        """
        headers = {"Authorization": self._get_auth_header()}
        response = self._http(method, path, body=body, headers=headers)
        return response

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """
        Query zone ID for a domain.

        For Name.com, the zone ID is the domain name itself.
        We verify the domain exists by listing its records.

        Args:
            domain (str): Main domain name (e.g., example.com)

        Returns:
            str | None: Domain name as zone ID if exists, None otherwise
        """
        try:
            path = "/core/v1/domains/{}/records".format(domain)
            response = self._request("GET", path)
            if response is not None and "records" in response:
                return domain
        except RuntimeError as e:
            # 401/403 authentication errors are critical
            self.logger.error("Failed to query zone for %s: %s", domain, e)
            raise
        except Exception as e:
            self.logger.debug("Domain %s not found or not accessible: %s", domain, e)
        return None

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """
        Query existing DNS record.

        Args:
            zone_id (str): Zone ID (domain name for Name.com)
            subdomain (str): Subdomain part (e.g., "www" or "@" for root)
            main_domain (str): Main domain (e.g., "example.com")
            record_type (str): Record type (A, AAAA, CNAME, etc.)
            line (str | None): Line/route info (not used for Name.com)
            extra (dict): Extra parameters (not used for Name.com)

        Returns:
            dict | None: Record info dict if found, None otherwise
        """
        try:
            path = "/core/v1/domains/{}/records".format(zone_id)
            response = self._request("GET", path)
            if not response or "records" not in response:
                return None

            records = response.get("records", [])
            # Name.com uses "host" for subdomain, "@" for root
            host = subdomain if subdomain and subdomain != "@" else ""
            for record in records:
                if record.get("host", "") == host and record.get("type") == record_type:
                    self.logger.debug("Found record: %s", record)
                    return record
        except RuntimeError:
            # Re-raise auth errors
            raise
        except Exception as e:
            self.logger.error("Error querying records: %s", e)
        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int | str | None, str | None, dict) -> bool
        """
        Create a new DNS record.

        Args:
            zone_id (str): Zone ID (domain name for Name.com)
            subdomain (str): Subdomain part (e.g., "www" or "@" for root)
            main_domain (str): Main domain (e.g., "example.com")
            value (str): Record value (IP address, target, etc.)
            record_type (str): Record type (A, AAAA, CNAME, etc.)
            ttl (int | str | None): TTL in seconds (minimum 300)
            line (str | None): Line/route info (not used)
            extra (dict): Extra parameters

        Returns:
            bool: True on success, False on failure
        """
        path = "/core/v1/domains/{}/records".format(zone_id)
        # Name.com uses "host" for subdomain, empty string for root
        host = subdomain if subdomain and subdomain != "@" else ""

        body = {"host": host, "type": record_type, "answer": value}

        # Add TTL if specified (minimum 300)
        if ttl is not None:
            body["ttl"] = max(int(ttl), 300)

        # Add priority for MX/SRV records
        if extra.get("priority") is not None:
            body["priority"] = extra["priority"]

        try:
            response = self._request("POST", path, body)
            if response and response.get("id"):
                self.logger.info("Record created successfully: %s", response)
                return True
            self.logger.error("Failed to create record: %s", response)
        except RuntimeError:
            raise
        except Exception as e:
            self.logger.error("Error creating record: %s", e)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | str | None, str | None, dict) -> bool
        """
        Update an existing DNS record.

        Note: Name.com requires all fields to be provided for update.

        Args:
            zone_id (str): Zone ID (domain name for Name.com)
            old_record (dict): Existing record information
            value (str): New record value
            record_type (str): Record type (A, AAAA, CNAME, etc.)
            ttl (int | str | None): TTL in seconds (minimum 300)
            line (str | None): Line/route info (not used)
            extra (dict): Extra parameters

        Returns:
            bool: True on success, False on failure
        """
        record_id = old_record.get("id")
        if not record_id:
            self.logger.error("Record ID not found in old_record")
            return False

        path = "/core/v1/domains/{}/records/{}".format(zone_id, record_id)

        # Name.com requires all fields for update
        body = {"host": old_record.get("host", ""), "type": record_type, "answer": value}

        # Use provided TTL or keep existing
        if ttl is not None:
            body["ttl"] = max(int(ttl), 300)
        elif old_record.get("ttl"):
            body["ttl"] = old_record["ttl"]

        # Preserve or update priority for MX/SRV records
        if extra.get("priority") is not None:
            body["priority"] = extra["priority"]
        elif old_record.get("priority") is not None:
            body["priority"] = old_record["priority"]

        try:
            response = self._request("PUT", path, body)
            if response and response.get("id"):
                self.logger.info("Record updated successfully: %s", response)
                return True
            self.logger.error("Failed to update record: %s", response)
        except RuntimeError:
            raise
        except Exception as e:
            self.logger.error("Error updating record: %s", e)
        return False
