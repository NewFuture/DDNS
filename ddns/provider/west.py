# coding=utf-8
"""
West.cn DNS API provider.

Supports domain-level apidomainkey authentication and account-level
username/apikey authentication for DDNS updates.
"""

from ._base import SimpleProvider, TYPE_FORM


class WestProvider(SimpleProvider):
    """
    西部数码 DNS 解析接口。
    """

    endpoint = "https://api.west.cn/API/v2/domain/dns"
    content_type = TYPE_FORM

    def _validate(self):
        # type: () -> None
        """
        验证认证信息。
        """
        if not self.token:
            raise ValueError("West.cn requires `token` (apidomainkey or apikey).")
        if self.id is None:
            self.id = ""
        if not self.endpoint:
            raise ValueError("API endpoint must be defined in WestProvider")

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        # type: (str, str, str, str | int | None, str | None, **object) -> bool
        """
        更新或创建 DNS 记录。
        """
        self.logger.info("%s => %s(%s)", domain, value, record_type)
        params = {"act": "dnsrec.update", "domain": domain, "hostname": domain, "record_value": value}

        domain_key = None
        if extra:
            domain_key = extra.get("domain_key") or extra.get("apidomainkey")
        if domain_key:
            params["apidomainkey"] = domain_key
        elif self.id:
            params["username"] = self.id
            params["apikey"] = self.token
        else:
            params["apidomainkey"] = self.token

        try:
            res = self._http("GET", "/", queries=params)
        except Exception as e:
            self.logger.error("Error updating West.cn record for %s: %s", domain, e)
            return False

        if not res:
            self.logger.error("Empty response from West.cn API")
            return False

        if isinstance(res, dict):
            if res.get("code") == 200:
                return True
            self.logger.error("West.cn API error: %s", res.get("msg") or res)
            return False

        if isinstance(res, str):
            if "success" in res.lower():
                return True
            self.logger.error("Unexpected West.cn API response: %s", res)
            return False

        self.logger.error("Unhandled West.cn API response: %s", res)
        return False
