# coding=utf-8
"""
HuaweiDNS API
华为DNS解析操作库
https://support.huaweicloud.com/api-dns/zh-cn_topic_0037134406.html
@author: cybmp3, NewFuture
"""

from ._base import BaseProvider, TYPE_JSON
from hashlib import sha256
from hmac import new as hmac
from json import dumps as jsonencode
from time import strftime, gmtime


class HuaweiDNSProvider(BaseProvider):
    API = "https://dns.myhuaweicloud.com"
    content_type = TYPE_JSON
    algorithm = "SDK-HMAC-SHA256"

    def _sign_headers(self, headers, signed_headers):
        a = []
        _headers = {}
        for key in headers:
            key_encoded = key.lower()
            value = headers[key]
            value_encoded = value.strip()
            _headers[key_encoded] = value_encoded
        for key in signed_headers:
            a.append(key + ":" + _headers[key])
        return "\n".join(a) + "\n"

    def _hex_encode_sha256(self, data):
        sha = sha256()
        sha.update(data)
        return sha.hexdigest()

    def _request(self, method, path, **params):
        # type: (str, str, **Any) -> dict
        params = {k: v for k, v in params.items() if v is not None}
        if method.upper() == "GET" or method.upper() == "DELETE":
            query = self._encode(sorted(params.items()))
            body = ""
        else:
            query = ""
            body = jsonencode(params)

        date_now = strftime("%Y%m%dT%H%M%SZ", gmtime())
        headers = {
            "content-type": self.content_type,
            "host": self.API.split("://", 1)[1].strip("/"),
            "X-Sdk-Date": date_now,
        }
        sign_headers = [k.lower() for k in headers]
        sign_headers.sort()

        hex_encode = self._hex_encode_sha256(body.encode("utf-8"))
        canonical_headers = self._sign_headers(headers, sign_headers)
        sign_path = path if path[-1] == "/" else path + "/"
        canonical_request = "%s\n%s\n%s\n%s\n%s\n%s" % (
            method.upper(),
            sign_path,
            query,
            canonical_headers,
            ";".join(sign_headers),
            hex_encode,
        )
        hashed_canonical_request = self._hex_encode_sha256(canonical_request.encode("utf-8"))

        str_to_sign = "%s\n%s\n%s" % (self.algorithm, date_now, hashed_canonical_request)
        secret = self.auth_token
        signature = hmac(secret.encode("utf-8"), str_to_sign.encode("utf-8"), digestmod=sha256).hexdigest()
        auth_header = "%s Access=%s, SignedHeaders=%s, Signature=%s" % (
            self.algorithm,
            self.auth_id,
            ";".join(sign_headers),
            signature,
        )
        headers["Authorization"] = auth_header
        self.logger.debug("Request headers: %s", headers)
        data = self._http(method, path + "?" + query, headers=headers, body=body)
        return data

    def _query_zone_id(self, domain):
        """https://support.huaweicloud.com/api-dns/dns_api_62003.html"""
        domain = domain + "." if not domain.endswith(".") else domain
        data = self._request("GET", "/v2/zones", search_mode="equal", limit=500, name=domain)
        zones = data.get("zones", [])
        zone = next((z for z in zones if domain == z.get("name")), None)
        zoneid = zone and zone["id"]
        return zoneid

    def _query_record(self, zone_id, sub_domain, main_domain, record_type, line, extra):
        """
        v2.1 https://support.huaweicloud.com/api-dns/dns_api_64004.html
        v2 https://support.huaweicloud.com/api-dns/ListRecordSetsByZone.html
        """
        domain = self._join_domain(sub_domain, main_domain) + "."
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

    def _create_record(self, zone_id, sub_domain, main_domain, value, record_type, ttl, line, extra):
        """
        v2.1 https://support.huaweicloud.com/api-dns/dns_api_64001.html
        v2 https://support.huaweicloud.com/api-dns/CreateRecordSet.html
        """
        domain = self._join_domain(sub_domain, main_domain) + "."
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
        )
        if res and res.get("id"):
            self.logger.info("Record created: %s", res)
            return True
        self.logger.warning("Failed to create record: %s", res)
        return False

    def _update_record(self, zone_id, old_record, value, record_type, ttl, line, extra):
        """https://support.huaweicloud.com/api-dns/UpdateRecordSet.html (无 line 参数)"""
        extra["description"] = extra.get("description", self.remark)
        res = self._request(
            "PUT",
            "/v2.1/zones/" + zone_id + "/recordsets/" + old_record["id"],
            name=old_record["name"],
            type=record_type,
            records=[value],
            ttl=ttl if ttl is not None else old_record.get("ttl"),
            **extra
        )
        if res and res.get("id"):
            self.logger.info("Record updated: %s", res)
            return True
        self.logger.warning("Failed to update record: %s", res)
        return False
