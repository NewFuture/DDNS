# coding=utf-8
"""
CloudFlare API
@author: TongYifan, NewFuture
"""

from ._base import TYPE_JSON, BaseProvider, join_domain


class CloudflareProvider(BaseProvider):
    endpoint = "https://api.cloudflare.com"
    content_type = TYPE_JSON

    def _validate(self):
        if not self.token:
            raise ValueError("token must be configured")
        if self.id:
            # must be email for Cloudflare API v4
            if "@" not in self.id:
                self.logger.critical("ID 必须为空或有效的邮箱地址")
                raise ValueError("ID must be a valid email or Empty for Cloudflare API v4")

    def _request(self, method, action, **params):
        """发送请求数据"""
        headers = {}
        if self.id:
            headers["X-Auth-Email"] = self.id
            headers["X-Auth-Key"] = self.token
        else:
            headers["Authorization"] = "Bearer " + self.token

        params = {k: v for k, v in params.items() if v is not None}  # 过滤掉None参数
        data = self._http(method, "/client/v4/zones" + action, headers=headers, params=params)
        if data and data.get("success"):
            return data.get("result")  # 返回结果或原始数据
        else:
            self.logger.warning("Cloudflare API error: %s", data.get("errors", "Unknown error"))
        return data

    def _query_zone_id(self, domain):
        """https://developers.cloudflare.com/api/resources/zones/methods/list/"""
        params = {"name.exact": domain, "per_page": 50}
        zones = self._request("GET", "", **params)
        zone = next((z for z in zones if domain == z.get("name", "")), None)
        self.logger.debug("Queried zone: %s", zone)
        if zone:
            return zone["id"]
        return None

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        # type: (str, str, str, str, str | None, dict) -> dict | None
        """
        查询DNS记录，优先使用extra filter匹配，匹配不到则fallback到不带extra的结果

        Query DNS records, prioritize extra filters, fallback to query without extra if no match found.
        https://developers.cloudflare.com/api/resources/dns/subresources/records/methods/list/
        """
        # cloudflare的域名查询需要完整域名
        name = join_domain(subdomain, main_domain)
        query = {"name.exact": name}  # type: dict[str, str|None]

        # 添加extra filter到查询参数，将布尔值转换为小写字符串
        proxied = extra.get("proxied") if extra else None
        if proxied is not None:
            query["proxied"] = str(proxied).lower()  # True -> "true", False -> "false"

        # 先使用extra filter查询
        data = self._request("GET", "/{}/dns_records".format(zone_id), type=record_type, per_page=10000, **query)
        record = next((r for r in data if r.get("name") == name and r.get("type") == record_type), None)

        # 如果使用了extra filter但没找到记录，尝试不带extra filter查询
        if not record and proxied is not None:
            self.logger.debug("No record found with extra filters, retrying without extra filters")
            data = self._request(
                "GET", "/{}/dns_records".format(zone_id), type=record_type, per_page=10000, **{"name.exact": name}
            )
            record = next((r for r in data if r.get("name") == name and r.get("type") == record_type), None)

        self.logger.debug("Record queried: %s", record)
        if record:
            return record
        self.logger.warning("Failed to query record: %s", data)
        return None

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        # type: (str, str, str, str, str, int | str | None, str | None, dict ) -> bool
        """https://developers.cloudflare.com/api/resources/dns/subresources/records/methods/create/"""
        name = join_domain(subdomain, main_domain)
        extra["comment"] = extra.get("comment", self.remark)  # 添加注释
        data = self._request(
            "POST", "/{}/dns_records".format(zone_id), name=name, type=record_type, content=value, ttl=ttl, **extra
        )
        if data:
            self.logger.info("Record created: %s", data)
            return True
        self.logger.error("Failed to create record: %s", data)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        # type: (str, dict, str, str, int | str | None, str | None, dict) -> bool
        """https://developers.cloudflare.com/api/resources/dns/subresources/records/methods/edit/"""
        extra["comment"] = extra.get("comment", self.remark)  # 注释
        extra["proxied"] = extra.get("proxied", old_record.get("proxied"))  # extra优先，保持原有的代理状态作为默认值
        extra["tags"] = extra.get("tags", old_record.get("tags"))  # extra优先，保持原有的标签作为默认值
        extra["settings"] = extra.get("settings", old_record.get("settings"))  # extra优先，保持原有的设置作为默认值
        data = self._request(
            "PUT",
            "/{}/dns_records/{}".format(zone_id, old_record["id"]),
            type=record_type,
            name=old_record.get("name"),
            content=value,
            ttl=ttl,
            **extra
        )  # fmt: skip
        self.logger.debug("Record updated: %s", data)
        if data:
            return True
        return False
