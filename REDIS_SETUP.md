# Redis 验证码系统设置指南

## 1. 安装 Redis

### Windows

```bash
# 下载Redis for Windows
# 或使用Docker
docker run -d --name redis -p 6379:6379 redis:latest
```

### Linux/Mac

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# CentOS/RHEL
sudo yum install redis

# Mac (使用Homebrew)
brew install redis
```

## 2. 启动 Redis 服务

```bash
# Linux/Mac
redis-server

# 或作为服务启动
sudo systemctl start redis

# Windows (如果安装了Redis)
redis-server.exe

# Docker
docker start redis
```

## 3. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

## 4. 环境变量配置 (可选)

创建 `.env` 文件或设置环境变量：

```bash
# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # 如果有密码的话
```

## 5. 验证码系统功能

### 发送验证码

- **接口**: `GET /login/getSendMessage?phoneNumber=手机号`
- **功能**:
  - 发送短信验证码
  - 验证码存储到 Redis，5 分钟过期
  - 发送频率限制：60 秒间隔
  - 手机号格式验证

### 验证验证码

- **接口**: `GET /login/postCodeVerify?code=验证码&phoneNumber=手机号`
- **功能**:
  - 验证用户输入的验证码
  - 最多尝试 5 次
  - 验证成功后删除验证码
  - 返回登录 token

## 6. Redis 存储结构

### 验证码存储

```
键: verification_code:sms:手机号
值: {
  "code": "123456",
  "phone_number": "13800138000",
  "created_at": "2024-01-01T12:00:00",
  "expire_at": "2024-01-01T12:05:00",
  "attempts": 0,
  "max_attempts": 5
}
过期时间: 5分钟
```

### 发送频率限制

```
键: sms_frequency:sms:手机号
值: 发送时间戳
过期时间: 60秒
```

## 7. 容错机制

如果 Redis 不可用，系统会自动：

- 使用内存存储作为后备方案
- 输出警告信息
- 保证基本功能正常运行

## 8. 测试验证码系统

### 发送验证码

```bash
curl "http://127.0.0.1:8836/login/getSendMessage?phoneNumber=13800138000"
```

### 验证验证码

```bash
curl "http://127.0.0.1:8836/login/postCodeVerify?code=123456&phoneNumber=13800138000"
```

## 9. 监控和管理

### 查看 Redis 中的验证码

```bash
redis-cli
> KEYS verification_code:*
> GET verification_code:sms:13800138000
```

### 清理过期数据

Redis 会自动清理过期数据，无需手动操作。

## 10. 生产环境配置建议

1. **Redis 配置优化**:

   - 设置合适的内存限制
   - 启用持久化（如果需要）
   - 配置密码认证

2. **安全建议**:

   - 使用 JWT token 替代简单 UUID
   - 添加更严格的手机号验证
   - 实现 IP 限制和黑名单功能

3. **监控**:
   - 监控 Redis 内存使用
   - 记录验证码发送和验证日志
   - 设置告警机制

## 故障排除

### 常见问题

1. **Redis 连接失败**

   - 检查 Redis 是否正在运行
   - 确认端口和主机配置
   - 查看防火墙设置

2. **验证码无法存储**

   - 检查 Redis 内存是否充足
   - 确认权限配置
   - 查看应用日志

3. **验证码验证失败**
   - 确认验证码未过期
   - 检查手机号是否匹配
   - 验证尝试次数是否超限
