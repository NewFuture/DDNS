#-*- coding:utf-8 -*-

# DNSPOD API 接口
import httplib
import urllib
import json

TOKEN = "id,token"  # token
PROXY = None  # 代理设置

def request(action,method='POST',**params):  # 发送请求
    API_SITE = "dnsapi.cn"
    if PROXY:
        conn = httplib.HTTPSConnection(PROXY)
        conn.set_tunnel(API_SITE, 443)
    else:
        conn = httplib.HTTPSConnection(API_SITE)
    
    params['login_token'],params['format'] = TOKEN,'json'
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/json"}
    conn.request(method, '/' + action, urllib.urlencode(params), headers)
    
    response = conn.getresponse()
    data = response.read()
    conn.close()
    
    if response.status == 200:
        return json.loads(data)
    else:
        return None

def get_domain_info(domain):  # 切割域名获取主域名和对应ID
    """
    TODO @记录支持
    """
    domain_split = domain.split('.')
    if 3 == len(domain_split) : # 长度为3
        sub, main = domain_split[0], domain_split[1] + '.' + domain_split[2]
        id = get_domain_id(main)
    else : # 长度大于三通过API判断,最后两个，三个递增
        main = domain_split.pop()
        while domain_split:
            main = domain_split.pop()+'.'+main
            id = get_domain_id(main)
            if id:
                sub = ".".join(domain_split)
                break 
        else:
            return None,None
    return id, sub


def get_domain_id(domain):  
    """
        获取域名ID
        http://www.dnspod.cn/docs/domains.html#domain-info
    """
    if not hasattr(get_domain_id, "domain_list"):
        get_domain_id.domain_list = {}  # "静态变量"存储已查询过的id

    if domain in get_domain_id.domain_list:
        #如果已经存在直接返回防止再次请求
        return get_domain_id.domain_list[domain]
    else:
        info = request('Domain.Info', domain=domain)
        if info and info.get('status',{}).get('code') == "1":
            id = info.get("domain",{}).get("id")
            if id:
                get_domain_id.domain_list[domain] = id
                return id


def get_records(id, **conditions):
    """
        获取记录ID
        返回满足条件的所有记录[]
        TODO 大于3000翻页
        http://www.dnspod.cn/docs/records.html#record-list
    """
    if not hasattr(get_records, "records"):
        get_records.records = {}  # "静态变量"存储已查询过的id
        get_records.keys = ("id","name","type","line","line_id","enabled","mx","value")
    
    if not id in get_records.records:
        get_records.records[id]={}
        data = request('Record.List', domain_id=id)
        if data and data.get("status",{}).get("code") == "1":
            for r in data.get('records'):
                get_records.records[id][r["id"]]={k: v for (k, v) in r.items() if k in get_records.keys}

    record = {}
    for (id,r) in get_records.records[id].items():
        for (k,v) in conditions.items():
            if r.get(k) != v :
                break
        else: # for else push
            record[id] = r
    return record

def update_record(domain, value, record_type="A"):  # 更改记录
    domainid,sub = get_domain_info(domain)
    if not domainid:
        raise "invalid domain"+domain
    
    records = get_records(domainid,name=sub,type=record_type)
    result={}
    if records: # update
        #http://www.dnspod.cn/docs/records.html#record-modify
        for (id,record) in records.items():
            if record["value"] != value:
                r=request('Record.Modify',record_id=id,record_line=record["line"].encode("utf-8"),value=value, sub_domain=sub,domain_id=domainid,record_type=record_type,ttl=600)
                if r and r.get("status",{}).get("code") == "1":
                    get_records.records[domainid][id]["value"]=value
                    result[id]=r.get("record")
                else:
                     result[id]="update fail!\n"+str(r)
            else:
                result[id]=domain
    else: # create
        #http://www.dnspod.cn/docs/records.html#record-create
        r = request("Record.Create", domain_id=domainid, value=value, sub_domain=sub, record_type=record_type, record_line="默认", ttl=600)
        if r and r.get("status",{}).get("code") == "1":
            id = r.get("record")["id"]
            get_records.records[domainid][id]=r.get("record")
            result=r.get("record")
        else:
            result=domain + " created fail!"
    return result
