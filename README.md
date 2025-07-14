# 面试助手 Flask 项目

这是一个基于 Flask 框架开发的智能面试助手系统，采用蓝图架构，集成了 AI 对话、数字人、简历分析等功能。

## 项目结构

```
interview-agent-flask/
├── app/                          # Flask 应用核心模块
│   ├── __init__.py              # Flask 应用工厂函数 (34行)
│   ├── config.py                # 应用配置文件 (8行)
│   ├── extensions.py            # Flask 扩展初始化
│   ├── blueprints/              # 蓝图模块
│   │   ├── __init__.py         # 蓝图包初始化
│   │   ├── interview/          # 面试蓝图
│   │   │   ├── __init__.py    # 面试蓝图初始化 (24行)
│   │   │   └── routes.py      # 面试路由 (275行)
│   │   ├── practice/           # 练习蓝图
│   │   │   ├── __init__.py    # 练习蓝图初始化 (4行)
│   │   │   └── routes.py      # 练习路由 (149行)
│   │   ├── interview_preset/   # 面试预设蓝图
│   │   │   ├── __init__.py    # 预设蓝图初始化 (10行)
│   │   │   └── routes.py      # 预设路由 (58行)
│   │   └── database/           # 数据库管理蓝图
│   │       ├── __init__.py    # 数据库蓝图初始化 (11行)
│   │       └── routes.py      # 数据库路由 (74行)
│   └── models/                 # 数据模型
│       ├── __init__.py        # 模型包初始化 (8行)
│       ├── interview_preset.py # 面试预设模型 (67行)
│       └── database.py        # 数据库模型
│
├── avatar/                       # 数字人模块
│   ├── AipaasAuth.py           # 数字人认证模块 (65行)
│   └── AvatarWebSocket.py      # 数字人 WebSocket 连接 (226行)
│
├── services/                     # 核心服务模块
│   ├── DeepSeek.py             # DeepSeek AI 对话服务 (127行)
│   ├── SparkPractice.py        # 练习 AI 服务 (69行)
│   ├── FaceDetect.py           # 人脸检测服务 (76行)
│   ├── AnalysisResume.py       # 简历分析服务 (76行)
│   ├── prompt.txt              # AI 对话提示词模板
│   └── feedbackPrompt.txt      # 反馈提示词模板
│
├── static/                       # 静态文件
│   ├── css/                    # 样式文件
│   └── js/                     # JavaScript 文件
│
├── templates/                    # 模板文件
│   └── database_manager.html   # 数据库管理页面 (183行)
│
├── resource/                     # 资源文件目录
│   ├── face_image/             # 人脸图片存储
│   ├── feedback/               # 反馈文件存储
│   ├── resume/                 # 简历文件存储
│   └── stream/                 # 视频流文件存储
│
├── run.py                       # 应用启动入口 (6行)
├── requirements.txt             # Python 依赖包列表 (13行)
└── README.md                   # 项目说明文档
```

## 核心功能模块

### 1. 面试蓝图 (`app/blueprints/interview/`)

- **面试初始化**: `POST /interview/init` - 设置面试参数（专业、意向、岗位描述）
- **人脸检测**: `POST /interview/image_detect` - 实时检测面试者表情
- **AI 对话**: `GET /interview/answer` - 与 DeepSeek AI 进行面试对话
- **数字人初始化**: `GET /interview/init_shuziren` - 启动数字人面试官
- **视频流**: `GET /interview/video/<filename>` - 获取数字人视频流
- **反馈生成**: `GET /interview/feedback` - 生成面试反馈报告

### 2. 练习蓝图 (`app/blueprints/practice/`)

- **AI 问答**: `GET /practice/answer_v1` - 基于 SparkPractice 的智能问答
- **学习评估**: `GET /practice/evaluate` - 分析学习薄弱环节
- **流式评估**: `GET /practice/evaluate_v2` - 流式输出评估结果
- **简历分析**: `POST /practice/resume` - 上传简历获取优化建议

