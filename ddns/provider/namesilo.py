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

    endpoint = "https://www.namesilo.com"
    content_type = TYPE_JSON

    def _validate(self):
        """Validate authentication credentials"""
        # NameSilo only requires API key (token), not ID
        if not self.token:
            raise ValueError("API key (token) must be configured for NameSilo")
        if not self.endpoint:
            raise ValueError("API endpoint must be defined in {}".format(self.__class__.__name__))

        # Warn if ID is configured since NameSilo doesn't need it
        if self.id:
            self.logger.warning("NameSilo does not require 'id' configuration - only API key (token) is needed")

        # Show pending verification warning
        self.logger.warning("NameSilo provider implementation is pending verification - please test thoroughly")

    def _request(self, operation, **params):
        # type: (str, **(str | int | bytes | bool | None)) -> dict|None
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
        response = self._http("GET", "/api/" + operation, queries=params)

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

        return None

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """
        Query domain information to get domain as zone identifier
        @doc: https://www.namesilo.com/api-reference#domains/get-domain-info
        """
        response = self._request("getDomainInfo", domain=domain)

        if response:
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
        @doc: https://www.namesilo.com/api-reference#dns/list-dns-records
        """
        response = self._request("dnsListRecords", domain=main_domain)

        if response:
            records = response.get("resource_record", [])

            # Find matching record
            for record in records:
                if record.get("host") == subdomain and record.get("type") == record_type:
                    self.logger.debug("Found existing record: %s", record)
                    return record

        self.logger.debug("No matching record found for %s.%s (%s)", subdomain, main_domain, record_type)
        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int | str | None, str | None, dict) -> bool
        """
        Create new DNS record
        @doc: https://www.namesilo.com/api-reference#dns/add-dns-record
        """
        response = self._request(
            "dnsAddRecord", domain=main_domain, rrtype=record_type, rrhost=subdomain, rrvalue=value, rrttl=ttl
        )

        if response:
            record_id = response.get("record_id")
            self.logger.info("DNS record created successfully: %s", record_id)
            return True
        else:
            self.logger.error("Failed to create DNS record")
            return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | str | None, str | None, dict) -> bool
        """
        Update existing DNS record
        @doc: https://www.namesilo.com/api-reference#dns/update-dns-record
        """
        record_id = old_record.get("record_id")
        if not record_id:
            self.logger.error("No record_id found in old_record: %s", old_record)
            return False

        # In NameSilo, zone_id is the main domain name
        response = self._request(
            "dnsUpdateRecord",
            rrid=record_id,
            domain=zone_id,  # zone_id is main_domain in NameSilo
            rrhost=old_record.get("host"),  # host field contains subdomain
            rrvalue=value,
            rrtype=record_type,
            rrttl=ttl or old_record.get("ttl"),
        )

        if response:
            self.logger.info("DNS record updated successfully: %s", record_id)
            return True
        else:
            self.logger.error("Failed to update DNS record")
            return False
