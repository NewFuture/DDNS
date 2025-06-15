#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Nuitka Project Configuration
# nuitka-project: --mode=onefile
# nuitka-project: --output-filename=ddns
# nuitka-project: --output-dir=dist
# nuitka-project: --product-name=DDNS
# nuitka-project: --product-version=0.0.0
# nuitka-project: --onefile-tempdir-spec="{TEMP}/{PRODUCT}_{VERSION}"
# nuitka-project: --no-deployment-flag=self-execution
# nuitka-project: --company-name="New Future"
# nuitka-project: --copyright=https://ddns.newfuture.cc
# nuitka-project: --assume-yes-for-downloads
# nuitka-project: --python-flag=no_site,no_asserts,no_docstrings,isolated,static_hashes
# nuitka-project: --nofollow-import-to=tkinter,unittest,pydoc,doctest,distutils,setuptools,lib2to3,test,idlelib,lzma
# nuitka-project: --noinclude-dlls=liblzma.*

from ddns.__main__ import main

main()
