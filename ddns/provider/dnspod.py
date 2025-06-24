# coding=utf-8
"""
DNSPOD API
@doc: https://docs.dnspod.cn/api/
@author: NewFuture
"""

from ._base import BaseProvider, TYPE_FORM


class DnspodProvider(BaseProvider):
    """
    DNSPOD API
    DNSPOD 接口解析操作库
    """

    API = "https://dnsapi.cn"
    ContentType = TYPE_FORM
    DefaultLine = "默认"

    def _request(self, action, extra=None, **params):
        # type: (str, dict | None, **(str | int | bytes | bool | None)) -> dict
        """
        发送请求数据

        Send request to DNSPod API.

        Args:
            action (str): API 动作/Action
            param (dict|None): 额外参数/Extra params
            params (dict): 其它参数/Other params
        Returns:
            dict: 响应数据/Response data
        """
        # 过滤掉None参数
        if extra:
            params.update(extra)
        params = {k: v for k, v in params.items() if v is not None}
        params.update(
            {"login_token": "{0},{1}".format(self.auth_id, self.auth_token), "format": "json", "length": "3000"}
        )

        headers = {"User-Agent": "DDNS/{0} (ddns@newfuture.cc)".format(self.Version)}
        data = self._http("POST", "/" + action, headers=headers, body=params)
        if data and data.get("status", {}).get("code") == "1":
            # 请求成功
            return data
        else:
            # 请求失败
            self.logger.warning("DNSPod API error: %s, ", data.get("status", {}).get("message", "Unknown error"))
            return data

    def _create_record(self, zone_id, sub_domain, main_domain, value, record_type, ttl=None, line=None, extra=None):
        # type: (str, str, str, str, str, int | str | None, str | None, dict | None) -> bool
        res = self._request(
            "Record.Create",
            extra=extra,
            domain_id=zone_id,
            sub_domain=sub_domain,
            value=value,
            record_type=record_type,
            record_line=line or self.DefaultLine,
            ttl=ttl,
        )
        record = res and res.get("record")
        if record:
            # 记录创建成功
            self.logger.info("Record created: %s", record)
            return True
        else:
            # 记录创建失败
            self.logger.error("Failed to create record: %s", res)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl=None, line=None, extra=None):
        # type: (str, dict, str, str, int | str | None, str | None, dict | None) -> bool
        record_line = (
            (line or old_record.get("line") or self.DefaultLine).replace("Default", "default").encode("utf-8")
        )
        res = self._request(
            "Record.Modify",
            domain_id=zone_id,
            record_id=old_record.get("id"),
            value=value,
            sub_domain=old_record.get("name"),
            record_line=record_line,
            extra=extra,
        )
        record = res and res.get("record")
        if record:
            # 记录更新成功
            self.logger.debug("Record updated: %s", record)
            return True
        else:
            # 记录更新失败
            self.logger.error("Failed to update record: %s", res)
            return False

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        res = self._request("Domain.Info", domain=domain)
        return res.get("domain", {}).get("id")

    def _query_record(self, zone_id, sub_domain, main_domain, record_type, line=None, extra=None):
        # type: (str, str, str, str, str | None, dict | None) -> dict | None
        """
        查询记录 list 然后逐个查找
        """

        res = self._request("Record.List", domain_id=zone_id)
        records = res.get("records", [])
        for record in records:
            if record.get("name") == sub_domain and record.get("type") == record_type:
                record_line = record.get("line", "")
                if line is None or record_line == line or record_line == "默认":
                    return record
        self.logger.warning(
            "No record found for [%s] with sub %s + type %s (line: %s)", zone_id, sub_domain, record_type, line
        )
        return None
