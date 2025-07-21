# coding=utf-8
"""
Hurricane Electric (he.net) API
@author: NN708, NewFuture
"""

from ._base import SimpleProvider, TYPE_FORM


class HeProvider(SimpleProvider):
    endpoint = "https://dyn.dns.he.net"
    content_type = TYPE_FORM
    accept = None  # he.net does not require a specific Accept header
    decode_response = False  # he.net response is plain text, not JSON

    def _validate(self):
        self.logger.warning(
            "HE.net 缺少充分的真实环境测试，请及时在 GitHub Issues 中反馈: %s",
            "https://github.com/NewFuture/DDNS/issues",
        )
        if self.id:
            raise ValueError("Hurricane Electric (he.net) does not use `id`, use `token(password)` only.")
        if not self.token:
            raise ValueError("Hurricane Electric (he.net) requires `token(password)`.")

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        """
        使用 POST API 更新或创建 DNS 记录。Update or create DNS record with POST API.
        https://dns.he.net/docs.html
        """
        self.logger.info("%s => %s(%s)", domain, value, record_type)
        params = {
            "hostname": domain,  # he.net requires full domain name
            "myip": value,  # IP address to update
            "password": self.token,  # Use token as password
        }
        try:
            res = self._http("POST", "/nic/update", body=params)
            if res and res[:5] == "nochg" or res[:4] == "good":  # No change or success
                self.logger.info("HE API response: %s", res)
                return True
            else:
                self.logger.error("HE API error: %s", res)
        except Exception as e:
            self.logger.error("Error updating record for %s: %s", domain, e)
        return False
