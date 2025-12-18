# coding=utf-8
"""
West.cn (西部数码) DNS Provider

API 文档参考:
- https://api.west.cn/API/v2/domain/dns/
- https://www.west.cn/CustomerCenter/doc/apiV2.html
"""

from ._base import TYPE_FORM, BaseProvider


class WestProvider(BaseProvider):
    """
    西部数码 DNS 解析 Provider

    支持两种认证方式:
    1. 域名级 apidomainkey
    2. 用户级 username + apikey
    """

    endpoint = "https://api.west.cn"
    content_type = TYPE_FORM

    def _validate(self):
        # type: () -> None
        if not self.token:
            raise ValueError("token (apidomainkey/apikey) must be configured for West.cn")
        if not self.endpoint:
            raise ValueError("API endpoint must be defined in {}".format(self.__class__.__name__))
        if not self.id:
            self.logger.info("Using domain-level apidomainkey authentication")

    def _auth_params(self, domain):
        # type: (str) -> dict[str, str]
        params = {"domain": domain}
        if self.id:
            params["username"] = self.id
            params["apikey"] = self.token
        else:
            params["apidomainkey"] = self.token
        return params

    def _is_success(self, code):
        # type: (object) -> bool
        try:
            code_int = int(code)  # type: ignore[arg-type]
            if code_int in (1, 200, 201):
                return True
        except (TypeError, ValueError):
            pass
        if isinstance(code, str):
            lower = code.lower()
            return lower in ("success", "ok", "true")
        return code is True

    def _hostname(self, subdomain, main_domain):
        # type: (str, str) -> str
        if subdomain in (None, "", "@"):
            return main_domain
        if subdomain.endswith("." + main_domain) or subdomain == main_domain:
            return subdomain
        return subdomain + "." + main_domain

    def _record_hostname(self, record, main_domain):
        # type: (dict, str) -> str
        # 官方返回字段为 hostname，以下别名用于兼容可能的字段命名差异
        host = (
            record.get("hostname")
            or record.get("host")
            or record.get("rrhost")
            or record.get("record")
            or record.get("name")
        )
        if host in (None, "", "@", main_domain):
            return main_domain
        if isinstance(host, str) and host.endswith("." + main_domain):
            return host
        return host + "." + main_domain

    def _request(self, action, domain, **params):
        # type: (str, str, **object) -> dict[str, object] | None
        payload = self._auth_params(domain)
        payload["act"] = action
        for key, value in params.items():
            if value is not None:
                payload[key] = value

        response = self._http("POST", "/API/v2/domain/dns/", body=payload)
        if isinstance(response, dict):
            code = response.get("code")
            if code is None:
                code = response.get("result") or response.get("status")
            if self._is_success(code):
                return response
            self.logger.warning(
                "West API %s failed: %s", action, response.get("msg") or response.get("message") or response
            )
        else:
            self.logger.error("Unexpected response for %s: %s", action, response)
        return None

    def _extract_records(self, response):
        # type: (dict | None) -> list[dict]
        if not response:
            return []
        for key in ("data", "list", "lists", "records"):
            # West.cn 文档使用 data 返回记录，其他键用于兼容示例或非标准响应
            records = response.get(key)  # type: ignore[index]
            if isinstance(records, list) and records:
                return records  # type: ignore[return-value]
        return []

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        resp = self._request("dnsrec.list", domain)
        if resp:
            return domain
        return None

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict[str, object] | None) -> dict | None
        hostname = self._hostname(subdomain, main_domain)
        resp = self._request("dnsrec.list", zone_id, hostname=hostname)
        records = self._extract_records(resp)
        for record in records:
            host = self._record_hostname(record, main_domain)
            if host == hostname and record.get("record_type") == record_type:
                if line is None or record.get("record_line") == line:
                    return record
        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int | str | None, str | None, dict[str, object] | None) -> bool
        hostname = self._hostname(subdomain, main_domain)
        params = {
            "hostname": hostname,
            "record_type": record_type,
            "record_value": value,
            "record_ttl": ttl,
            "record_line": line,
        }
        params.update(extra or {})
        resp = self._request("dnsrec.add", zone_id, **params)
        if resp:
            self.logger.info("Record created for %s", hostname)
            return True
        self.logger.error("Failed to create record for %s", hostname)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | str | None, str | None, dict[str, object] | None) -> bool
        hostname = self._record_hostname(old_record, zone_id)
        params = {
            "hostname": hostname,
            "record_type": record_type,
            "record_value": value,
            "record_ttl": ttl or old_record.get("record_ttl"),
            "record_line": line or old_record.get("record_line"),
            "record_id": old_record.get("id") or old_record.get("record_id"),
        }
        params.update(extra or {})
        resp = self._request("dnsrec.update", zone_id, **params)
        if resp:
            self.logger.info("Record updated for %s", hostname)
            return True
        self.logger.error("Failed to update record for %s", hostname)
        return False