### 3. 面试预设蓝图 (`app/blueprints/interview_preset/`)

- **预设管理**: 管理面试问题和预设场景

### 4. 数据库管理蓝图 (`app/blueprints/database/`)

- **数据库操作**: 管理面试数据和用户信息

### 5. 数字人模块 (`avatar/`)

- **WebSocket 连接**: 实时与数字人进行语音对话
- **RTMP 转 HLS**: 将数字人视频流转换为网页可播放格式
- **表情检测**: 实时分析面试者面部表情

### 6. AI 服务模块 (`services/`)

- **DeepSeek API**: 主要的 AI 对话服务
- **SparkPractice API**: 练习场景的 AI 服务
- **人脸检测**: OpenCV 实现的面部表情识别
- **简历分析**: 智能简历优化建议

## 技术架构

### 蓝图架构

- **模块化设计**: 使用 Flask 蓝图实现功能模块化
- **路由分离**: 不同功能模块使用独立的蓝图
- **配置集中**: 统一的配置管理

### 技术栈

- **后端框架**: Flask 3.1.1
- **跨域支持**: flask_cors 6.0.1
- **AI 服务**: OpenAI API, DeepSeek API
- **图像处理**: OpenCV 4.11.0.86
- **文档处理**: PyPDF2, python_docx
- **WebSocket**: ws4py 0.6.0
- **HTTP 请求**: Requests 2.32.4

## 启动方式

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python run.py
```

应用将在 `http://127.0.0.1:8836` 启动，支持以下主要功能：

- 智能面试对话
- 数字人面试官
- 简历分析优化
- 学习进度评估
- 实时表情检测
- 面试预设管理
- 数据库管理

## 配置说明

项目使用 `app/config.py` 进行配置管理，支持：

- 数据库连接配置
- AI 服务 API 密钥
- 数字人服务配置
- 文件存储路径配置

## API 路由

### 面试相关

- `POST /interview/init` - 初始化面试
- `POST /interview/image_detect` - 人脸检测
- `GET /interview/answer` - AI 对话
- `GET /interview/init_shuziren` - 启动数字人
- `GET /interview/video/<filename>` - 视频流
- `GET /interview/feedback` - 生成反馈
- `GET /interview/del_wss` - 关闭连接

### 面试预设管理

- `GET /interview_preset/api/presets` - 获取所有面试预设（支持分页和搜索）
- `GET /interview_preset/api/presets/<id>` - 获取单个面试预设
- `POST /interview_preset/api/presets` - 创建新的面试预设
- `PUT /interview_preset/api/presets/<id>` - 更新面试预设
- `DELETE /interview_preset/api/presets/<id>` - 删除面试预设
- `GET /interview_preset/api/presets/major/<major>` - 根据专业获取面试预设
- `GET /interview_preset/api/presets/random_some` - 获取 3 个随机面试预设
- `GET /interview_preset/api/presets/random_some/<num>` - 获取指定数量的随机面试预设

#### 随机预设接口详情

**获取默认随机预设**

```
GET /interview_preset/api/presets/random_some
```

**响应示例：**

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

**获取指定数量随机预设**

```
GET /interview_preset/api/presets/random_some/5
```

**参数说明：**

- `num`: 请求的随机预设数量（1-50，超过 50 自动限制为 50）

**错误响应：**

```json
{
  "error": "数量必须大于0"
}
```

### 练习相关

- `GET /practice/answer` - 模拟问答
- `GET /practice/answer_v1` - AI 问答
- `GET /practice/evaluate` - 学习评估
- `GET /practice/evaluate_v2` - 流式评估
- `POST /practice/resume` - 简历分析

## 注意事项

- 项目依赖 FFmpeg 进行视频流转换
- 需要配置相应的 AI 服务 API 密钥
- 数字人服务需要单独的服务商支持
- 建议在生产环境中使用环境变量管理敏感配置
- 全局变量在多用户环境下需要改进为会话管理
