# coding=utf-8
"""
HuaweiDNS API
华为DNS解析操作库
@author: NewFuture
"""

from time import gmtime, strftime

from ._base import TYPE_JSON, BaseProvider, encode_params, join_domain
from ._signature import hmac_sha256_authorization, sha256_hash


class HuaweiDNSProvider(BaseProvider):
    endpoint = "https://dns.myhuaweicloud.com"
    content_type = TYPE_JSON
    algorithm = "SDK-HMAC-SHA256"

    def _validate(self):
        self.logger.warning(
            "华为云 DNS 缺少充分的真实环境测试，请及时在 GitHub Issues 中反馈: %s",
            "https://github.com/NewFuture/DDNS/issues",
        )
        super(HuaweiDNSProvider, self)._validate()

    def _request(self, method, path, **params):
        """
        https://support.huaweicloud.com/api-dns/zh-cn_topic_0037134406.html
        https://support.huaweicloud.com/devg-apisign/api-sign-algorithm-002.html
        https://support.huaweicloud.com/devg-apisign/api-sign-algorithm-003.html
        https://support.huaweicloud.com/devg-apisign/api-sign-algorithm-004.html
        """
        # type: (str, str, **Any) -> dict
        params = {k: v for k, v in params.items() if v is not None}
        if method.upper() == "GET" or method.upper() == "DELETE":
            query = encode_params(params)
            body = ""
        else:
            query = ""
            body = self._encode_body(params)

        now = strftime("%Y%m%dT%H%M%SZ", gmtime())
        headers = {
            "content-type": self.content_type,
            "host": self.endpoint.split("://", 1)[1].strip("/"),
            "X-Sdk-Date": now,
        }

        # 使用通用签名函数
        body_hash = sha256_hash(body)
        # 华为云需要在签名时使用带尾斜杠的路径
        sign_path = path if path.endswith("/") else path + "/"
        authorization_format = "%s Access=%s, SignedHeaders={SignedHeaders}, Signature={Signature}" % (
            self.algorithm,
            self.id,
        )
        authorization = hmac_sha256_authorization(
            secret_key=self.token,
            method=method,
            path=sign_path,
            query=query,
            headers=headers,
            body_hash=body_hash,
            signing_string_format=self.algorithm + "\n" + now + "\n{HashedCanonicalRequest}",
            authorization_format=authorization_format,
        )
        headers["Authorization"] = authorization

        # 使用原始路径发送实际请求
        path = "{}?{}".format(path, query) if query else path
        data = self._http(method, path, headers=headers, body=body)
        return data

    def _query_zone_id(self, domain):
        """https://support.huaweicloud.com/api-dns/dns_api_62003.html"""
        domain = domain + "." if not domain.endswith(".") else domain
        data = self._request("GET", "/v2/zones", search_mode="equal", limit=500, name=domain)
        zones = data.get("zones", [])
        zone = next((z for z in zones if domain == z.get("name")), None)
        zoneid = zone and zone["id"]
        return zoneid

    def _query_record(self, zone_id, subdomain, main_domain, record_type, line, extra):
        """
        v2.1 https://support.huaweicloud.com/api-dns/dns_api_64004.html
        v2 https://support.huaweicloud.com/api-dns/ListRecordSetsByZone.html
        """
        domain = join_domain(subdomain, main_domain) + "."
        data = self._request(
            "GET",
            "/v2.1/zones/" + zone_id + "/recordsets",
            limit=500,
            name=domain,
            type=record_type,
            line_id=line,
            search_mode="equal",
        )
        records = data.get("recordsets", [])
        record = next((r for r in records if r.get("name") == domain and r.get("type") == record_type), None)
        return record

    def _create_record(self, zone_id, subdomain, main_domain, value, record_type, ttl, line, extra):
        """
        v2.1 https://support.huaweicloud.com/api-dns/dns_api_64001.html
        v2 https://support.huaweicloud.com/api-dns/CreateRecordSet.html
        """
        domain = join_domain(subdomain, main_domain) + "."
        extra["description"] = extra.get("description", self.remark)
        res = self._request(
            "POST",
            "/v2.1/zones/" + zone_id + "/recordsets",
            name=domain,
            type=record_type,
            records=[value],
            ttl=ttl,
            line=line,
            **extra
        )  # fmt: skip
        if res and res.get("id"):
            self.logger.info("Record created: %s", res)
            return True
        self.logger.warning("Failed to create record: %s", res)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        """https://support.huaweicloud.com/api-dns/UpdateRecordSets.html"""
        extra["description"] = extra.get("description", self.remark)
        # Note: The v2.1 update API does not support the line parameter in the request body
        # The line parameter is returned in the response but cannot be modified
        res = self._request(
            "PUT",
            "/v2.1/zones/" + zone_id + "/recordsets/" + old_record["id"],
            name=old_record["name"],
            type=record_type,
            records=[value],
            ttl=ttl if ttl is not None else old_record.get("ttl"),
            **extra
        )  # fmt: skip
        if res and res.get("id"):
            self.logger.info("Record updated: %s", res)
            return True
        self.logger.warning("Failed to update record: %s", res)
        return False
