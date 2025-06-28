# coding=utf-8
"""
测试 ddns.util.http 模块
Test ddns.util.http module
"""

import unittest
import ssl
from base_test import MagicMock, patch
from ddns.util.http import (
    HTTPException,
    send_http_request,
    _create_connection,
    _load_system_ca_certs,
    _close_connection,
    _build_redirect_url,
)


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
    @patch("ddns.util.http.ssl.create_default_context")
    @patch("ddns.util.http.logger")
    def test_create_https_connection_custom_ca_failure(self, mock_logger, mock_ssl_context, mock_https_conn):
        """测试创建HTTPS连接 - 自定义CA证书失败"""
        mock_context = MagicMock()
        mock_ssl_context.return_value = mock_context
        mock_context.load_verify_locations.side_effect = Exception("File not found")
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


class TestSendHttpRequest(unittest.TestCase):
    """测试 send_http_request 函数"""

    @patch("ddns.util.http._create_connection")
    @patch("ddns.util.http._close_connection")
    def test_http_request_success(self, mock_close, mock_create):
        """测试HTTP请求成功"""
        mock_conn = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"success": true}'
        mock_conn.getresponse.return_value = mock_response
        mock_create.return_value = mock_conn

        result = send_http_request("GET", "http://example.com/api")

        self.assertEqual(result, '{"success": true}')
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
        mock_response.read.return_value = b'{"secure": true}'
        mock_conn.getresponse.return_value = mock_response
        mock_create.return_value = mock_conn

        result = send_http_request("GET", "https://secure.example.com/api")

        self.assertEqual(result, '{"secure": true}')
        mock_create.assert_called_once_with("secure.example.com", None, True, None, True)

    @patch("ddns.util.http._create_connection")
    @patch("ddns.util.http._close_connection")
    def test_request_with_body_and_headers(self, mock_close, mock_create):
        """测试带请求体和头的请求"""
        mock_conn = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 201
        mock_response.read.return_value = b'{"created": true}'
        mock_conn.getresponse.return_value = mock_response
        mock_create.return_value = mock_conn

        headers = {"Content-Type": "application/json"}
        body = '{"data": "test"}'

        result = send_http_request("POST", "http://example.com/api", body=body, headers=headers)

        self.assertEqual(result, '{"created": true}')
        mock_conn.request.assert_called_once_with("POST", "/api", body, headers)

    @patch("ddns.util.http._create_connection")
    @patch("ddns.util.http._close_connection")
    def test_request_with_query_params(self, mock_close, mock_create):
        """测试带查询参数的请求"""
        mock_conn = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"query": true}'
        mock_conn.getresponse.return_value = mock_response
        mock_create.return_value = mock_conn

        result = send_http_request("GET", "http://example.com/api?param1=value1&param2=value2")

        self.assertEqual(result, '{"query": true}')
        mock_conn.request.assert_called_once_with("GET", "/api?param1=value1&param2=value2", None, {})

    @patch("ddns.util.http._create_connection")
    @patch("ddns.util.http._close_connection")
    def test_http_error_response(self, mock_close, mock_create):
        """测试HTTP错误响应"""
        mock_conn = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.reason = "Not Found"
        mock_response.read.return_value = b'{"error": "Not found"}'
        mock_conn.getresponse.return_value = mock_response
        mock_create.return_value = mock_conn

        with self.assertRaises(HTTPException) as context:
            send_http_request("GET", "http://example.com/notfound")

        self.assertEqual(str(context.exception), 'HTTP Error 404: Not Found\n{"error": "Not found"}')
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
        mock_response.read.return_value = b'{"fallback": true}'
        mock_conn2.getresponse.return_value = mock_response

        mock_create.side_effect = [mock_conn1, mock_conn2]

        result = send_http_request("GET", "https://bad-ssl.example.com/api", verify_ssl="auto")

        self.assertEqual(result, '{"fallback": true}')
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
        mock_response2.read.return_value = b'{"redirected": true}'
        mock_conn2.getresponse.return_value = mock_response2

        mock_create.side_effect = [mock_conn1, mock_conn2]

        result = send_http_request("GET", "http://old.example.com/api")

        self.assertEqual(result, '{"redirected": true}')
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
        mock_response2.read.return_value = b'{"relative": true}'
        mock_conn2.getresponse.return_value = mock_response2

        mock_create.side_effect = [mock_conn1, mock_conn2]

        result = send_http_request("GET", "http://example.com/oldpath")

        self.assertEqual(result, '{"relative": true}')
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
        mock_response2.read.return_value = b'{"method_changed": true}'
        mock_conn2.getresponse.return_value = mock_response2

        mock_create.side_effect = [mock_conn1, mock_conn2]

        result = send_http_request("POST", "http://example.com/submit", body="data")

        self.assertEqual(result, '{"method_changed": true}')
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
        mock_response2.read.return_value = b'{"empty_location": true}'
        mock_conn2.getresponse.return_value = mock_response2

        mock_create.side_effect = [mock_conn1, mock_conn2]

        result = send_http_request("GET", "http://example.com/api")

        mock_logger.warning.assert_called_once()
        self.assertEqual(result, '{"empty_location": true}')


if __name__ == "__main__":
    unittest.main()
