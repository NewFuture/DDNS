#!/usr/bin/env python
# -*- coding:utf-8 -*-

import unittest

class TestSSL(unittest.TestCase):
    """Test ssl connect"""
    def connect(self,domain):
        try:
            # python 2
            from httplib import HTTPSConnection
        except ImportError:
            # python 3
            from http.client import HTTPSConnection
        conn = HTTPSConnection(domain)
        try:
            conn.request("POST", "/")
        except:
            self.assertTrue(False)
        response = conn.getresponse()
        res = response.read().decode('utf8')
        conn.close()

    def test_dnspod(self):
        from dns import dnspod
        self.connect(dnspod.API.SITE)

    def test_dnspod_com(self):
        from dns import dnspod_com as dnspod
        self.connect(dnspod.API.SITE)

    def test_alidns(self):
        from dns import alidns
        self.connect(alidns.API.SITE)

    def test_cloudflare(self):
        from dns import cloudflare
        self.connect(cloudflare.API.SITE)

    def test_dnscom(self):
        from dns import dnscom
        self.connect(dnscom.API.SITE)

    def test_he(self):
        from dns import he
        self.connect(he.API.SITE)

    def test_huaweidns(self):
        from dns import huaweidns
        self.connect(huaweidns.API.SITE)

    def test_public_v4(self):
        """test public_v4"""
        from util import ip
        result=ip.public_v4()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result)>7)
    #def test_dnspod(self):
    #    """test dnspod"""
    #    from dns import dnspod
    #    dnspod.Config.ID='13490'
    #    dnspod.Config.TOKEN='6b5976c68aba5b14a0558b77c17c3932'
    #    result=dnspod.request('Info.Version')
    #    self.assertTrue(result["status"]["code"]=="1")
    #def test_dnspod_com(self):
    #    """test dnspod.com. notoken always fail"""
    #    from dns import dnspod_com as dnspod
    #    try:
    #        dnspod.request('Info.Version')
    #    except Exception as e:
    #        self.assertTrue(eval(str(e))["code"]=="-1")

def main():
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSSL))
    runner = unittest.TextTestRunner()
    runner.run(suite)
if __name__ == '__main__':
    main()
