# coding=utf-8
"""
CloudFlare API
@author: TongYifan, NewFuture
"""

import logging
from ._base import BaseProvider, TYPE_JSON


class CloudflareProvider(BaseProvider):
    API = "api.cloudflare.com"
    ContentType = TYPE_JSON

    def _request(self, method, action, **params):
        """
        发送请求数据
        """
        headers = {}
        if self.auth_id:
            headers["X-Auth-Email"] = self.auth_id
            headers["X-Auth-Key"] = self.auth_token
        else:
            headers["Authorization"] = "Bearer " + self.auth_token

        params = {k: v for k, v in params.items() if v is not None}  # 过滤掉None参数
        data = self._https(method, "/client/v4/zones" + action, headers=headers, params=params)
        if data and data.get("success"):
            return data.get("result")  # 返回结果或原始数据
        else:
            logging.warning("Cloudflare API error: %s", data.get("errors", "Unknown error"))
        return data

    def _query_zone_id(self, domain):
        """
        https://developers.cloudflare.com/api/resources/zones/methods/list/
        """
        params = {"name.exact": domain, "per_page": 50}
        zones = self._request("GET", "", **params)
        zone = next((z for z in zones if domain == z.get("name", "")), None)
        logging.debug("Queried zone: %s", zone)
        if zone:
            return zone["id"]
        return None

    def _query_record(self, zone_id, sub_domain, main_domain, record_type, line=None, extra={}):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """
        https://developers.cloudflare.com/api/resources/dns/subresources/records/methods/list/
        """
        # cloudflare的域名查询需要完整域名
        name = sub_domain + "." + main_domain
        if "." not in main_domain:
            name = sub_domain  # 如果没有主域名，直接使用子域名
        query = {"name.exact": name}
        data = self._request(
            "GET",
            "/{}/dns_records".format(zone_id),
            **query,
            type=record_type,
            proxied=extra.pop("proxied", None),
            per_page=500000
        )
        record = next((r for r in data if r.get("name") == name and r.get("type") == record_type), None)
        logging.debug("Record queried: %s", record)
        if record:
            return record
        logging.warning("Failed to query record: %s", data)
        return None

    def _create_record(self, zone_id, sub_domain, main_domain, value, record_type, ttl=None, line=None, extra={}):
        # type: (str, str, str, str, str, int | str | None, str | None, dict) -> bool
        """
        https://developers.cloudflare.com/api/resources/dns/subresources/records/methods/create/
        """
        domain = sub_domain + "." + main_domain
        extra["comment"] = extra.get("comment", self.Remark)  # 添加注释
        data = self._request(
            "POST", "/{}/dns_records".format(zone_id), name=domain, type=record_type, content=value, ttl=ttl, **extra
        )
        if data:
            logging.info("Record created: %s", data)
            return True
        logging.error("Failed to create record: %s", data)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl=None, line=None, extra={}):
        # type: (str, dict, str, str, int | str | None, str | None, dict) -> bool
        """
        https://developers.cloudflare.com/api/resources/dns/subresources/records/methods/edit/
        """
        extra["comment"] = old_record.get("comment", extra.get("comment", self.Remark))  # 注释
        extra["proxied"] = old_record.get("proxied", extra.get("proxied"))  # 保持原有的代理状态
        extra["tags"] = old_record.get("tags", extra.get("tags"))  # 保持原有的标签
        extra["settings"] = old_record.get("settings", extra.get("settings"))  # 保持原有的设置
        data = self._request(
            "PUT",
            "/{}/dns_records/{}".format(zone_id, old_record["id"]),
            type=record_type,
            name=old_record.get("name"),
            content=value,
            ttl=ttl,
            **extra
        )
        logging.debug("Record updated: %s", data)
        if data:
            return True
        return False
