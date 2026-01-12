# 面试助手 API 文档

## 概述

面试助手是一个基于 Flask 的智能面试系统，提供面试预设管理、AI 对话、数字人面试等功能。

**基础 URL**: `http://127.0.0.1:8836`

## 常用

7, 8.1, 8.2

## 面试预设管理 API

### 1. 获取所有面试预设

**接口**: `GET /interview_preset/api/presets`

**描述**: 获取所有面试预设，支持分页和搜索

**查询参数**:

- `page` (可选): 页码，默认为 1
- `per_page` (可选): 每页数量，默认为 10
- `search` (可选): 搜索关键词

**请求示例**:

```
GET /interview_preset/api/presets?page=1&per_page=10&search=Java
```

**响应示例**:

```json
{
  "data": [
    {
      "id": 1,
      "name": "Java开发工程师面试",
      "brief": "Java基础到高级的全面面试",
      "difficulty": 3.5,
      "tags": "Java,Spring,MySQL",
      "heat": 4.2,
      "major": "计算机科学",
      "intension": "后端开发",
      "responsibility": "负责公司核心业务系统的开发..."
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 10,
    "total_records": 25,
    "total_pages": 3
  },
  "search": "Java"
}
```

### 2. 获取单个面试预设

**接口**: `GET /interview_preset/api/presets/{id}`

**描述**: 根据 ID 获取单个面试预设

**路径参数**:

- `id`: 预设 ID

**请求示例**:

```
GET /interview_preset/api/presets/1
```

**响应示例**:

```json
{
  "id": 1,
  "name": "Java开发工程师面试",
  "brief": "Java基础到高级的全面面试",
  "difficulty": 3.5,
  "tags": "Java,Spring,MySQL",
  "heat": 4.2,
  "major": "计算机科学",
  "intension": "后端开发",
  "responsibility": "负责公司核心业务系统的开发..."
}
```

**错误响应** (404):

```json
{
  "error": "面试预设不存在"
}
```

### 3. 创建面试预设

**接口**: `POST /interview_preset/api/presets`

**描述**: 创建新的面试预设

**请求体示例**:

```json
{
  "name": "Python开发工程师面试",
  "brief": "Python全栈开发面试",
  "difficulty": 3.0,
  "tags": "Python,Django,Flask",
  "heat": 4.0,
  "major": "计算机科学",
  "intension": "后端开发",
  "responsibility": "负责Python后端系统开发..."
}
```

**响应示例**:

```json
{
  "success": true,
  "message": "面试预设创建成功",
  "id": 26
}
```

### 4. 更新面试预设

**接口**: `PUT /interview_preset/api/presets/{id}`

**描述**: 更新指定 ID 的面试预设

**路径参数**:

- `id`: 预设 ID

**请求体示例**: 同创建接口

**响应示例**:

```json
{
  "success": true,
  "message": "面试预设更新成功"
}
```

### 5. 删除面试预设

**接口**: `DELETE /interview_preset/api/presets/{id}`

**描述**: 删除指定 ID 的面试预设

**路径参数**:

- `id`: 预设 ID

**响应示例**:

```json
{
  "success": true,
  "message": "面试预设删除成功"
}
```

### 6. 根据专业获取面试预设

**接口**: `GET /interview_preset/api/presets/major/{major}`

**描述**: 根据专业名称获取相关的面试预设

**路径参数**:

- `major`: 专业名称

**请求示例**:

```
GET /interview_preset/api/presets/major/计算机科学
```

**响应示例**:

```json
[
  {
    "id": 1,
    "name": "Java开发工程师面试",
    "brief": "Java基础到高级的全面面试",
    "difficulty": 3.5,
    "tags": "Java,Spring,MySQL",
    "heat": 4.2,
    "major": "计算机科学",
    "intension": "后端开发",
    "responsibility": "负责公司核心业务系统的开发..."
  }
]
```

### 7. 搜索面试预设

**接口**: `GET /interview_preset/api/presets/search`

**描述**: 根据面试岗位名称进行模糊搜索

**查询参数**:

