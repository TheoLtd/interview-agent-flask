import http.client
import json
from flask import current_app

class AIMbtiAPI():
    _instance = None

    def __init__(self):
        self.name = "MBTI测试助手"
    
    def get_answer(self, prompt, max_retries=1):
        api_key = current_app.config['SPARK_MBTI_API']['api_key']
        api_secret = current_app.config['SPARK_MBTI_API']['api_secret']
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {api_key}:{api_secret}",
        }
        
        # 与 SparkPractice 保持一致，使用 host + path
        agent_client = http.client.HTTPSConnection(current_app.config['SPARK_MBTI_API']['host'], timeout=120)
        data = {
            "flow_id": current_app.config['SPARK_MBTI_API']['flow_id'],
            "uid": "123",
            "parameters": {"AGENT_USER_INPUT": prompt},
            "ext": {},
            "stream": False,
        }
        payload = json.dumps(data)
        agent_client.request(
            "POST", current_app.config['SPARK_MBTI_API'].get('path', '/workflow/v1/chat/completions'), payload, headers, encode_chunked=True)
        res = agent_client.getresponse()
        data = res.readline()
        response_data = json.loads(data.decode("utf-8"))
        content = response_data["choices"][0]["delta"]["content"]
        return content

    @classmethod
    def getInstance(cls) -> "AIMbtiAPI":
        if cls._instance is None:
            cls._instance = AIMbtiAPI()
        return cls._instance
