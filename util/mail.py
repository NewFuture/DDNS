# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText


def send_email(host, port=25, to_addrs=None, user=None, password=None, html=None):
    msg = MIMEText(html, 'html', 'utf-8')
    msg['Subject'] = 'DDNS'
    msg['From'] = user
    # 收件人为多个收件人,通过join将列表转换为以;为间隔的字符串
    msg['To'] = ";".join(to_addrs)
    smtp = smtplib.SMTP()
    smtp.set_debuglevel(1)
    smtp.connect(host=host, port=port)
    smtp.login(user, password)
    smtp.sendmail(user, to_addrs, msg.as_string())
