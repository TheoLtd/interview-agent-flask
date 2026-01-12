import http.client
import json
from flask import current_app
import uuid


class AIResumeRefinationAPI():
    _instance = None

    def __init__(self):
        self.name = "简历优化助手"
        self.session_id = str(uuid.uuid4())
        print("已创建简历优化助手, 会话id{0}".format(self.session_id))

    def get_answer(self, prompt, max_retries=3):
        api_key = current_app.config['RESUME_REFINATION_API']['api_key']
        api_secret = current_app.config['RESUME_REFINATION_API']['api_secret']

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}:{api_secret}",
        }

        # 创建HTTPS连接
        agent_client = http.client.HTTPSConnection(
            current_app.config['RESUME_REFINATION_API']['host'],
            timeout=120
        )

        # 准备请求数据
        data = {
            "flow_id": current_app.config['RESUME_REFINATION_API']['flow_id'],
            "uid": "123",
            "session_id" : self.session_id,
            "parameters": {"AGENT_USER_INPUT": prompt},
            "ext": {},
            "stream": False,
        }
        payload = json.dumps(data)

        try:
            # 发送请求
            agent_client.request(
                "POST",
                current_app.config['RESUME_REFINATION_API'].get('path', '/workflow/v1/chat/completions'),
                payload,
                headers
            )
            res = agent_client.getresponse()

            # 检查HTTP状态
            if res.status != 200:
                error_msg = f"API错误: HTTP {res.status} {res.reason}"
                current_app.logger.error(error_msg)
                return error_msg

            # 读取完整响应
            raw_data = res.read()
            response_data = json.loads(raw_data.decode("utf-8"))

            # 检查API错误码
            if "code" in response_data and response_data["code"] != 0:
                error_code = response_data["code"]
                error_msg = response_data.get("message", "未知错误")
                current_app.logger.error(f"API错误 ({error_code}): {error_msg}")
                return f"API错误 ({error_code}): {error_msg}"

            # 解析响应内容
            if "choices" in response_data and response_data["choices"]:
                choice = response_data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
                elif "delta" in choice and "content" in choice["delta"]:
                    return choice["delta"]["content"]

            # 其他可能的响应结构
            if "content" in response_data:
                return response_data["content"]

            # 无法解析响应
            current_app.logger.error(f"无法解析API响应: {response_data}")
            return "错误: 无法解析API响应"

        except Exception as e:
            error_msg = f"API调用失败: {str(e)}"
            current_app.logger.error(error_msg)
            if max_retries > 0:
                current_app.logger.info(f"重试中... ({max_retries} 次剩余)")
                return self.get_answer(prompt, max_retries - 1)
            return error_msg

    @classmethod
    def getInstance(cls) -> "AIResumeRefinationAPI":
        if cls._instance is None:
            cls._instance = AIResumeRefinationAPI()
        return cls._instance