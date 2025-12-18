# coding=utf-8
"""
West.cn (西部数码) DNS Provider
@doc: https://www.west.cn/CustomerCenter/doc/domain_v2.html
@author: NewFuture
"""

from ._base import SimpleProvider, TYPE_FORM


class WestProvider(SimpleProvider):
    """
    West.cn (西部数码) DNS Provider
    西部数码域名解析接口

    支持两种认证方式:
    1. 域名级认证(推荐): domain + apidomainkey
    2. 用户级认证(代理商): username + apikey

    Supports two authentication methods:
    1. Domain-level auth (recommended): domain + apidomainkey
    2. User-level auth (reseller): username + apikey
    """

    endpoint = "https://api.west.cn/API/v2/domain/dns/"
    content_type = TYPE_FORM

    def _validate(self):
        # type: () -> None
        """
        验证配置是否有效

        Validate configuration.
        - Domain-level auth: id=domain, token=apidomainkey
        - User-level auth: id=username, token=apikey
        """
        if not self.id or not self.token:
            raise ValueError("id and token must be configured")

    def set_record(self, domain, value, record_type="A", ttl=None, line=None, **extra):
        # type: (str, str, str, int | str | None, str | None, **str) -> bool
        """
        更新DNS记录

        Update DNS record using West.cn API.
        West.cn只支持更新操作,不区分创建和更新
        West.cn only supports update operation, no distinction between create and update.

        Args:
            domain (str): 完整域名 (如 www.example.com)
            value (str): 记录值 (IP地址)
            record_type (str): 记录类型 (默认为A)
            ttl (int|str|None): TTL值 (West.cn不支持通过DDNS API设置TTL)
            line (str|None): 线路 (West.cn不支持通过DDNS API设置线路)
            **extra: 额外参数

        Returns:
            bool: 成功返回True, 失败返回False
        """
        if record_type != "A" and record_type != "AAAA":
            self.logger.warning("West.cn DDNS API only supports A and AAAA records, got: %s", record_type)
            return False

        # 拆分域名为主域名和完整域名
        # Split domain into main domain and full hostname
        parts = domain.split(".")
        if len(parts) < 2:
            self.logger.error("Invalid domain format: %s", domain)
            return False

        # 尝试提取主域名 (最后两部分)
        # Try to extract main domain (last two parts)
        main_domain = ".".join(parts[-2:])

        # 构建请求参数
        # Build request parameters
        params = {
            "act": "dnsrec.update",
            "hostname": domain,  # 完整域名/Full hostname
            "record_value": value,  # IP地址/IP address
        }

        # 判断认证方式
        # Determine authentication method
        if "@" in self.id or len(self.id.split(".")) > 1:
            # 域名级认证: id是域名, token是apidomainkey
            # Domain-level auth: id is domain, token is apidomainkey
            params["domain"] = main_domain
            params["apidomainkey"] = self.token
            self.logger.debug("Using domain-level authentication for: %s", main_domain)
        else:
            # 用户级认证: id是username, token是apikey
            # User-level auth: id is username, token is apikey
            params["username"] = self.id
            params["apikey"] = self.token
            params["domain"] = main_domain
            self.logger.debug("Using user-level authentication for: %s", self.id)

        # 发送请求
        # Send request
        self.logger.info("Updating DNS record: %s => %s", domain, value)

        # West.cn API使用GB2312/GBK编码
        # West.cn API uses GB2312/GBK encoding
        # 需要在请求时处理编码转换
        # Need to handle encoding conversion in request
        response = self._http("GET", "", params=params)

        # West.cn API返回格式示例:
        # 成功: {"result":200,"msg":"成功"}
        # 失败: {"result":其他值,"msg":"错误信息"}
        # Response format example:
        # Success: {"result":200,"msg":"Success"}
        # Failure: {"result":other,"msg":"Error message"}

        if response:
            result_code = response.get("result")
            msg = response.get("msg", "Unknown error")

            if result_code == 200:
                self.logger.info("DNS record updated successfully: %s", msg)
                return True
            else:
                self.logger.error("Failed to update DNS record: [%s] %s", result_code, msg)
                return False
        else:
            self.logger.error("Empty response from West.cn API")
            return False
