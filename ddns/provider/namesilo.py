# coding=utf-8
"""
NameSilo API Provider
DNS provider implementation for NameSilo domain registrar
@doc: https://www.namesilo.com/api-reference
@author: NewFuture & Copilot
"""

from ._base import BaseProvider, TYPE_JSON


class NamesiloProvider(BaseProvider):
    """
    NameSilo DNS API Provider

    Supports DNS record management through NameSilo's API including:
    - Domain information retrieval
    - DNS record listing
    - DNS record creation
    - DNS record updating
    """

    endpoint = "https://www.namesilo.com/api"
    content_type = TYPE_JSON

    def _validate(self):
        """Validate authentication credentials"""
        # NameSilo only requires API key (token), not ID
        if not self.token:
            raise ValueError("API key (token) must be configured for NameSilo")
        if not self.endpoint:
            raise ValueError("API endpoint must be defined in {}".format(self.__class__.__name__))

    def _request(self, operation, **params):
        # type: (str, **(str | int | bytes | bool | None)) -> dict
        """
        Send request to NameSilo API

        Args:
            operation (str): API operation name
            params: API parameters

        Returns:
            dict: API response data
        """
        # Filter out None parameters
        params = {k: v for k, v in params.items() if v is not None}

        # Add required authentication and format parameters
        params.update({"version": "1", "type": "json", "key": self.token})

        # Make API request
        response = self._http("GET", "/" + operation, queries=params)

        # Parse response
        if response and isinstance(response, dict):
            reply = response.get("reply", {})

            # Check for successful response
            if reply.get("code") == "300":  # NameSilo success code
                return reply
            else:
                # Log error details
                error_msg = reply.get("detail", "Unknown error")
                self.logger.warning("NameSilo API error [%s]: %s", reply.get("code", "unknown"), error_msg)

        return response

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """
        Query domain information to get domain as zone identifier

        For NameSilo, the domain name itself serves as the zone identifier
        We verify the domain exists by calling getDomainInfo

        Args:
            domain (str): Domain name

        Returns:
            str | None: Domain name if it exists, None otherwise
        """
        response = self._request("getDomainInfo", domain=domain)

        if response and response.get("code") == "300":
            # Domain exists, return the domain name as zone_id
            domain_info = response.get("domain", {})
            if domain_info:
                self.logger.debug("Domain found: %s", domain)
                return domain

        self.logger.warning("Domain not found or not accessible: %s", domain)
        return None

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """
        Query existing DNS record

        Args:
            zone_id (str): Domain name (zone identifier)
            subdomain (str): Subdomain name
            main_domain (str): Main domain name
            record_type (str): Record type (A, AAAA, CNAME, etc.)
            line (str | None): Line/location parameter (not used by NameSilo)
            extra (dict): Extra parameters

        Returns:
            dict | None: Record information if found
        """
        response = self._request("dnsListRecords", domain=zone_id)

        if response and response.get("code") == "300":
            records = response.get("resource_record", [])

            # Handle single record response
            if isinstance(records, dict):
                records = [records]

            # Find matching record
            for record in records:
                record_host = record.get("host", "")
                record_type_api = record.get("type", "")

                # Match subdomain and record type
                if record_host == subdomain and record_type_api == record_type:
                    self.logger.debug("Found existing record: %s", record)
                    return record

        self.logger.debug("No matching record found for %s.%s (%s)", subdomain, main_domain, record_type)
        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int | str | None, str | None, dict) -> bool
        """
        Create new DNS record

        Args:
            zone_id (str): Domain name (zone identifier)
            subdomain (str): Subdomain name
            main_domain (str): Main domain name
            value (str): Record value
            record_type (str): Record type
            ttl (int | str | None): TTL value
            line (str | None): Line parameter (not used)
            extra (dict): Extra parameters

        Returns:
            bool: True if record created successfully
        """
        params = {"domain": zone_id, "rrtype": record_type, "rrhost": subdomain, "rrvalue": value}

        # Add TTL if provided
        if ttl:
            params["rrttl"] = str(ttl)

        response = self._request("dnsAddRecord", **params)

        if response and response.get("code") == "300":
            record_id = response.get("record_id")
            self.logger.info("DNS record created successfully: %s", record_id)
            return True
        else:
            self.logger.error("Failed to create DNS record: %s", response)
            return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | str | None, str | None, dict) -> bool
        """
        Update existing DNS record

        Args:
            zone_id (str): Domain name (zone identifier)
            old_record (dict): Existing record information
            value (str): New record value
            record_type (str): Record type
            ttl (int | str | None): TTL value
            line (str | None): Line parameter (not used)
            extra (dict): Extra parameters

        Returns:
            bool: True if record updated successfully
        """
        record_id = old_record.get("record_id")
        if not record_id:
            self.logger.error("No record_id found in old_record: %s", old_record)
            return False

        params = {
            "domain": zone_id,
            "rrid": record_id,
            "rrhost": old_record.get("host", ""),
            "rrvalue": value,
            "rrtype": record_type,
        }

        # Add TTL if provided, otherwise keep existing
        if ttl:
            params["rrttl"] = str(ttl)
        else:
            # Keep existing TTL
            existing_ttl = old_record.get("ttl")
            if existing_ttl:
                params["rrttl"] = str(existing_ttl)

        response = self._request("dnsUpdateRecord", **params)

        if response and response.get("code") == "300":
            self.logger.info("DNS record updated successfully: %s", record_id)
            return True
        else:
            self.logger.error("Failed to update DNS record: %s", response)
            return False
