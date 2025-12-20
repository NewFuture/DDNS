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
    1. Domain auth (apidomainkey): Uses token only (apidomainkey, MD5 of domain password); id is not used and may be None
    2. Account auth (username + apikey): Set id to username and token to MD5 of API password

    API Documentation:
    https://console-docs.apipost.cn/preview/bf57a993975b67e0/7b363d9b8808faa2
    """

    endpoint = "https://api.west.cn/API/v2/domain/dns/"
    content_type = TYPE_FORM

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

        Tries domain parsing from longest subdomain to shortest:
        e.g., ipv6.ddns.test.com => try ipv6.ddns+test.com first (longest subdomain),
        if domain not found (code=500) then try ipv6+ddns.test.com (shorter subdomain)

        Args:
            domain (str): Full domain name (e.g., 'www.example.com')
            value (str): Record value (IP address)
            record_type (str): Record type (A or AAAA), auto-detected based on value
            ttl (int | None): TTL value (not used by dnsrec.update)
            line (str | None): Line routing option (e.g., LTEL, LCNC, LMOB)
            extra (dict): Extra parameters

        Returns:
            bool: True on success, False on failure
        """
        domain = domain.lower()
        self.logger.info("%s => %s (%s)", domain, value, record_type)

        # Check for custom separator (~ or +) for explicit domain splitting
        subdomain = None
        main_domain = None
        for sep in ("~", "+"):
            if sep in domain:
                subdomain, main_domain = domain.split(sep, 1)
                break

        if subdomain is not None and main_domain is not None:
            # Use explicit domain splitting
            return self._try_update(subdomain, main_domain, value, line) or False

        # Try domain parsing from longest subdomain to shortest main domain
        # e.g., ipv6.ddns.test.com => try ipv6.ddns+test.com, then ipv6+ddns.test.com
        parts = domain.split(".")
        if len(parts) <= 2:
            # Root domain or simple domain
            return self._try_update("@", domain, value, line) or False

        # Try from longest subdomain to shortest
        # For ipv6.ddns.test.com: try (ipv6.ddns, test.com) first, then (ipv6, ddns.test.com)
        for i in range(len(parts) - 2, 0, -1):
            subdomain = ".".join(parts[:i])
            main_domain = ".".join(parts[i:])
            self.logger.debug("Trying: %s + %s", subdomain, main_domain)
            result = self._try_update(subdomain, main_domain, value, line)
            if result is not None:
                return result

        # Final fallback: try as root domain
        return self._try_update("@", domain, value, line) or False

    def _try_update(self, subdomain, main_domain, value, line):
        # type: (str, str, str, str | None) -> bool | None
        """
        Try to update DNS record with given subdomain and main_domain.

        Args:
            subdomain (str): Subdomain part (e.g., 'www' or '@')
            main_domain (str): Main domain part (e.g., 'example.com')
            value (str): Record value (IP address)
            line (str | None): Line routing option

        Returns:
            bool: True on success (code=200), False on failure (code=500 with error)
            None: if domain not found (code=500 with "not found" message), to try next combination
        """
        # Build request parameters
        params = {"act": "dnsrec.update", "domain": main_domain, "hostname": subdomain, "record_value": value}

        # Add authentication parameters
        params.update(self._get_auth_params())

        # Add line if specified
        if line:
            params["record_line"] = line

        # Make API request
        try:
            response = self._http("POST", "", body=params)
            if response and isinstance(response, dict):
                code = response.get("code")
                if code == 200:
                    record_id = response.get("body", {}).get("record_id")
                    domain_str = main_domain if subdomain == "@" else "{}.{}".format(subdomain, main_domain)
                    self.logger.info("Record updated successfully: %s (id=%s)", domain_str, record_id)
                    return True
                elif code == 500:
                    msg = response.get("msg", "Unknown error")
                    # Check if domain not found (try next combination)
                    # West.cn API returns code=500 with message containing "not found" or "不存在"
                    if "not found" in msg.lower() or "不存在" in msg:
                        self.logger.debug(
                            "Domain not found (code=%s): %s+%s, trying next...", code, subdomain, main_domain
                        )
                        return None
                    self.logger.error("Failed to update record (code=%s): %s", code, msg)
                    return False
                else:
                    msg = response.get("msg", "Unknown error")
                    self.logger.error("Unexpected response code=%s: %s", code, msg)
                    return False
            else:
                self.logger.error("Invalid API response: %s", response)
                return False
        except Exception as e:
            self.logger.error("API request failed: %s", e)
            return False
