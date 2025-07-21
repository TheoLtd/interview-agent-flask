import http.client
import json
from flask import current_app


# print("a")
# headers = {
#     "Content-Type": "application/json",
#     "Accept": "text/event-stream",
#     "Authorization": f"Bearer {API_KEY}:{API_SECRET}",
# }


class AIPracticeAPI():
    _instance = None

    def __init__(self):
        self.name = "简历出题助手"
    
    def get_answer(self, prompt, max_retries=1):
        api_key = current_app.config['SPARK_PRACTICE_API']['api_key']
        api_secret = current_app.config['SPARK_PRACTICE_API']['api_secret']
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {api_key}:{api_secret}",
        }
        
        agent_client = http.client.HTTPSConnection(current_app.config['SPARK_PRACTICE_API']['url'], timeout=120)
        data = {
            "flow_id": current_app.config['SPARK_PRACTICE_API']['flow_id'],
            "uid": "123",
            "parameters": {"AGENT_USER_INPUT": prompt},
            "ext": {},
            "stream": False,
        }
        payload = json.dumps(data)
        agent_client.request(
            "POST", "/workflow/v1/chat/completions", payload, headers, encode_chunked=True)
        res = agent_client.getresponse()
        data = res.readline()
        # Remove the print statement that outputs conversation data to terminal
        # print(data.decode("utf-8"))
        response_data = json.loads(data.decode("utf-8"))
        content = response_data["choices"][0]["delta"]["content"]
        return content
    

    @classmethod
    def getInstance(cls)-> "AIPracticeAPI":
        if cls._instance is None:
            cls._instance = AIPracticeAPI()
        return cls._instance


# data = {
#     "flow_id": "7341661804480536578",
#     "uid": "123",
#     "parameters": {"AGENT_USER_INPUT": "你好"},
#     "ext": {},
#     "stream": True,
# }
# payload = json.dumps(data)

# conn = http.client.HTTPSConnection("xingchen-api.xf-yun.com", timeout=120)
# conn.request(
#     "POST", "/workflow/v1/chat/completions", payload, headers, encode_chunked=True
# )
# res = conn.getresponse()

# if data.get("stream"):
#     while chunk := res.readline():
#         print(chunk.decode("utf-8"))
# else:
#     data = res.readline()
#     print(data.decode("utf-8"))
