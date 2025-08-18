import json
import time
from datetime import datetime, timedelta
from app.extensions import get_redis, redis_manager


class VerificationCodeService:
    """验证码服务类"""
    
    def __init__(self):
        self.redis_client = None
        self.memory_storage = {}  # 内存后备存储
        
    def _get_redis_client(self):
        """获取Redis客户端"""
        if self.redis_client is None:
            self.redis_client = get_redis()
        return self.redis_client
    
    def _generate_key(self, phone_number, code_type="sms"):
        """生成Redis键"""
        return f"verification_code:{code_type}:{phone_number}"
    
    def store_code(self, phone_number, code, expire_minutes=5, code_type="sms"):
        """
        存储验证码
        :param phone_number: 手机号
        :param code: 验证码
        :param expire_minutes: 过期时间（分钟）
        :param code_type: 验证码类型
        :return: True/False
        """
        try:
            redis_client = self._get_redis_client()
            key = self._generate_key(phone_number, code_type)
            
            print(f"💾 存储验证码 - 手机号: {phone_number}, 验证码: {code}")
            print(f"💾 存储键: {key}, 过期时间: {expire_minutes}分钟")
            
            # 存储的数据结构
            code_data = {
                'code': code,
                'phone_number': phone_number,
                'created_at': datetime.now().isoformat(),
                'expire_at': (datetime.now() + timedelta(minutes=expire_minutes)).isoformat(),
                'attempts': 0,  # 验证尝试次数
                'max_attempts': 5  # 最大尝试次数
            }
            
            if redis_client and redis_manager.is_available():
                # 使用Redis存储
                redis_client.setex(
                    key, 
                    expire_minutes * 60,  # 转换为秒
                    json.dumps(code_data)
                )
                print(f"✅ 验证码已存储到Redis: {phone_number} -> {code}")
                return True
            else:
                # 使用内存存储作为后备
                self.memory_storage[key] = {
                    **code_data,
                    'expire_timestamp': time.time() + (expire_minutes * 60)
                }
                print(f"⚠️ 验证码已存储到内存: {phone_number} -> {code}")
                return True
                
        except Exception as e:
            print(f"❌ 存储验证码失败: {e}")
            return False
    
    def verify_code(self, phone_number, input_code, code_type="sms"):
        """
        验证验证码
        :param phone_number: 手机号
        :param input_code: 用户输入的验证码
        :param code_type: 验证码类型
        :return: dict 包含验证结果和信息
        """
        try:
            redis_client = self._get_redis_client()
            key = self._generate_key(phone_number, code_type)
            
            # debug code
            print(f"🔍 验证码验证 - 手机号: {phone_number}, 输入验证码: {input_code}")
            print(f"🔍 生成的存储键: {key}")
            print(f"🔍 Redis可用性: {redis_client is not None and redis_manager.is_available()}")
            
            # 从Redis获取
            if redis_client and redis_manager.is_available():
                # debug code
                print("🔍 从Redis获取验证码...")
                code_data_str = redis_client.get(key)
                # debug code
                print(f"🔍 Redis中的数据: {code_data_str}")
                if not code_data_str:
                    print("❌ Redis中未找到验证码")
                    return {
                        'success': False, 
                        'message': '验证码不存在或已过期',
                        'code': 'CODE_NOT_EXISTS'
                    }
                code_data = json.loads(code_data_str)
                # debug code
                print(f"🔍 解析后的验证码数据: {code_data}")
            else:
                # debug code
                print("🔍 从内存获取验证码...")
                # debug code
                print(f"🔍 内存中的所有键: {list(self.memory_storage.keys())}")
                if key not in self.memory_storage:
                    # debug code
                    print(f"❌ 内存中未找到键: {key}")
                    return {
                        'success': False, 
                        'message': '验证码不存在或已过期',
                        'code': 'CODE_NOT_EXISTS'
                    }
                
                code_data = self.memory_storage[key]
                # debug code
                print(f"🔍 内存中的验证码数据: {code_data}")
                # 检查内存中的过期时间
                current_time = time.time()
                expire_time = code_data.get('expire_timestamp', 0)
                # debug code
                print(f"🔍 当前时间: {current_time}, 过期时间: {expire_time}")
                if current_time > expire_time:
                    print("❌ 验证码已过期")
                    del self.memory_storage[key]
                    return {
                        'success': False, 
                        'message': '验证码已过期',
                        'code': 'CODE_EXPIRED'
                    }
            
            # 检查尝试次数
            if code_data.get('attempts', 0) >= code_data.get('max_attempts', 5):
                self._delete_code(phone_number, code_type)
                return {
                    'success': False, 
                    'message': '验证码尝试次数过多，请重新获取',
                    'code': 'TOO_MANY_ATTEMPTS'
                }
            
            # 检查验证码是否已被使用
            if code_data.get('used', False):
                return {
                    'success': False, 
                    'message': '验证码已被使用',
                    'code': 'CODE_ALREADY_USED'
                }

            # 验证码验证
            if str(input_code) == str(code_data['code']):
                # 验证成功，标记为已使用而不是删除
                code_data['used'] = True
                code_data['used_at'] = datetime.now().isoformat()
                self._update_attempts(phone_number, code_data, code_type)
                
                return {
                    'success': True, 
                    'message': '验证成功',
                    'code': 'VERIFY_SUCCESS'
                }
            else:
                # 验证失败，增加尝试次数
                code_data['attempts'] = code_data.get('attempts', 0) + 1
                self._update_attempts(phone_number, code_data, code_type)
                
                remaining_attempts = code_data.get('max_attempts', 5) - code_data['attempts']
                return {
                    'success': False, 
                    'message': f'验证码错误，还有{remaining_attempts}次尝试机会',
                    'code': 'CODE_INCORRECT',
                    'remaining_attempts': remaining_attempts
                }
                
        except Exception as e:
            # debug code
            print(f"❌ 验证验证码失败: {e}")
            return {
                'success': False, 
                'message': '验证服务异常',
                'code': 'SERVICE_ERROR'
            }
    
    def _update_attempts(self, phone_number, code_data, code_type="sms"):
        """更新尝试次数"""
        try:
            redis_client = self._get_redis_client()
            key = self._generate_key(phone_number, code_type)
            
            if redis_client and redis_manager.is_available():
                # 获取剩余TTL
                ttl = redis_client.ttl(key)
                if ttl > 0:
                    redis_client.setex(key, ttl, json.dumps(code_data))
            else:
                # 更新内存存储
                if key in self.memory_storage:
                    self.memory_storage[key].update(code_data)
                    
        except Exception as e:
            print(f"❌ 更新尝试次数失败: {e}")
    
    def _delete_code(self, phone_number, code_type="sms"):
        """删除验证码"""
        try:
            redis_client = self._get_redis_client()
            key = self._generate_key(phone_number, code_type)
            
            if redis_client and redis_manager.is_available():
                redis_client.delete(key)
            else:
                self.memory_storage.pop(key, None)
                
        except Exception as e:
            print(f"❌ 删除验证码失败: {e}")
    
    def check_send_frequency(self, phone_number, interval_seconds=60, code_type="sms"):
        """
        检查发送频率限制
        :param phone_number: 手机号
        :param interval_seconds: 发送间隔（秒）
        :param code_type: 验证码类型
        :return: dict 包含是否可以发送和剩余等待时间
        """
        try:
            redis_client = self._get_redis_client()
            frequency_key = f"sms_frequency:{code_type}:{phone_number}"
            
            if redis_client and redis_manager.is_available():
                last_send_time = redis_client.get(frequency_key)
                if last_send_time:
                    last_time = float(last_send_time)
                    elapsed = time.time() - last_time
                    if elapsed < interval_seconds:
                        return {
                            'can_send': False,
                            'wait_seconds': int(interval_seconds - elapsed),
                            'message': f'请等待{int(interval_seconds - elapsed)}秒后再试'
                        }
                
                # 记录本次发送时间
                redis_client.setex(frequency_key, interval_seconds, str(time.time()))
            else:
                # 简单的内存频率控制
                if hasattr(self, '_last_send_times'):
                    if phone_number in self._last_send_times:
                        elapsed = time.time() - self._last_send_times[phone_number]
                        if elapsed < interval_seconds:
                            return {
                                'can_send': False,
                                'wait_seconds': int(interval_seconds - elapsed),
                                'message': f'请等待{int(interval_seconds - elapsed)}秒后再试'
                            }
                else:
                    self._last_send_times = {}
                
                self._last_send_times[phone_number] = time.time()
            
            return {'can_send': True, 'wait_seconds': 0}
            
        except Exception as e:
            print(f"❌ 检查发送频率失败: {e}")
            return {'can_send': True, 'wait_seconds': 0}  # 发生错误时允许发送
    
    def cleanup_expired_codes(self):
        """清理过期的验证码（仅适用于内存存储）"""
        try:
            current_time = time.time()
            expired_keys = []
            
            for key, data in self.memory_storage.items():
                if current_time > data.get('expire_timestamp', 0):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.memory_storage[key]
                
            if expired_keys:
                print(f"🧹 清理了{len(expired_keys)}个过期验证码")
                
        except Exception as e:
            print(f"❌ 清理过期验证码失败: {e}")


# 全局验证码服务实例
verification_service = VerificationCodeService() 