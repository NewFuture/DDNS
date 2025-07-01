# coding=utf-8
"""
测试 ddns.util.http 模块
Test ddns.util.http module
"""

from __future__ import unicode_literals
import unittest
import ssl
import sys
from base_test import MagicMock, patch
from ddns.util.http import (
    HTTPException,
    send_http_request,
    HttpResponse,
    _create_connection,
    _load_system_ca_certs,
    _close_connection,
    _build_redirect_url,
    _decode_response_body,
)

# Python 2/3 compatibility
if sys.version_info[0] == 2:  # python 2
    text_type = unicode  # noqa: F821
    binary_type = str
else:
    text_type = str
    binary_type = bytes


def to_bytes(s, encoding="utf-8"):
    if isinstance(s, text_type):
        return s.encode(encoding)
    return s


def to_unicode(s, encoding="utf-8"):
    if isinstance(s, binary_type):
        return s.decode(encoding)
    return s


def byte_string(s):
    if isinstance(s, text_type):
        return s.encode("utf-8")
    return s


class TestHttpResponse(unittest.TestCase):
    """测试 HttpResponse 类"""

    def test_init(self):
        """测试初始化HttpResponse对象"""
        headers = [("Content-Type", "application/json"), ("Content-Length", "100")]
        response = HttpResponse(200, "OK", headers, '{"test": true}')

        self.assertEqual(response.status, 200)
        self.assertEqual(response.reason, "OK")
        self.assertEqual(response.headers, headers)
        self.assertEqual(response.body, '{"test": true}')

    def test_get_header_case_insensitive(self):
        """测试get_header方法不区分大小写"""
        headers = [("Content-Type", "application/json"), ("Content-Length", "100")]
        response = HttpResponse(200, "OK", headers, "test")

        self.assertEqual(response.get_header("content-type"), "application/json")
        self.assertEqual(response.get_header("Content-Type"), "application/json")
        self.assertEqual(response.get_header("CONTENT-TYPE"), "application/json")
        self.assertEqual(response.get_header("content-length"), "100")

    def test_get_header_not_found(self):
        """测试get_header方法找不到头部时的默认值"""
        headers = [("Content-Type", "application/json")]
        response = HttpResponse(200, "OK", headers, "test")

        self.assertIsNone(response.get_header("Authorization"))
        self.assertEqual(response.get_header("Authorization", "default"), "default")

    def test_get_header_first_match(self):
        """测试get_header方法返回第一个匹配的头部"""
        headers = [("Set-Cookie", "session=abc"), ("Set-Cookie", "token=xyz")]
        response = HttpResponse(200, "OK", headers, "test")

        self.assertEqual(response.get_header("Set-Cookie"), "session=abc")


class TestCreateConnection(unittest.TestCase):
    """测试 _create_connection 函数"""

    @patch("ddns.util.http.HTTPConnection")
    def test_create_http_connection(self, mock_http_conn):
        """测试创建HTTP连接"""
        mock_conn = MagicMock()
        mock_http_conn.return_value = mock_conn

        result = _create_connection("example.com", 80, False, None, True)

        self.assertEqual(result, mock_conn)
        mock_http_conn.assert_called_once_with("example.com", 80)
        mock_conn.set_tunnel.assert_not_called()

    @patch("ddns.util.http.HTTPSConnection")
    def test_create_https_connection_default_ssl(self, mock_https_conn):
        """测试创建HTTPS连接 - 默认SSL验证"""
        mock_conn = MagicMock()
        mock_https_conn.return_value = mock_conn

        with patch("ddns.util.http._load_system_ca_certs") as mock_load_ca:
            result = _create_connection("example.com", 443, True, None, True)

        self.assertEqual(result, mock_conn)
        mock_https_conn.assert_called_once()
        mock_load_ca.assert_called_once()

    @patch("ddns.util.http.HTTPSConnection")
    @patch("ddns.util.http.ssl.create_default_context")
    def test_create_https_connection_no_ssl_verify(self, mock_ssl_context, mock_https_conn):
        """测试创建HTTPS连接 - 禁用SSL验证"""
        mock_context = MagicMock()
        mock_ssl_context.return_value = mock_context
        mock_conn = MagicMock()
        mock_https_conn.return_value = mock_conn

        result = _create_connection("example.com", 443, True, None, False)

        self.assertEqual(result, mock_conn)
        mock_ssl_context.assert_called_once()
        self.assertFalse(mock_context.check_hostname)
        self.assertEqual(mock_context.verify_mode, ssl.CERT_NONE)

    @patch("ddns.util.http.HTTPConnection")
    def test_create_connection_with_proxy(self, mock_http_conn):
        """测试创建带代理的连接"""
        mock_conn = MagicMock()
        mock_http_conn.return_value = mock_conn

        result = _create_connection("example.com", 80, False, "proxy.example.com:8080", True)

        self.assertEqual(result, mock_conn)
        mock_http_conn.assert_called_once_with("proxy.example.com:8080", 80)
        mock_conn.set_tunnel.assert_called_once_with("example.com", 80)

    @patch("ddns.util.http.HTTPSConnection")
    @patch("ddns.util.http.ssl.create_default_context")
    def test_create_https_connection_custom_ca_success(self, mock_ssl_context, mock_https_conn):
        """测试创建HTTPS连接 - 自定义CA证书成功"""
        mock_context = MagicMock()
        mock_ssl_context.return_value = mock_context
        mock_conn = MagicMock()
        mock_https_conn.return_value = mock_conn

        result = _create_connection("example.com", 443, True, None, "/path/to/ca.pem")

        self.assertEqual(result, mock_conn)
        mock_context.load_verify_locations.assert_called_once_with("/path/to/ca.pem")

    @patch("ddns.util.http.HTTPSConnection")
    @patch("ddns.util.http.logger")
    def test_create_https_connection_custom_ca_failure(self, mock_logger, mock_https_conn):
        """测试创建HTTPS连接 - 自定义CA证书失败"""
        mock_conn = MagicMock()
        mock_https_conn.return_value = mock_conn

        result = _create_connection("example.com", 443, True, None, "/nonexistent/ca.pem")

        self.assertEqual(result, mock_conn)
        mock_logger.error.assert_called_once()