- `keyword` (必需): 搜索关键词
- `page` (可选): 页码，默认为 1
- `per_page` (可选): 每页数量，默认为 10，最大 100

**请求示例**:

```
GET /interview_preset/api/presets/search?keyword=Java&page=1&per_page=10
```

**响应示例**:

```json
{
  "data": [
    {
      "id": 1,
      "name": "Java开发工程师面试",
      "brief": "Java基础到高级的全面面试",
      "difficulty": 3.5,
      "tags": "Java,Spring,MySQL",
      "heat": 4.2,
      "major": "计算机科学",
      "intension": "后端开发",
      "responsibility": "负责公司核心业务系统的开发..."
    },
    {
      "id": 5,
      "name": "Java高级工程师面试",
      "brief": "Java高级开发技能面试",
      "difficulty": 4.0,
      "tags": "Java,Spring Boot,微服务",
      "heat": 4.5,
      "major": "计算机科学",
      "intension": "高级后端开发",
      "responsibility": "负责系统架构设计和核心模块开发..."
    }
  ],
  "pagination": {
    "current_page": 1,
    "per_page": 10,
    "total_records": 2,
    "total_pages": 1
  },
  "search": {
    "keyword": "Java",
    "field": "name"
  }
}
```

**错误响应** (400):

```json
{
  "error": "搜索关键词不能为空"
}
```

### 8. 获取随机面试预设

#### 8.1 获取默认数量随机预设

**接口**: `GET /interview_preset/api/presets/random_some`

**描述**: 获取 3 个随机面试预设

**请求示例**:

```
GET /interview_preset/api/presets/random_some
```

**响应示例**:

```json
{
  "data": [
    {
      "id": 1,
      "name": "Java开发工程师面试",
      "brief": "Java基础到高级的全面面试",
      "difficulty": 3.5,
      "tags": "Java,Spring,MySQL",
      "heat": 4.2,
      "major": "计算机科学",
      "intension": "后端开发",
      "responsibility": "负责公司核心业务系统的开发..."
    }
  ],
  "total_requested": 3,
  "total_available": 25,
  "actual_returned": 3
}
```

#### 8.2 获取指定数量随机预设

**接口**: `GET /interview_preset/api/presets/random_some/{num}`

**描述**: 获取指定数量的随机面试预设

**路径参数**:

- `num`: 请求的随机预设数量（1-50，超过 50 自动限制为 50）

**请求示例**:

```
GET /interview_preset/api/presets/random_some/5
```

**响应示例**:

```json
{
  "data": [
    {
      "id": 1,
      "name": "Java开发工程师面试",
      "brief": "Java基础到高级的全面面试",
      "difficulty": 3.5,
      "tags": "Java,Spring,MySQL",
      "heat": 4.2,
      "major": "计算机科学",
      "intension": "后端开发",
      "responsibility": "负责公司核心业务系统的开发..."
    }
  ],
  "total_requested": 5,
  "total_available": 25,
  "actual_returned": 5
}
```

**错误响应** (400):

```json
{
  "error": "数量必须大于0"
}
```

## 面试相关 API

### 1. 初始化面试

**接口**: `POST /interview/init`

**描述**: 初始化面试会话

**请求体示例**:

```json
{
  "major": "计算机科学",
  "intention": "后端开发",
  "job_description": "负责公司核心业务系统的开发..."
}
```

**响应示例**:

```json
{
  "success": true,
  "message": "面试初始化成功"
}
```

### 2. AI 对话

**接口**: `GET /interview/answer`

**描述**: 获取 AI 面试官的回复

**查询参数**:

- `message`: 用户消息

**请求示例**:

```
GET /interview/answer?message=你好，我是张三，有3年Java开发经验
```

**响应示例**:

```json
{
  "response": "您好张三，很高兴见到您。请详细介绍一下您的Java开发经验，特别是您使用过的技术栈和项目经验。"
}
```

### 3. 人脸检测

**接口**: `POST /interview/image_detect`

**描述**: 上传图片进行人脸表情检测

**请求体示例**: multipart/form-data

- `image`: 图片文件

**响应示例**:

