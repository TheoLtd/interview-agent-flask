# Avatar 会话超时 API 文档

## 概述

为 Avatar 面试会话添加了 30 分钟超时限制，确保会话不会无限期运行，提高系统资源利用率。

## 功能特性

### 1. 自动超时机制

- **超时时间**: 30 分钟（1800 秒）
- **警告提醒**: 25 分钟时发送警告消息
- **自动终止**: 30 分钟后自动发送结束消息并终止会话

### 2. 会话状态监控

- 实时跟踪会话开始时间
- 计算剩余时间和已用时间
- 检查会话是否过期

### 3. 优雅关闭

- 超时前 5 分钟发送警告
- 超时时发送告别消息
- 自动清理资源

## API 端点

### 1. 获取会话状态

```http
GET /interview/session_status
```

**响应示例**:

```json
{
  "session_active": true,
  "remaining_time": 1200,
  "elapsed_time": 600,
  "remaining_minutes": 20.0,
  "elapsed_minutes": 10.0,
  "message": "会话活跃，剩余时间: 20.0分钟"
}
```

**字段说明**:

- `session_active`: 会话是否活跃
- `remaining_time`: 剩余时间（秒）
- `elapsed_time`: 已用时间（秒）
- `remaining_minutes`: 剩余时间（分钟）
- `elapsed_minutes`: 已用时间（分钟）
- `message`: 状态描述信息

### 2. 手动结束会话

```http
POST /interview/end_session
```

**响应示例**:

```json
{
  "success": true,
  "message": "会话已成功结束"
}
```

### 3. 初始化数字人（更新）

```http
GET /interview/init_shuziren
```

**响应示例**（新增字段）:

```json
{
  "content": "true",
  "remaining_time": 1800,
  "session_active": true
}
```

## 实现细节

### AvatarWebSocket 类新增属性

```python
class avatarWebsocket:
    def __init__(self, ...):
        # 会话超时相关属性
        self.session_start_time = None      # 会话开始时间
        self.session_timeout = 30 * 60      # 超时时间（30分钟）
        self.timeout_warning_sent = False   # 是否已发送警告
        self.timeout_timer = None           # 超时定时器
```

### 新增方法

```python
def get_session_remaining_time(self):
    """获取会话剩余时间（秒）"""

def get_session_elapsed_time(self):
    """获取会话已用时间（秒）"""

def is_session_expired(self):
    """检查会话是否已过期"""

def start_timeout_monitor(self):
    """启动超时监控线程"""

def stop_timeout_monitor(self):
    """停止超时监控"""
```

## 使用示例

### 前端监控会话状态

```javascript
// 定期检查会话状态
setInterval(async () => {
  try {
    const response = await fetch("/interview/session_status");
    const status = await response.json();

    if (!status.session_active) {
      console.log("会话已结束");
      // 处理会话结束逻辑
    } else {
      console.log(`剩余时间: ${status.remaining_minutes}分钟`);

      // 如果剩余时间少于5分钟，显示警告
      if (status.remaining_minutes < 5) {
        showTimeoutWarning(status.remaining_minutes);
      }
    }
  } catch (error) {
    console.error("检查会话状态失败:", error);
  }
}, 30000); // 每30秒检查一次
```

### 手动结束会话

```javascript
async function endSession() {
  try {
    const response = await fetch("/interview/end_session", {
      method: "POST",
    });
    const result = await response.json();

    if (result.success) {
      console.log("会话已结束");
      // 跳转到结束页面
    }
  } catch (error) {
    console.error("结束会话失败:", error);
  }
}
```

## 配置选项

可以通过修改`avatarWebsocket`类的`session_timeout`属性来调整超时时间：

```python
# 在创建实例后修改超时时间
wsclient = avatarWebsocket(authUrl, protocols='', headers=None)
wsclient.session_timeout = 45 * 60  # 设置为45分钟
```

## 测试

使用提供的测试脚本验证超时功能：

```bash
python test_avatar_timeout.py
```

测试脚本会：

1. 测试超时相关函数的正确性
2. 可选择进行完整的 Avatar 连接超时测试
3. 验证警告和自动终止机制

## 注意事项

1. **资源清理**: 会话结束时会自动清理相关资源
2. **并发安全**: 当前实现使用全局变量，在高并发环境下可能需要改进
3. **网络异常**: 网络断开时会自动触发清理机制
4. **日志记录**: 所有超时事件都会记录到控制台和日志文件

## 错误处理

- 会话未启动时调用状态检查会返回相应提示
- 网络错误时会自动重试或优雅降级
- 超时处理过程中的异常会被捕获并记录
