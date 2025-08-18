# -*- coding: utf-8 -*-
import json
from datetime import datetime
from time import mktime
from wsgiref.handlers import format_date_time
from urllib.parse import urlencode
import os
import traceback
import hmac
import hashlib
import requests
import base64
from flask import current_app


class AssembleHeaderException(Exception):
    def __init__(self, msg):
        self.message = msg


class Url:
    def __init__(self, host, path, schema):
        self.host = host
        self.path = path
        self.schema = schema


def sha256base64(data):
    """进行sha256加密和base64编码"""
    sha256 = hashlib.sha256()
    sha256.update(data)
    digest = base64.b64encode(sha256.digest()).decode(encoding='utf-8')
    return digest


def parse_url(request_url):
    """解析URL"""
    stidx = request_url.index("://")
    host = request_url[stidx + 3:]
    schema = request_url[:stidx + 3]
    edidx = host.index("/")
    if edidx <= 0:
        raise AssembleHeaderException("invalid request url:" + request_url)
    path = host[edidx:]
    host = host[:edidx]
    u = Url(host, path, schema)
    return u


def assemble_ws_auth_url(request_url, method="POST", api_key="", api_secret=""):
    """组装认证URL"""
    u = parse_url(request_url)
    host = u.host
    path = u.path
    now = datetime.now()
    date = format_date_time(mktime(now.timetuple()))
    
    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha256).digest()
    signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = "api_key=\"%s\", algorithm=\"%s\", headers=\"%s\", signature=\"%s\"" % (
        api_key, "hmac-sha256", "host date request-line", signature_sha)
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    
    values = {
        "host": host,
        "date": date,
        "authorization": authorization
    }

    return request_url + "?" + urlencode(values)


def gen_body(appid, img_path, server_id):
    """生成请求体"""
    with open(img_path, 'rb') as f:
        img_data = f.read()
    body = {
        "header": {
            "app_id": appid,
            "status": 3
        },
        "parameter": {
            server_id: {
                "service_kind": "face_detect",
                "detect_points": "1",  # 检测特征点
                "detect_property": "1",  # 检测人脸属性
                "face_detect_result": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "json"
                }
            }
        },
        "payload": {
            "input1": {
                "encoding": "jpg",
                "status": 3,
                "image": str(base64.b64encode(img_data), 'utf-8')
            }
        }
    }
    return json.dumps(body)


def parse_expression_result(face_data):
    """
    解析人脸检测结果，转换表情到统计数组
    讯飞表情映射：0:惊讶；1:害怕；2:厌恶；3:高兴；4:悲伤；5:生气；6:正常
    项目表情映射：[其他(非人脸表情图片), 其他表情, 喜悦, 愤怒, 悲伤, 惊恐, 厌恶, 中性]
    """
    # 初始化表情统计数组 [其他, 其他表情, 喜悦, 愤怒, 悲伤, 惊恐, 厌恶, 中性]
    expression_count = [0, 0, 0, 0, 0, 0, 0, 0]
    
    if face_data.get('face_num', 0) == 0:
        # 没有检测到人脸
        expression_count[0] = 1  # 其他(非人脸表情图片)
        return expression_count
    
    # 获取第一个人脸的表情信息
    face_1 = face_data.get('face_1', {})
    if not face_1:
        expression_count[1] = 1  # 其他表情
        return expression_count
    
    property_info = face_1.get('property', {})
    expression = property_info.get('expression', -1)
    
    # 讯飞表情到项目表情的映射
    expression_mapping = {
        0: 5,  # 惊讶 -> 惊恐
        1: 5,  # 害怕 -> 惊恐  
        2: 6,  # 厌恶 -> 厌恶
        3: 2,  # 高兴 -> 喜悦
        4: 4,  # 悲伤 -> 悲伤
        5: 3,  # 生气 -> 愤怒
        6: 7,  # 正常 -> 中性
    }
    
    if expression in expression_mapping:
        expression_count[expression_mapping[expression]] = 1
    else:
        expression_count[1] = 1  # 其他表情
    
    print(f"检测到表情: 讯飞表情代码={expression}, 映射到项目表情索引={expression_mapping.get(expression, 1)}")
    return expression_count


def facial_detect(img_path=""):
    """
    人脸检测主函数
    使用讯飞人脸检测API进行表情识别
    """
    if not img_path:
        print("❌ 图片路径为空")
        return [1, 0, 0, 0, 0, 0, 0, 0]  # 返回"其他(非人脸表情图片)"
    
    if not os.path.exists(img_path):
        print(f"❌ 图片文件不存在: {img_path}")
        return [1, 0, 0, 0, 0, 0, 0, 0]
    
    try:
        # 获取配置
        config = current_app.config.get('FACIAL_DETECT_API', {})
        appid = config.get('appid')
        apikey = config.get('apikey')
        apisecret = config.get('apisecret')
        server_id = config.get('server_id', 's67c9c78c')
        url_template = config.get('url', 'http://api.xf-yun.com/v1/private/{}')
        
        if not all([appid, apikey, apisecret]):
            print("❌ 讯飞API配置缺失")
            return [1, 0, 0, 0, 0, 0, 0, 0]
        
        # 构建请求URL
        url = url_template.format(server_id)
        request_url = assemble_ws_auth_url(url, "POST", apikey, apisecret)
        
        # 构建请求头
        headers = {
            'content-type': "application/json", 
            'host': 'api.xf-yun.com', 
            'app_id': appid
        }
        
        # 构建请求体
        body = gen_body(appid, img_path, server_id)
        
        print(f"🔍 开始人脸检测: {img_path}")
        print(f"🔗 请求URL: {url}")
        
        # 发送请求
        response = requests.post(request_url, data=body, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ HTTP请求失败，状态码: {response.status_code}")
            return [1, 0, 0, 0, 0, 0, 0, 0]
        
        # 解析响应
        resp_data = response.json()
        print(f"📤 API响应: {resp_data}")
        
        # 检查响应状态
        header = resp_data.get('header', {})
        if header.get('code') != 0:
            print(f"❌ API返回错误: {header.get('message', '未知错误')}")
            return [1, 0, 0, 0, 0, 0, 0, 0]
        
        # 获取人脸检测结果
        payload = resp_data.get('payload', {})
        face_detect_result = payload.get('face_detect_result', {})
        
        if not face_detect_result:
            print("❌ 未获取到人脸检测结果")
            return [1, 0, 0, 0, 0, 0, 0, 0]
        
        # 解码base64结果
        encoded_text = face_detect_result.get('text', '')
        if not encoded_text:
            print("❌ 人脸检测结果为空")
            return [1, 0, 0, 0, 0, 0, 0, 0]
        
        # 解码并解析结果
        decoded_text = base64.b64decode(encoded_text).decode('utf-8')
        face_data = json.loads(decoded_text)
        
        print(f"🎭 人脸检测结果: {face_data}")
        
        # 转换为表情统计数组
        expression_result = parse_expression_result(face_data)
        print(f"📊 表情统计结果: {expression_result}")
        
        return expression_result
        
    except Exception as e:
        print(f"❌ 人脸检测异常: {str(e)}")
        print(f"详细错误: {traceback.format_exc()}")
        return [1, 0, 0, 0, 0, 0, 0, 0]


def add_arrays(arr1, arr2):
    """数组相加"""
    return [a + b for a, b in zip(arr1, arr2)]

# facial_detect(bendiimage)

# print(r.content)

