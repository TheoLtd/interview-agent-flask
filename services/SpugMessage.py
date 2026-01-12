import requests
import random
import string
from flask import current_app

class SpugMessage():
    def __init__(self, phone_number, validity_time=5, name="面试通", code=None):
        self.phone_number = phone_number
        self.validity_time = validity_time
        self.name = name
        self.code = code

    def send_message(self):
        self.generate_code()
        try:
            # 在函数内获取配置，避免在模块加载时获取current_app
            spug_api = current_app.config.get('SPUG_API')
            if not spug_api or not spug_api.get('ID'):
                print("❌ SPUG API配置缺失")
                return {"status": "error", "message": "SPUG API配置缺失"}
            
            url = "https://push.spug.cc/send/{0}".format(spug_api['ID'])
            data = {
                "key1": self.name,
                "key2": self.code,
                "key3": self.validity_time,
                "targets": self.phone_number
            }
            
            # print(f"📱 正在发送短信到: {self.phone_number}, 验证码: {self.code}")
            # print(f"🔗 Spug API URL: {url}")
            
            response = requests.post(url, data=data)
            # print(f"📤 Spug API响应状态码: {response.status_code}")
            # print(f"📤 Spug API响应内容: {response.text}")
            
            result = response.json()
            
            # 检查Spug API响应
            if response.status_code == 200 or response.status_code == 204:
                # 存储验证码到缓存/数据库（用于后续验证）
                store_result = self._store_verification_code()
                # print(f"💾 验证码存储结果: {store_result}")
                
                # 检查Spug API返回的具体状态
                if result.get('code') == 200 and result.get('msg') == '请求成功':
                    # print("✅ 短信发送成功")
                    return {"status": "success", "message": "短信发送成功", "spug_response": result}
                else:
                    # print(f"❌ Spug API返回失败: {result}")
                    return {"status": "error", "message": f"短信发送失败: {result.get('message', '未知错误')}", "spug_response": result}
            else:
                # print(f"❌ HTTP请求失败，状态码: {response.status_code}")
                return {"status": "error", "message": f"HTTP请求失败，状态码: {response.status_code}"}
            
        except requests.exceptions.RequestException as e:
            # print(f"❌ 网络请求异常: {e}")
            return {"status": "error", "message": f"网络请求失败: {str(e)}"}
        except Exception as e:
            # print(f"❌ 发送短信异常: {e}")
            return {"status": "error", "message": f"发送短信失败: {str(e)}"}
    
    def _store_verification_code(self):
        """存储验证码到缓存或数据库，用于后续验证"""
        from .VerificationCodeService import verification_service
        return verification_service.store_code(
            phone_number=self.phone_number,
            code=self.code,
            expire_minutes=self.validity_time,
            code_type="sms"
        )
    
    def generate_code(self):
        self.code = ''.join(random.choices(string.digits, k=6))