# 人脸检测 API 升级说明

## 🎯 升级概述

本次升级将人脸检测接口从旧的讯飞表情分析 API 升级到了新的讯飞人脸检测 API，完全参照提供的 demo 代码实现。

## 🔄 主要变更

### 1. **API 接口变更**

- **旧接口**: `http://tupapi.xfyun.cn/v1/expression`
- **新接口**: `http://api.xf-yun.com/v1/private/{server_id}`

### 2. **认证方式变更**

- **旧方式**: MD5 签名认证
- **新方式**: HMAC-SHA256 签名认证（与 demo 完全一致）

### 3. **请求格式变更**

- **旧格式**: 简单的图片二进制数据
- **新格式**: JSON 结构体，包含 header、parameter、payload

### 4. **响应格式变更**

- **旧响应**: 直接返回表情统计数组
- **新响应**: 返回详细的人脸检测结果，需要解析 base64 编码的 JSON

## 📊 表情映射关系

### 讯飞 API 表情编码

根据用户提供的信息，讯飞 API 返回的表情编码为：

- `0`: 惊讶
- `1`: 害怕
- `2`: 厌恶
- `3`: 高兴
- `4`: 悲伤
- `5`: 生气
- `6`: 正常

### 项目内部表情编码

项目使用的表情标签（来自 config.py）：

```python
FACIAL_EXPRESSION_LABEL = [
    "其他(非人脸表情图片)",  # 0
    "其他表情",             # 1
    "喜悦",                # 2
    "愤怒",                # 3
    "悲伤",                # 4
    "惊恐",                # 5
    "厌恶",                # 6
    "中性"                 # 7
]
```

### 映射转换

```python
expression_mapping = {
    0: 5,  # 惊讶 -> 惊恐
    1: 5,  # 害怕 -> 惊恐
    2: 6,  # 厌恶 -> 厌恶
    3: 2,  # 高兴 -> 喜悦
    4: 4,  # 悲伤 -> 悲伤
    5: 3,  # 生气 -> 愤怒
    6: 7,  # 正常 -> 中性
}
```

## 🛠️ 技术实现

### 1. **签名算法**

```python
def assemble_ws_auth_url(request_url, method="POST", api_key="", api_secret=""):
    # 按照demo代码实现HMAC-SHA256签名
    signature_origin = "host: {}\ndate: {}\n{} {} HTTP/1.1".format(host, date, method, path)
    signature_sha = hmac.new(api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                             digestmod=hashlib.sha256).digest()
    # ... 生成认证URL
```

### 2. **请求体构建**

```python
def gen_body(appid, img_path, server_id):
    body = {
        "header": {"app_id": appid, "status": 3},
        "parameter": {
            server_id: {
                "service_kind": "face_detect",
                "detect_points": "1",
                "detect_property": "1",
                "face_detect_result": {"encoding": "utf8", "compress": "raw", "format": "json"}
            }
        },
        "payload": {
            "input1": {"encoding": "jpg", "status": 3, "image": base64_image}
        }
    }
```

### 3. **响应解析**

```python
# 1. 获取响应
resp_data = response.json()

# 2. 解码base64结果
encoded_text = resp_data['payload']['face_detect_result']['text']
decoded_text = base64.b64decode(encoded_text).decode('utf-8')

# 3. 解析人脸数据
face_data = json.loads(decoded_text)
```

## 🔧 配置要求

配置文件(`app/config.py`)已包含所需配置：

```python
FACIAL_DETECT_API = {
    'url': "http://api.xf-yun.com/v1/private/{}",
    'server_id': "s67c9c78c",
    'appid': 'db4f89ef',
    'apisecret': 'ZDIwNzBiZmVlZmQyNGVkYzE4YWUyMDcx',
    'apikey': '53aa48c511bcb1cedc81fe7702342e1f',
}
```

## 🧪 测试方式

### 运行测试脚本

```bash
python test_face_detect.py
```

### 测试内容

- ✅ API 配置验证
- ✅ 网络连接测试
- ✅ 签名算法验证
- ✅ 响应解析测试
- ✅ 表情映射验证

## 📈 升级优势

### 1. **更准确的检测**

- 使用最新的讯飞人脸检测 API
- 支持更多人脸属性检测
- 提供置信度分数

### 2. **更强的兼容性**

- 与 demo 代码完全一致的实现
- 标准化的认证流程
- 规范的错误处理

### 3. **更好的扩展性**

- 支持检测更多人脸特征点
- 可以轻松添加其他人脸属性
- 模块化的代码结构

## 🔍 调试信息

升级后的代码包含详细的调试日志：

```
🔍 开始人脸检测: /path/to/image.jpg
🔗 请求URL: http://api.xf-yun.com/v1/private/s67c9c78c
📤 API响应: {'header': {'code': 0, 'message': 'success'}, ...}
🎭 人脸检测结果: {'face_1': {'property': {'expression': 3}}, ...}
检测到表情: 讯飞表情代码=3, 映射到项目表情索引=2
📊 表情统计结果: [0, 0, 1, 0, 0, 0, 0, 0]
```

## ⚠️ 注意事项

1. **网络要求**: 需要能够访问讯飞 API 服务器
2. **图片格式**: 支持 JPG、PNG、BMP 格式
3. **文件大小**: 建议图片大小不超过 2MB
4. **错误处理**: 任何异常都会返回默认值 `[1, 0, 0, 0, 0, 0, 0, 0]`

## 🚀 使用方式

升级后，原有的调用方式保持不变：

```python
from services.FaceDetect import facial_detect

# 检测图片表情
result = facial_detect("/path/to/image.jpg")
# 返回: [0, 0, 1, 0, 0, 0, 0, 0]  # 表示检测到"喜悦"表情
```

项目的其他部分无需修改，保持了完全的向后兼容性。
