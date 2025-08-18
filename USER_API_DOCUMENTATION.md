# 用户系统 API 文档

## 概述

用户系统提供完整的用户认证、注册、资料管理和登录记录功能。支持三种登录方式：手机号验证码、账号密码、微信登录。

## 认证机制

- 使用 JWT（JSON Web Token）进行身份认证
- Token 有效期：24 小时
- 需要认证的接口需要在 Header 中携带：`Authorization: Bearer {token}`

## 登录接口

### 1. 手机号验证码登录

#### 1.1 发送验证码

```
GET /login/getSendMessage?phoneNumber={手机号}
```

**请求参数：**

- `phoneNumber`: 11 位手机号

**响应示例：**

```json
{
  "success": true,
  "message": "验证码发送成功",
  "code": 200
}
```

**错误响应：**

```json
{
  "success": false,
  "message": "请等待60秒后再试",
  "code": 429,
  "wait_seconds": 45
}
```

#### 1.2 验证码登录

```
GET /login/postCodeVerify?code={验证码}&phoneNumber={手机号}
```

**请求参数：**

- `code`: 6 位数字验证码
- `phoneNumber`: 手机号

**响应示例：**

```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 1,
      "name": "用户8727",
      "telephone": "15775988727"
    }
  },
  "code": 200
}
```

### 2. 账号密码登录

```
POST /login/postPasswordLogin
```

**请求体：**

```json
{
  "data": {
    "account": "用户名/邮箱/手机号",
    "password": "密码"
  }
}
```

**响应示例：**

```json
{
  "success": true,
  "message": "登录成功",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 1,
      "name": "张三",
      "telephone": "15775988727",
      "email": "zhang@example.com"
    }
  },
  "code": 200
}
```

### 3. 微信登录

```
POST /api/wechat/login
```

**请求体：**

```json
{
  "code": "微信授权码"
}
```

**响应示例：**

```json
{
  "code": 0,
  "msg": "登录成功",
  "openid": "oNWTp5BU2ZtyBXmr_cR2F0ZZQ1g",
  "session_key": "session_key_value",
  "user": {
    "id": 1,
    "name": "微信用户1g",
    "weixin_id": "oNWTp5BU2ZtyBXmr_cR2F0ZZQ1g"
  }
}
```

## 用户管理接口

### 4. 用户注册

```
POST /user/register
```

**请求体：**

```json
{
  "name": "张三",
  "email": "zhang@example.com",
  "password": "password123",
  "telephone": "15775988727",
  "age": 25,
  "major": "计算机科学",
  "school": "清华大学",
  "gender": 1
}
```

**响应示例：**

```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 1,
      "name": "张三",
      "email": "zhang@example.com",
      "telephone": "15775988727"
    }
  },
  "code": 200
}
```

### 5. 获取用户资料

```
GET /user/profile
Authorization: Bearer {token}
```

**响应示例：**

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "张三",
    "gender": 1,
    "telephone": "15775988727",
    "age": 25,
    "email": "zhang@example.com",
    "major": "计算机科学",
    "school": "清华大学",
    "introduction": "这个人很懒，什么都没有留下~",
    "avater": null
  },
  "code": 200
}
```

### 6. 更新用户资料

```
PUT /user/profile
Authorization: Bearer {token}
```

**请求体：**

```json
{
  "name": "李四",
  "age": 26,
  "introduction": "热爱编程的程序员",
  "major": "软件工程"
}
```

**响应示例：**

```json
{
  "success": true,
  "message": "资料更新成功",
  "code": 200
}
```

### 7. 修改密码

```
PUT /user/password
Authorization: Bearer {token}
```

**请求体：**

```json
{
  "old_password": "旧密码",
  "new_password": "新密码"
}
```

**响应示例：**

```json
{
  "success": true,
  "message": "密码修改成功",
  "code": 200
}
```

### 8. 获取登录历史

```
GET /user/login-history?limit=10
Authorization: Bearer {token}
```

**请求参数：**

- `limit`: 返回记录数量（可选，默认 10）

**响应示例：**

```json
{
  "success": true,
  "data": [
    {
      "login_method": "SMS",
      "login_time": "2025-08-19 13:46:27",
      "ip_address": "127.0.0.1",
      "identification": "a1b2c3d4e5f6g7h8"
    },
    {
      "login_method": "PWD",
      "login_time": "2025-08-19 12:30:15",
      "ip_address": "192.168.1.100",
      "identification": "h8g7f6e5d4c3b2a1"
    }
  ],
  "code": 200
}
```

## 调试接口

### 9. 查看验证码状态

```
GET /debug/verification/{手机号}
```

**响应示例：**

```json
{
  "phone_number": "15775988727",
  "storage_key": "verification_code:sms:15775988727",
  "memory_data": {
    "code": "123456",
    "phone_number": "15775988727",
    "created_at": "2025-08-19T05:46:27.993178",
    "expire_at": "2025-08-19T05:51:27.993178",
    "attempts": 0,
    "max_attempts": 5
  },
  "redis_data": null,
  "all_memory_keys": ["verification_code:sms:15775988727"],
  "redis_available": false
}
```

## 登录方式代码对照

- `SMS`: 手机号验证码登录
- `PWD`: 账号密码登录
- `WX`: 微信登录
- `REG`: 注册后自动登录

## 错误码说明

- `200`: 成功
- `400`: 请求参数错误
- `401`: 认证失败/Token 无效
- `404`: 资源不存在
- `409`: 资源冲突（如用户名已存在）
- `429`: 请求过于频繁
- `500`: 服务器内部错误

## 数据库表结构

### 用户表 (user)

- `id`: 用户 ID（主键）
- `name`: 用户名
- `gender`: 性别 ID（外键关联 gender 表）
- `telephone`: 手机号
- `weixin_id`: 微信 ID
- `age`: 年龄
- `email`: 邮箱
- `major`: 专业
- `school`: 学校
- `password`: 密码（加密存储）
- `introduction`: 个人简介
- `avater`: 头像 URL

### 登录日志表 (user_login_log)

- `id`: 日志 ID（主键）
- `user_id`: 用户 ID
- `login_method`: 登录方式
- `login_time`: 登录时间
- `ip_address`: IP 地址
- `identification`: 登录标识
- `access_code`: 访问码

### 性别表 (gender)

- `id`: 性别 ID（主键）
- `name`: 性别名称（男/女/其他）
