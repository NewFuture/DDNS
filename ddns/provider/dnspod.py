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

    endpoint = "https://dnsapi.cn"
    content_type = TYPE_FORM

    DefaultLine = "默认"

    def _request(self, action, extra=None, **params):
        # type: (str, dict | None, **(str | int | bytes | bool | None)) -> dict
        """
        发送请求数据

        Send request to DNSPod API.
        Args:
            action (str): API 动作/Action
            extra (dict|None): 额外参数/Extra params
            params (dict): 其它参数/Other params
        Returns:
            dict: 响应数据/Response data
        """
        # 过滤掉None参数
        if extra:
            params.update(extra)
        params = {k: v for k, v in params.items() if v is not None}
        params.update({"login_token": "{0},{1}".format(self.id, self.token), "format": "json"})
        data = self._http("POST", "/" + action, body=params)
        if data and data.get("status", {}).get("code") == "1":  # 请求成功
            return data
        else:  # 请求失败
            error_msg = "Unknown error"
            if data and isinstance(data, dict):
                error_msg = data.get("status", {}).get("message", "Unknown error")
            self.logger.warning("DNSPod API error: %s", error_msg)
            return data

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int | str | None, str | None, dict) -> bool
        """https://docs.dnspod.cn/api/add-record/"""
        res = self._request(
            "Record.Create",
            extra=extra,
            domain_id=zone_id,
            sub_domain=subdomain,
            value=value,
            record_type=record_type,
            record_line=line or self.DefaultLine,
            ttl=ttl,
        )
        record = res and res.get("record")
        if record:  # 记录创建成功
            self.logger.info("Record created: %s", record)
            return True
        else:  # 记录创建失败
            self.logger.error("Failed to create record: %s", res)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | str | None, str | None, dict) -> bool
        """https://docs.dnspod.cn/api/modify-records/"""
        record_line = (line or old_record.get("line") or self.DefaultLine).replace("Default", "default")
        res = self._request(
            "Record.Modify",
            domain_id=zone_id,
            record_id=old_record.get("id"),
            sub_domain=old_record.get("name"),
            record_type=record_type,
            value=value,
            record_line=record_line,
            extra=extra,
        )
        record = res and res.get("record")
        if record:  # 记录更新成功
            self.logger.debug("Record updated: %s", record)
            return True
        else:  # 记录更新失败
            self.logger.error("Failed to update record: %s", res)
            return False

    def _query_zone_id(self, domain):
        # type: (str) -> str | None
        """查询域名信息 https://docs.dnspod.cn/api/domain-info/"""
        res = self._request("Domain.Info", domain=domain)
        if res and isinstance(res, dict):
            return res.get("domain", {}).get("id")
        return None

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """查询记录 list 然后逐个查找 https://docs.dnspod.cn/api/record-list/"""
        res = self._request("Record.List", domain_id=zone_id, sub_domain=subdomain, record_type=record_type, line=line)
        # length="3000"
        records = res.get("records", [])
        n = len(records)
        if not n:
            self.logger.warning("No record found for [%s] %s<%s>(line: %s)", zone_id, subdomain, record_type, line)
            return None
        if n > 1:
            self.logger.warning("%d records found for %s<%s>(%s):\n %s", n, subdomain, record_type, line, records)
            return next((r for r in records if r.get("name") == subdomain), None)
        return records[0]
