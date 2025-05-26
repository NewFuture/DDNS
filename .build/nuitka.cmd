nuitka --standalone --onefile \
       --product-name=DDNS \
       --file-description="DDNS Client 自动更新域名解析到本机IP" \
       --remove-output \
       --include-module=dns.dnspod \
       --include-module=dns.alidns \
       --include-module=dns.dnspod_com \
       --include-module=dns.dnscom \
       --include-module=dns.cloudflare \
       --include-module=dns.he \
       --include-module=dns.huaweidns \
       --include-module=dns.callback \
       --windows-console-mode=attach \
       --copyright="2016-2025, New Future" \
       --windows-icon-from-ico=".build/icon.png" \
       --macos-app-icon=".build/icon.png" \
       run.py