```json
{
  "expression": "喜悦",
  "confidence": 0.85,
  "timestamp": "2025-07-13 12:30:00"
}
```

### 4. 启动数字人

**接口**: `GET /interview/init_shuziren`

**描述**: 启动数字人面试官

**响应示例**:

```json
{
  "success": true,
  "message": "数字人启动成功",
  "websocket_url": "ws://127.0.0.1:8836/avatar"
}
```

### 5. 生成反馈

**接口**: `GET /interview/feedback`

**描述**: 根据面试对话生成评估反馈

**响应示例**:

```json
{
  "scores": [76, 93, 87, 91, 83, 99],
  "advantages": [
    {
      "title": "需求分析能力",
      "desc": "能系统性地使用RICE模型进行优先级评估，展示了专业方法论"
    }
  ],
  "disadvantages": [
    {
      "title": "技术深度不足",
      "desc": "对分布式事务的Seata框架实现原理理解较浅，建议加强底层原理学习"
    }
  ]
}
```

## 练习相关 API

### 1. 学习评估

**接口**: `GET /practice/evaluate`

**描述**: 分析学习薄弱环节

**响应示例**:

```json
{
  "weaknesses": ["算法基础", "系统设计"],
  "recommendations": ["建议加强算法练习", "多关注系统架构设计"]
}
```

### 2. 流式评估

**接口**: `GET /practice/evaluate_v2`

**描述**: 流式输出评估结果

**响应**: Server-Sent Events 格式

### 3. 简历分析

**接口**: `POST /practice/resume`

**描述**: 上传简历获取优化建议

**请求体示例**: multipart/form-data

- `resume`: 简历文件（PDF/DOCX）

**响应示例**:

```json
{
  "analysis": {
    "strengths": ["技术栈丰富", "项目经验丰富"],
    "weaknesses": ["简历格式需要优化", "缺少量化成果"],
    "suggestions": ["建议添加项目成果数据", "优化简历结构"]
  }
}
```

## 数据库管理 API

### 1. 数据库管理界面

**接口**: `GET /db/`

**描述**: 访问数据库管理界面

**响应**: HTML 页面

### 2. 获取表数据

**接口**: `GET /db/api/tables/{table_name}`

**描述**: 获取指定表的数据

**查询参数**:

- `page`: 页码
- `per_page`: 每页数量
- `search`: 搜索关键词
- `search_column`: 搜索列名

**请求示例**:

```
GET /db/api/tables/interview_preset_recommended?page=1&per_page=10&search=&search_column=
```

## 错误码说明

| 状态码 | 说明           |
| ------ | -------------- |
| 200    | 请求成功       |
| 400    | 请求参数错误   |
| 404    | 资源不存在     |
| 500    | 服务器内部错误 |

## 通用错误响应格式

```json
{
  "error": "错误描述信息"
}
```

## 测试工具

### PowerShell 测试示例

```powershell
# 获取随机预设
Invoke-RestMethod -Uri "http://127.0.0.1:8836/interview_preset/api/presets/random_some" -Method GET

# 获取指定数量随机预设
Invoke-RestMethod -Uri "http://127.0.0.1:8836/interview_preset/api/presets/random_some/5" -Method GET
```

### Python 测试示例

```python
import requests

# 获取随机预设
response = requests.get("http://127.0.0.1:8836/interview_preset/api/presets/random_some")
print(response.json())

# 创建预设
data = {
    "name": "测试预设",
    "brief": "测试描述",
    "difficulty": 3.0,
    "tags": "测试",
    "heat": 4.0,
    "major": "计算机科学",
    "intension": "测试",
    "responsibility": "测试职责"
}
response = requests.post("http://127.0.0.1:8836/interview_preset/api/presets", json=data)
print(response.json())
```

## 注意事项

1. 所有 API 返回的 JSON 数据都使用 UTF-8 编码
2. 文件上传接口支持 PDF、DOCX、图片等格式
3. 数据库操作需要确保 MySQL 服务正常运行
4. 数字人功能需要 WebSocket 连接支持
5. 随机预设 API 会自动限制最大请求数量为 50，避免性能问题