class TestLoadSystemCaCerts(unittest.TestCase):
    """测试 _load_system_ca_certs 函数"""

    @patch("ddns.util.http.os.path.isfile")
    def test_load_ca_certs_success(self, mock_isfile):
        """测试成功加载CA证书"""
        mock_context = MagicMock()
        mock_isfile.return_value = True

        _load_system_ca_certs(mock_context)

        # 验证至少尝试加载了一些证书路径
        self.assertTrue(mock_context.load_verify_locations.called)

    @patch("ddns.util.http.os.path.isfile")
    def test_load_ca_certs_no_files(self, mock_isfile):
        """测试没有找到CA证书文件"""
        mock_context = MagicMock()
        mock_isfile.return_value = False

        _load_system_ca_certs(mock_context)

        # 没有文件存在时不应该调用加载方法
        mock_context.load_verify_locations.assert_not_called()

    @patch("ddns.util.http.os.path.isfile")
    @patch("ddns.util.http.logger")
    def test_load_ca_certs_partial_failure(self, mock_logger, mock_isfile):
        """测试部分CA证书加载失败"""
        mock_context = MagicMock()
        mock_isfile.return_value = True
        # 模拟第一次成功，第二次失败
        mock_context.load_verify_locations.side_effect = [None, Exception("Load failed"), None]

        _load_system_ca_certs(mock_context)

        # 应该继续尝试加载其他证书
        self.assertTrue(mock_context.load_verify_locations.call_count > 1)


class TestCloseConnection(unittest.TestCase):
    """测试 _close_connection 函数"""

    def test_close_connection_success(self):
        """测试成功关闭连接"""
        mock_conn = MagicMock()

        _close_connection(mock_conn)

        mock_conn.close.assert_called_once()

    @patch("ddns.util.http.logger")
    def test_close_connection_failure(self, mock_logger):
        """测试关闭连接失败"""
        mock_conn = MagicMock()
        mock_conn.close.side_effect = Exception("Close failed")

        _close_connection(mock_conn)

        mock_conn.close.assert_called_once()
        mock_logger.warning.assert_called_once()


class TestBuildRedirectUrl(unittest.TestCase):
    """测试 _build_redirect_url 函数"""

    def test_absolute_url(self):
        """测试绝对URL重定向"""
        result = _build_redirect_url("http://new.example.com/api", "http://old.example.com", "/old")
        self.assertEqual(result, "http://new.example.com/api")

    def test_absolute_path(self):
        """测试绝对路径重定向"""
        result = _build_redirect_url("/newpath", "http://example.com", "/oldpath")
        self.assertEqual(result, "http://example.com/newpath")

    def test_relative_path(self):
        """测试相对路径重定向"""
        result = _build_redirect_url("newfile.html", "http://example.com", "/dir/oldfile.html")
        self.assertEqual(result, "http://example.com/dir/newfile.html")

    def test_relative_path_root(self):
        """测试根目录相对路径重定向"""
        result = _build_redirect_url("newfile.html", "http://example.com", "/oldfile.html")
        self.assertEqual(result, "http://example.com/newfile.html")

    def test_relative_path_no_slash(self):
        """测试无斜杠路径的相对重定向"""
        result = _build_redirect_url("newfile.html", "http://example.com", "oldfile.html")
        self.assertEqual(result, "http://example.com/newfile.html")


