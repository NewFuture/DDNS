# coding=utf-8
"""
HMAC-SHA256 Authorization 函数单元测试

针对 ddns.provider._signature.hmac_sha256_authorization 函数的完整测试套件。
测试覆盖多种典型使用场景，包括各大云服务商的认证模式，
所有期望结果都是预先计算好的，确保测试结果的可复现性。

Test suite for ddns.provider._signature.hmac_sha256_authorization function.
Covers various typical use cases including authentication patterns of major cloud providers.
All expected results are pre-calculated to ensure reproducible test results.
"""

from __init__ import unittest
from ddns.provider._signature import hmac_sha256_authorization, sha256_hash, hmac_sha256


class TestHmacSha256Authorization(unittest.TestCase):
    """HMAC-SHA256 Authorization 函数测试类"""

    def test_basic_functionality(self):
        """测试基本功能 - 简单的签名生成"""
        secret_key = "test_secret_key"
        method = "GET"
        path = "/api/test"
        query = ""
        headers = {"Host": "api.example.com", "Date": "20231201T120000Z"}
        body_hash = sha256_hash("")  # 空请求体的哈希

        auth_header_template = "TEST {SignedHeaders} {Signature}"
        signing_string_template = "TEST\n{HashedCanonicalRequest}"

        result = hmac_sha256_authorization(
            secret_key=secret_key,
            method=method,
            path=path,
            query=query,
            headers=headers,
            body_hash=body_hash,
            authorization_format=auth_header_template,
            signing_string_format=signing_string_template,
        )

        # 严格验证基本功能测试的完整结果 - 精确匹配
        expected_result = "TEST date;host b5b3ee3c39b1c749faa31c1b5bd3a5609a3e5408dfb7f90eca5ea17d8aeb1ba2"
        self.assertEqual(result, expected_result)

    def test_alibaba_cloud_official_example(self):
        """测试阿里云官方文档示例 - ACS3-HMAC-SHA256签名算法"""
        # 使用阿里云官方文档中的固定参数示例
        # 来源: https://help.aliyun.com/zh/sdk/product-overview/v3-request-structure-and-signature
        secret_key = "YourAccessKeySecret"
        method = "POST"
        path = "/"
        query = "ImageId=win2019_1809_x64_dtc_zh-cn_40G_alibase_20230811.vhd&RegionId=cn-shanghai"
        headers = {
            "host": "ecs.cn-shanghai.aliyuncs.com",
            "x-acs-action": "RunInstances",
            "x-acs-content-sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "x-acs-date": "2023-10-26T10:22:32Z",
            "x-acs-signature-nonce": "3156853299f313e23d1673dc12e1703d",
            "x-acs-version": "2014-05-26",
        }
        body_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        auth_header_template = (
            "ACS3-HMAC-SHA256 Credential=YourAccessKeyId,SignedHeaders={SignedHeaders},Signature={Signature}"
        )
        signing_string_template = "ACS3-HMAC-SHA256\n{HashedCanonicalRequest}"

        result = hmac_sha256_authorization(
            secret_key=secret_key,
            method=method,
            path=path,
            query=query,
            headers=headers,
            body_hash=body_hash,
            authorization_format=auth_header_template,
            signing_string_format=signing_string_template,
        )

        # 严格验证阿里云官方示例的完整授权头 - 精确匹配
        expected_result = (
            "ACS3-HMAC-SHA256 Credential=YourAccessKeyId,"
            "SignedHeaders=host;x-acs-action;x-acs-content-sha256;x-acs-date;x-acs-signature-nonce;x-acs-version,"
            "Signature=06563a9e1b43f5dfe96b81484da74bceab24a1d853912eee15083a6f0f3283c0"
        )
        self.assertEqual(result, expected_result)

    def test_huawei_cloud_official_example(self):
        """测试华为云官方文档示例 - SDK-HMAC-SHA256签名算法"""
        # 使用华为云官方文档中的查询VPC列表示例
        # 来源: https://support.huaweicloud.com/devg-apisign/api-sign-algorithm-002.html
        secret_key = "your_secret_access_key"
        method = "GET"
        path = "/v1/77b6a44cba5143ab91d13ab9a8ff44fd/vpcs/"  # 注意官方示例要求以/结尾
        query = "limit=2&marker=13551d6b-755d-4757-b956-536f674975c0"
        headers = {
            "content-type": "application/json",
            "host": "service.region.example.com",
            "x-sdk-date": "20191115T033655Z",
        }
        body_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        auth_header_template = (
            "SDK-HMAC-SHA256 Access=your_access_key_id, SignedHeaders={SignedHeaders}, Signature={Signature}"
        )
        signing_string_template = "SDK-HMAC-SHA256\n20191115T033655Z\n{HashedCanonicalRequest}"

        result = hmac_sha256_authorization(
            secret_key=secret_key,
            method=method,
            path=path,
            query=query,
            headers=headers,
            body_hash=body_hash,
            authorization_format=auth_header_template,
            signing_string_format=signing_string_template,
        )

        # 严格验证华为云官方示例的完整授权头 - 精确匹配
        expected_result = (
            "SDK-HMAC-SHA256 Access=your_access_key_id, "
            "SignedHeaders=content-type;host;x-sdk-date, "
            "Signature=8037a231336d8904f667c082dd84fc06d7e6c7c278c2d8599db31d14e8ee19f9"
        )
        self.assertEqual(result, expected_result)

    def test_tencent_cloud_official_example(self):
        """测试腾讯云官方文档示例 - TC3-HMAC-SHA256签名算法"""
        # 使用腾讯云官方文档中的固定参数示例
        # 来源: https://cloud.tencent.com/document/api/213/30654
        # 注意：腾讯云使用派生密钥，这里模拟最终的签名密钥
        # Python 2/3 compatible hex to bytes conversion
        hex_string = "b596b923aad85185e2d1f6659d2a062e0a86731226e021e61bfe06f7ed05f5af"
        try:
            final_signing_key = bytes.fromhex(hex_string)
        except AttributeError:  # Python 2.7
            final_signing_key = hex_string.decode("hex")  # type: ignore[attr-defined]
        method = "POST"
        path = "/"
        query = ""  # POST请求，查询字符串为空
        headers = {
            "content-type": "application/json; charset=utf-8",
            "host": "cvm.tencentcloudapi.com",
            "x-tc-action": "describeinstances",
        }
        # 官方示例中的请求体
        # body = '{"Limit": 1, "Filters": [{"Values": ["\\u672a\\u547d\\u540d"], "Name": "instance-name"}]}'
        body_hash = "35e9c5b0e3ae67532d3c9f17ead6c90222632e5b1ff7f6e89887f1398934f064"

        auth_header_template = (
            "TC3-HMAC-SHA256 Credential=AKID********************************/2019-02-25/cvm/tc3_request, "
            "SignedHeaders={SignedHeaders}, Signature={Signature}"
        )
        signing_string_template = "TC3-HMAC-SHA256\n1551113065\n2019-02-25/cvm/tc3_request\n{HashedCanonicalRequest}"

        result = hmac_sha256_authorization(
            secret_key=final_signing_key,
            method=method,
            path=path,
            query=query,
            headers=headers,
            body_hash=body_hash,
            authorization_format=auth_header_template,
            signing_string_format=signing_string_template,
        )

        # 严格验证腾讯云官方示例的完整授权头 - 精确匹配
        expected_result = (
            "TC3-HMAC-SHA256 Credential=AKID********************************/2019-02-25/cvm/tc3_request, "
            "SignedHeaders=content-type;host;x-tc-action, "
            "Signature=10b1a37a7301a02ca19a647ad722d5e43b4b3cff309d421d85b46093f6ab6c4f"
        )
        self.assertEqual(result, expected_result)

    def test_edge_cases(self):
        """测试边界情况"""

        # 测试空字符串参数 - 严格验证
        result1 = hmac_sha256_authorization(
            secret_key="key",
            method="GET",
            path="",
            query="",
            headers={},
            body_hash=sha256_hash(""),
            authorization_format="AUTH {Signature}",
            signing_string_format="{HashedCanonicalRequest}",
        )
        expected_result1 = "AUTH 1d29fda5ce641f10c7e16b1e607ce10f1cad4fd4b071f1b3a4465e051b9a7d6d"
        self.assertEqual(result1, expected_result1)

        # 测试包含特殊字符的参数 - 严格验证
        result2 = hmac_sha256_authorization(
            secret_key="special!@#$%^&*()key",
            method="POST",
            path="/path/with spaces",
            query="param1=value with spaces&param2=value%20encoded",
            headers={"Custom-Header": "value with spaces and symbols!@#"},
            body_hash=sha256_hash("body with 中文 and symbols"),
            authorization_format="SPECIAL {SignedHeaders} {Signature}",
            signing_string_format="SPECIAL\n{HashedCanonicalRequest}",
        )
        expected_result2 = "SPECIAL custom-header edbf4d68ebb33f305e8d0e2f72c012997543a0bdc6a9f42142d1dfa236fa1dd5"
        self.assertEqual(result2, expected_result2)

    def test_header_normalization(self):
        """测试头部规范化处理"""
        secret_key = "test_key"
        method = "GET"
        path = "/test"
        query = ""
        body_hash = sha256_hash("")

        # 测试头部大小写混合和值的前后空格处理
        headers = {
            "Host": "  example.com  ",  # 前后有空格
            "X-Custom-Header": "value",
            "x-another-header": "another_value",
            "CONTENT-TYPE": "application/json",
        }

        auth_header_template = "TEST {SignedHeaders} {Signature}"
        signing_string_template = "{HashedCanonicalRequest}"

        result = hmac_sha256_authorization(
            secret_key=secret_key,
            method=method,
            path=path,
            query=query,
            headers=headers,
            body_hash=body_hash,
            authorization_format=auth_header_template,
            signing_string_format=signing_string_template,
        )

        # 验证头部已被正确规范化（小写且按字母顺序排列）
        # 模板格式是 "TEST {SignedHeaders} {Signature}"，所以直接检查signed headers部分
        self.assertIn("content-type;host;x-another-header;x-custom-header", result)

    def test_reproducible_signatures(self):
        """测试签名结果的可复现性"""
        params = {
            "secret_key": "reproducible_test_key",
            "method": "POST",
            "path": "/api/v1/test",
            "query": "param1=value1&param2=value2",
            "headers": {"Host": "api.test.com", "Content-Type": "application/json", "Date": "20231201T120000Z"},
            "body_hash": sha256_hash('{"test": "data"}'),
            "authorization_format": "REPRO {SignedHeaders} {Signature}",
            "signing_string_format": "REPRO\n{HashedCanonicalRequest}",
        }

        # 多次调用应该产生相同的结果
        result1 = hmac_sha256_authorization(**params)
        result2 = hmac_sha256_authorization(**params)
        result3 = hmac_sha256_authorization(**params)

        self.assertEqual(result1, result2)
        self.assertEqual(result2, result3)

        # 验证结果包含预期的组件
        self.assertIn("REPRO", result1)
        self.assertIn("content-type;date;host", result1)

        # 提取签名部分进行验证 - 格式是 "REPRO {SignedHeaders} {Signature}"
        parts = result1.split()
        self.assertEqual(len(parts), 3)  # "REPRO", signed_headers, signature
        signature_part = parts[2]
        self.assertEqual(len(signature_part), 64)  # SHA256签名应该是64个十六进制字符
        self.assertTrue(all(c in "0123456789abcdef" for c in signature_part))

    def test_different_key_types(self):
        """测试不同类型的密钥输入"""
        base_params = {
            "method": "GET",
            "path": "/test",
            "query": "",
            "headers": {"Host": "example.com"},
            "body_hash": sha256_hash(""),
            "authorization_format": "TYPE {Signature}",
            "signing_string_format": "{HashedCanonicalRequest}",
        }

        # 字符串密钥
        result_str = hmac_sha256_authorization(secret_key="string_key", **base_params)

        # 字节密钥
        result_bytes = hmac_sha256_authorization(secret_key=b"string_key", **base_params)

        # 相同内容的字符串和字节密钥应该产生相同的签名
        self.assertEqual(result_str, result_bytes)

    def test_hmac_sha256_basic_functionality(self):
        """测试 hmac_sha256 基础功能"""
        key = "test_key"
        message = "test_message"

        # 测试返回的是 HMAC 对象
        hmac_obj = hmac_sha256(key, message)

        # 验证可以调用 digest() 和 hexdigest() 方法
        digest_result = hmac_obj.digest()
        hexdigest_result = hmac_obj.hexdigest()

        # 验证结果类型
        self.assertIsInstance(digest_result, bytes)
        self.assertIsInstance(hexdigest_result, str)

        # 验证 hexdigest 结果长度 (SHA256 产生64个十六进制字符)
        self.assertEqual(len(hexdigest_result), 64)

        # 验证结果的可复现性
        hmac_obj2 = hmac_sha256(key, message)
        self.assertEqual(hmac_obj.hexdigest(), hmac_obj2.hexdigest())

    def test_hmac_sha256_different_key_types(self):
        """测试 hmac_sha256 不同密钥类型"""
        message = "test_message"

        # 字符串密钥
        hmac_str = hmac_sha256("test_key", message)

        # 字节密钥
        hmac_bytes = hmac_sha256(b"test_key", message)

        # 相同内容的字符串和字节密钥应该产生相同的结果
        self.assertEqual(hmac_str.hexdigest(), hmac_bytes.hexdigest())

    def test_hmac_sha256_different_message_types(self):
        """测试 hmac_sha256 不同消息类型"""
        key = "test_key"

        # 字符串消息
        hmac_str = hmac_sha256(key, "test_message")

        # 字节消息
        hmac_bytes = hmac_sha256(key, b"test_message")

        # 相同内容的字符串和字节消息应该产生相同的结果
        self.assertEqual(hmac_str.hexdigest(), hmac_bytes.hexdigest())

    def test_hmac_sha256_known_vector(self):
        """测试 hmac_sha256 已知测试向量"""
        # 使用已知的测试向量验证实现正确性
        key = "key"
        message = "The quick brown fox jumps over the lazy dog"

        hmac_obj = hmac_sha256(key, message)
        result = hmac_obj.hexdigest()

        # 预期结果(可以通过其他实现验证)
        expected = "f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8"
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
