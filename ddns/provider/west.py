# coding=utf-8
"""
West.cn DNS API
西部数码 DNS 服务商接口

@doc: https://console-docs.apipost.cn/preview/bf57a993975b67e0/7b363d9b8808faa2
@author: NewFuture
"""

from ._base import SimpleProvider, TYPE_FORM


class WestProvider(SimpleProvider):
    """
    West.cn DNS Provider
    西部数码 DNS 服务商接口

    Supports two authentication methods:
    1. Domain auth (apidomainkey): Set id to domain name and token to apidomainkey
    2. Account auth (username + apikey): Set id to username and token to MD5 of API password

    API Documentation:
    https://console-docs.apipost.cn/preview/bf57a993975b67e0/7b363d9b8808faa2
    """

    endpoint = "https://api.west.cn/API/v2/domain/dns/"
    content_type = TYPE_FORM

    # Line mapping for West.cn (线路映射)
    LINE_MAPPING = {
        "": "",  # Default line
        "默认": "",  # Default
        "电信": "LTEL",  # China Telecom
        "联通": "LCNC",  # China Unicom
        "移动": "LMOB",  # China Mobile
        "教育网": "LEDU",  # Education Network
        "搜索引擎": "LSEO",  # Search Engine
        "境外": "LFOR",  # Overseas
    }

    def _validate(self):
        # type: () -> None
        """
        Validate authentication credentials.
        West.cn supports two authentication methods, so id is optional for domain auth.
        """
        if not self.token:
            raise ValueError("token (apidomainkey or apikey) must be configured")
        if not self.endpoint:
            raise ValueError("API endpoint must be defined in {}".format(self.__class__.__name__))

    def _get_auth_params(self):
        # type: () -> dict
        """
        Get authentication parameters based on configured credentials.

        Authentication modes:
        - Account auth: id (username) + token (MD5 of API password)
        - Domain auth: token only (apidomainkey, MD5 of domain password)

        Returns:
            dict: Authentication parameters for API request
        """
        if self.id:
            # Account auth mode: id is username, token is apikey (MD5 of password)
            return {"username": self.id, "apikey": self.token}
        else:
            # Domain auth mode: only token (apidomainkey), no username needed
            return {"apidomainkey": self.token}

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        # type: (str, str, str, str | int | None, str | None, **object) -> bool
        """
        Set DNS record using the dnsrec.update API endpoint.

        This uses West.cn's DDNS update API which automatically handles
        creating or updating records based on whether they exist.

        Args:
            domain (str): Full domain name (e.g., 'www.example.com')
            value (str): Record value (IP address)
            record_type (str): Record type (A or AAAA), auto-detected based on value
            ttl (int | None): TTL value (not used by dnsrec.update)
            line (str | None): Line routing option
            extra (dict): Extra parameters

        Returns:
            bool: True on success, False on failure
        """
        domain = domain.lower()
        self.logger.info("%s => %s (%s)", domain, value, record_type)

        # Parse domain to get subdomain and main domain
        subdomain, main_domain = self._parse_domain(domain)

        # Build request parameters
        params = {"act": "dnsrec.update", "domain": main_domain, "hostname": subdomain, "record_value": value}

        # Add authentication parameters
        params.update(self._get_auth_params())

        # Add line if specified
        if line:
            record_line = self.LINE_MAPPING.get(line, line)
            if record_line:
                params["record_line"] = record_line

        # Make API request
        try:
            response = self._http("POST", "", body=params)
            if response and isinstance(response, dict):
                code = response.get("code")
                if code == 200:
                    record_id = response.get("body", {}).get("record_id")
                    self.logger.info("Record updated successfully: %s (id=%s)", domain, record_id)
                    return True
                else:
                    msg = response.get("msg", "Unknown error")
                    self.logger.error("Failed to update record: %s", msg)
                    return False
            else:
                self.logger.error("Invalid API response: %s", response)
                return False
        except Exception as e:
            self.logger.error("API request failed: %s", e)
            return False

    def _parse_domain(self, domain):
        # type: (str) -> tuple[str, str]
        """
        Parse full domain name into subdomain and main domain.

        Supports custom separator format (~ or +) for explicit domain splitting.

        Args:
            domain (str): Full domain name

        Returns:
            tuple[str, str]: (subdomain, main_domain)
        """
        # Check for custom separator
        for sep in ("~", "+"):
            if sep in domain:
                parts = domain.split(sep, 1)
                return parts[0], parts[1]

        # Default domain parsing: assume last two parts are main domain
        # e.g., 'www.example.com' -> ('www', 'example.com')
        parts = domain.split(".")
        if len(parts) <= 2:
            # Root domain or simple domain
            return "@", domain
        else:
            # Subdomain
            main_domain = ".".join(parts[-2:])
            subdomain = ".".join(parts[:-2])
            return subdomain, main_domain