class TestDecodeResponseBody(unittest.TestCase):
    """测试 _decode_response_body 函数"""

    def test_utf8_decoding(self):
        """测试UTF-8解码"""
        raw_body = to_bytes("中文测试", "utf-8")
        result = _decode_response_body(raw_body, "text/html; charset=utf-8")
        self.assertEqual(result, "中文测试")

    def test_gbk_decoding(self):
        """测试GBK解码"""
        raw_body = to_bytes("中文测试", "gbk")
        result = _decode_response_body(raw_body, "text/html; charset=gbk")
        self.assertEqual(result, "中文测试")

    def test_gb2312_alias(self):
        """测试GB2312别名映射到GBK"""
        raw_body = to_bytes("中文测试", "gbk")
        result = _decode_response_body(raw_body, "text/html; charset=gb2312")
        self.assertEqual(result, "中文测试")

    def test_iso_8859_1_alias(self):
        """测试ISO-8859-1别名映射到latin-1"""
        raw_body = to_bytes("test", "latin-1")
        result = _decode_response_body(raw_body, "text/html; charset=iso-8859-1")
        self.assertEqual(result, "test")

    def test_no_charset_fallback_to_utf8(self):
        """测试没有charset时默认使用UTF-8"""
        raw_body = to_bytes("test", "utf-8")
        result = _decode_response_body(raw_body, "text/html")
        self.assertEqual(result, "test")

    def test_no_content_type(self):
        """测试没有Content-Type时使用UTF-8"""
        raw_body = to_bytes("test", "utf-8")
        result = _decode_response_body(raw_body, None)
        self.assertEqual(result, "test")

    def test_empty_body(self):
        """测试空响应体"""
        result = _decode_response_body(byte_string(""), "text/html")
        self.assertEqual(result, "")

    def test_invalid_encoding_fallback(self):
        """测试无效编码时的后备机制"""
        raw_body = to_bytes("中文测试", "utf-8")
        # 指定一个无效的编码
        result = _decode_response_body(raw_body, "text/html; charset=invalid-encoding")
        self.assertEqual(result, "中文测试")  # 应该回退到UTF-8

    def test_malformed_charset(self):
        """测试格式错误的charset"""
        raw_body = to_bytes("test", "utf-8")
        result = _decode_response_body(raw_body, "text/html; charset=")
        self.assertEqual(result, "test")


