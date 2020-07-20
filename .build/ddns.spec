# -*- mode: python -*-

block_cipher = None

from PyInstaller.utils.hooks import exec_statement
cert_datas = exec_statement(
    'import ssl;print(ssl.get_default_verify_paths().cafile)').strip()
if cert_datas and cert_datas != 'None':
    cert_datas = [(f, 'lib') for f in cert_datas.split()]
else:
    cert_datas = []


a = Analysis(['../run.py'],
             pathex=[],
             binaries=[],
             datas=cert_datas,
             hiddenimports=[
                 'dns.dnspod', 
                 'dns.alidns',
                 'dns.dnspod_com',
                 'dns.dnscom',
                 'dns.cloudflare',
                 'dns.he',
                 'dns.huaweidns',
                 'dns.callback'
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure,
          a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='ddns',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True)
