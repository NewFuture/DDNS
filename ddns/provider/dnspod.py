# coding=utf-8
"""
DNSPOD API
@doc: https://docs.dnspod.cn/api/
@author: New Future
"""

import logging
from ._base import BaseProvider, TYPE_FORM


class DnspodProvider(BaseProvider):
    """
    DNSPOD API
    DNSPOD 接口解析操作库
    """
    API = "dnsapi.cn"
    ContentType = TYPE_FORM

    def _request(self, action, **params):
        # type: (str, **(str | int | bytes | bool | None)) -> dict
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
        # if param:
        #     params.update(param)
        # 过滤掉None参数
        params = {k: v for k, v in params.items() if v is not None}
        params.update({
            "login_token": "{0},{1}".format(self.auth_id, self.auth_token),
            "format": "json",
            "length": "3000"
        })

        headers = {
            "User-Agent": "DDNS/{0} (ddns@newfuture.cc)".format(self.Version)
        }
        return self._https("POST", "/{0}".format(action), headers, **params)

    def _create_record(self, zone_id, sub, value, record_type, ttl=None, line=None, extra=None):
        # type: (str, str, str, str, int | str | None, str | None, dict | None) -> bool
        params = {
            "domain_id": zone_id,
            "sub_domain": sub,
            "value": value,
            "record_type": record_type,
            "record_line": line or "默认",
        }
        if ttl:
            params["ttl"] = ttl  # type: ignore[assignment]
        if extra:
            params.update(extra)
        res = self._request("Record.Create", **params)
        record = res.get("record")
        if record:
            # 记录创建成功
            logging.info("Record created: %s", record)
            return True
        else:
            # 记录创建失败
            logging.error("Failed to create record: %s", res)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl=None, line=None, extra=None):
        # type: (str, dict, str, str, int | str | None, str | None, dict | None) -> bool
        params = {
            "domain_id": zone_id,
            "record_id": old_record.get("id"),
            "value": value,
            "sub_domain": old_record.get("name"),
            "record_type": record_type,
        }
        if ttl:
            params["ttl"] = ttl
        if extra:
            params.update(extra)
        record_line = (line or old_record.get("line") or "默认").replace("Default", "default").encode("utf-8")
        res = self._request("Record.Modify", record_line=record_line, **params)
        return res.get("record") is not None

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        res = self._request("Domain.Info", domain=domain)
        return res.get("domain", {}).get("id")

    def _query_record(self, zone_id, sub, record_type, line=None):
        # type: (str, str, str, str | None) -> dict | None
        params = {
            "domain_id": zone_id
        }
        res = self._request("Record.List", **params)
        records = res.get("records", [])
        for record in records:
            if record.get("name") == sub and record.get("type") == record_type:
                record_line = record.get("line", "")
                if line is None or record_line == line or record_line == "默认":
                    return record
        return None