class TestSendHttpRequest(unittest.TestCase):
    """测试 send_http_request 函数"""

    @patch("ddns.util.http._create_connection")
    @patch("ddns.util.http._close_connection")
    def test_http_request_success(self, mock_close, mock_create):
        """测试HTTP请求成功"""
        mock_conn = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.reason = "OK"
        mock_response.getheader.return_value = "application/json; charset=utf-8"
        mock_response.getheaders.return_value = [("Content-Type", "application/json; charset=utf-8")]
        mock_response.read.return_value = byte_string('{"success": true}')
        mock_conn.getresponse.return_value = mock_response
        mock_create.return_value = mock_conn

        result = send_http_request("GET", "http://example.com/api")

        # 验证返回的是HttpResponse对象
        self.assertIsInstance(result, HttpResponse)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.reason, "OK")
        self.assertEqual(result.body, '{"success": true}')
        self.assertEqual(result.headers, [("Content-Type", "application/json; charset=utf-8")])

        mock_create.assert_called_once_with("example.com", None, False, None, True)
        mock_conn.request.assert_called_once_with("GET", "/api", None, {})
        mock_close.assert_called_once_with(mock_conn)

    @patch("ddns.util.http._create_connection")
    @patch("ddns.util.http._close_connection")
    def test_https_request_success(self, mock_close, mock_create):
        """测试HTTPS请求成功"""
        mock_conn = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.reason = "OK"
        mock_response.getheader.return_value = "application/json"
        mock_response.getheaders.return_value = [("Content-Type", "application/json")]
        mock_response.read.return_value = byte_string('{"secure": true}')
        mock_conn.getresponse.return_value = mock_response
        mock_create.return_value = mock_conn

        result = send_http_request("GET", "https://secure.example.com/api")

        self.assertIsInstance(result, HttpResponse)
        self.assertEqual(result.status, 200)
        self.assertEqual(result.body, '{"secure": true}')
        mock_create.assert_called_once_with("secure.example.com", None, True, None, True)

    @patch("ddns.util.http._create_connection")
    @patch("ddns.util.http._close_connection")
    def test_request_with_body_and_headers(self, mock_close, mock_create):
        """测试带请求体和头的请求"""
        mock_conn = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 201
        mock_response.reason = "Created"
        mock_response.getheader.return_value = "application/json"
        mock_response.getheaders.return_value = [("Content-Type", "application/json")]
        mock_response.read.return_value = byte_string('{"created": true}')
        mock_conn.getresponse.return_value = mock_response
        mock_create.return_value = mock_conn

        headers = {"Content-Type": "application/json"}
        body = '{"data": "test"}'

        result = send_http_request("POST", "http://example.com/api", body=body, headers=headers)

        self.assertIsInstance(result, HttpResponse)
        self.assertEqual(result.status, 201)
        self.assertEqual(result.body, '{"created": true}')
        mock_conn.request.assert_called_once_with("POST", "/api", body, headers)

    @patch("ddns.util.http._create_connection")
    @patch("ddns.util.http._close_connection")
    def test_request_with_query_params(self, mock_close, mock_create):
        """测试带查询参数的请求"""
        mock_conn = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.reason = "OK"
        mock_response.getheader.return_value = None
        mock_response.getheaders.return_value = []
        mock_response.read.return_value = byte_string('{"query": true}')
        mock_conn.getresponse.return_value = mock_response
        mock_create.return_value = mock_conn

        result = send_http_request("GET", "http://example.com/api?param1=value1&param2=value2")

        self.assertIsInstance(result, HttpResponse)
        self.assertEqual(result.body, '{"query": true}')
        mock_conn.request.assert_called_once_with("GET", "/api?param1=value1&param2=value2", None, {})

    @patch("ddns.util.http._create_connection")
    @patch("ddns.util.http._close_connection")
    def test_http_error_response(self, mock_close, mock_create):
        """测试HTTP错误响应"""
        mock_conn = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.reason = "Not Found"
        mock_response.getheader.return_value = None
        mock_response.getheaders.return_value = []
        mock_response.read.return_value = byte_string('{"error": "Not found"}')
        mock_conn.getresponse.return_value = mock_response
        mock_create.return_value = mock_conn

        result = send_http_request("GET", "http://example.com/notfound")

        # 验证返回的是HttpResponse对象，不抛出异常
        self.assertIsInstance(result, HttpResponse)
        self.assertEqual(result.status, 404)
        self.assertEqual(result.reason, "Not Found")
        self.assertEqual(result.body, '{"error": "Not found"}')
        mock_close.assert_called_once_with(mock_conn)

    def test_too_many_redirects(self):
        """测试重定向次数超限"""
        with self.assertRaises(HTTPException) as context:
            send_http_request("GET", "http://example.com/api", max_redirects=0)

        self.assertEqual(str(context.exception), "Too many redirects")

    @patch("ddns.util.http._create_connection")
    @patch("ddns.util.http._close_connection")
    @patch("ddns.util.http.logger")
    def test_ssl_auto_fallback(self, mock_logger, mock_close, mock_create):
        """测试SSL auto模式的自动降级"""
        # 第一次连接SSL失败
        mock_conn1 = MagicMock()
        mock_conn1.request.side_effect = ssl.SSLError("certificate verify failed")

        # 第二次连接成功
        mock_conn2 = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.reason = "OK"
        mock_response.getheader.return_value = None
        mock_response.getheaders.return_value = []
        mock_response.read.return_value = byte_string('{"fallback": true}')
        mock_conn2.getresponse.return_value = mock_response

        mock_create.side_effect = [mock_conn1, mock_conn2]

        result = send_http_request("GET", "https://bad-ssl.example.com/api", verify_ssl="auto")

        self.assertIsInstance(result, HttpResponse)
        self.assertEqual(result.body, '{"fallback": true}')
        mock_logger.warning.assert_called_once()

    @patch("ddns.util.http._create_connection")
    @patch("ddns.util.http._close_connection")
    def test_redirect_301_absolute_url(self, mock_close, mock_create):
        """测试301重定向到绝对URL"""
        # 第一次请求返回301重定向
        mock_conn1 = MagicMock()
        mock_response1 = MagicMock()
        mock_response1.status = 301
        mock_response1.getheader.return_value = "http://new.example.com/newapi"
        mock_conn1.getresponse.return_value = mock_response1

        # 第二次请求返回成功
        mock_conn2 = MagicMock()
        mock_response2 = MagicMock()
        mock_response2.status = 200
        mock_response2.reason = "OK"
        mock_response2.getheader.return_value = None
        mock_response2.getheaders.return_value = []
        mock_response2.read.return_value = byte_string('{"redirected": true}')
        mock_conn2.getresponse.return_value = mock_response2

        mock_create.side_effect = [mock_conn1, mock_conn2]

        result = send_http_request("GET", "http://old.example.com/api")

        self.assertIsInstance(result, HttpResponse)
        self.assertEqual(result.body, '{"redirected": true}')
        # 验证第二次调用使用了新的主机名
        second_call_args = mock_create.call_args_list[1][0]
        self.assertEqual(second_call_args[0], "new.example.com")

    @patch("ddns.util.http._create_connection")
    @patch("ddns.util.http._close_connection")
    def test_redirect_302_relative_path(self, mock_close, mock_create):
        """测试302重定向到相对路径"""
        # 第一次请求返回302重定向
        mock_conn1 = MagicMock()
        mock_response1 = MagicMock()
        mock_response1.status = 302
        mock_response1.getheader.return_value = "/newpath"
        mock_conn1.getresponse.return_value = mock_response1

        # 第二次请求返回成功
        mock_conn2 = MagicMock()
        mock_response2 = MagicMock()
        mock_response2.status = 200
        mock_response2.reason = "OK"
        mock_response2.getheader.return_value = None
        mock_response2.getheaders.return_value = []
        mock_response2.read.return_value = byte_string('{"relative": true}')
        mock_conn2.getresponse.return_value = mock_response2

        mock_create.side_effect = [mock_conn1, mock_conn2]

        result = send_http_request("GET", "http://example.com/oldpath")

        self.assertIsInstance(result, HttpResponse)
        self.assertEqual(result.body, '{"relative": true}')
        # 验证第二次请求使用了正确的路径
        mock_conn2.request.assert_called_once_with("GET", "/newpath", None, {})

    @patch("ddns.util.http._create_connection")
    @patch("ddns.util.http._close_connection")
    def test_redirect_303_post_to_get(self, mock_close, mock_create):
        """测试303重定向POST变为GET"""
        # 第一次POST请求返回303重定向
        mock_conn1 = MagicMock()
        mock_response1 = MagicMock()
        mock_response1.status = 303
        mock_response1.getheader.return_value = "/result"
        mock_conn1.getresponse.return_value = mock_response1

        # 第二次GET请求返回成功
        mock_conn2 = MagicMock()
        mock_response2 = MagicMock()
        mock_response2.status = 200
        mock_response2.reason = "OK"
        mock_response2.getheader.return_value = None
        mock_response2.getheaders.return_value = []
        mock_response2.read.return_value = byte_string('{"method_changed": true}')
        mock_conn2.getresponse.return_value = mock_response2

        mock_create.side_effect = [mock_conn1, mock_conn2]

        result = send_http_request("POST", "http://example.com/submit", body="data")

        self.assertIsInstance(result, HttpResponse)
        self.assertEqual(result.body, '{"method_changed": true}')
        # 验证第二次请求变为GET且没有body
        mock_conn2.request.assert_called_once_with("GET", "/result", None, {})

    @patch("ddns.util.http._create_connection")
    @patch("ddns.util.http._close_connection")
    @patch("ddns.util.http.logger")
    def test_redirect_without_location_header(self, mock_logger, mock_close, mock_create):
        """测试重定向状态码但没有Location头"""
        # 第一次请求返回重定向但没有Location头
        mock_conn1 = MagicMock()
        mock_response1 = MagicMock()
        mock_response1.status = 302
        mock_response1.getheader.return_value = None  # 没有Location头
        mock_conn1.getresponse.return_value = mock_response1

        # 第二次请求（重定向到空字符串）
        mock_conn2 = MagicMock()
        mock_response2 = MagicMock()
        mock_response2.status = 200
        mock_response2.reason = "OK"
        mock_response2.getheader.return_value = None
        mock_response2.getheaders.return_value = []
        mock_response2.read.return_value = byte_string('{"empty_location": true}')
        mock_conn2.getresponse.return_value = mock_response2

        mock_create.side_effect = [mock_conn1, mock_conn2]

        result = send_http_request("GET", "http://example.com/api")

        mock_logger.warning.assert_called_once()
        self.assertIsInstance(result, HttpResponse)
        self.assertEqual(result.body, '{"empty_location": true}')


if __name__ == "__main__":
    unittest.main()
