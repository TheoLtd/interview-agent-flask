import jwt
import uuid
import hashlib
from datetime import datetime, timedelta
from flask import current_app, request
from app.extensions import get_session
from app.models.user import User, UserLoginLog
from sqlalchemy.exc import IntegrityError
import requests


class UserService:
    """用户服务类"""
    
    def __init__(self):
        self.session = None
    
    def _get_session(self):
        """获取数据库会话"""
        if self.session is None:
            self.session = get_session()
        return self.session
    
    def generate_jwt_token(self, user_id, expire_hours=24):
        """生成JWT令牌"""
        try:
            payload = {
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(hours=expire_hours),
                'iat': datetime.utcnow(),
                'iss': 'interview-system'
            }
            
            secret_key = current_app.config.get('SECRET_KEY', 'dev-key')
            token = jwt.encode(payload, secret_key, algorithm='HS256')
            return token
        except Exception as e:
            print(f"❌ JWT生成失败: {e}")
            return None
    
    def verify_jwt_token(self, token):
        """验证JWT令牌"""
        try:
            secret_key = current_app.config.get('SECRET_KEY', 'dev-key')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return {'error': 'Token已过期'}
        except jwt.InvalidTokenError:
            return {'error': 'Token无效'}
    
    def create_or_get_user_by_phone(self, phone_number):
        """通过手机号创建或获取用户"""
        try:
            session = self._get_session()
            
            # 查找现有用户
            user = session.query(User).filter_by(telephone=phone_number).first()
            
            if user:
                print(f"✅ 找到现有用户: {user.name} ({phone_number})")
                return user
            
            # 创建新用户
            new_user = User(
                name=f"用户{phone_number[-4:]}",  # 默认用户名
                telephone=phone_number,
                avater=None,
                introduction="这个人很懒，什么都没有留下~"
            )
            
            session.add(new_user)
            session.commit()
            
            print(f"✅ 创建新用户: {new_user.name} ({phone_number})")
            return new_user
            
        except Exception as e:
            print(f"❌ 创建/获取用户失败: {e}")
            if session:
                session.rollback()
            return None
    
    def authenticate_user(self, account, password):
        """用户名/邮箱密码认证"""
        try:
            session = self._get_session()
            
            # 支持用户名、邮箱、手机号登录
            user = session.query(User).filter(
                (User.name == account) | 
                (User.email == account) | 
                (User.telephone == account)
            ).first()
            
            if user and user.check_password(password):
                print(f"✅ 用户认证成功: {user.name}")
                return user
            
            print(f"❌ 用户认证失败: {account}")
            return None
            
        except Exception as e:
            print(f"❌ 用户认证异常: {e}")
            return None
    
    def wechat_login(self, code):
        """微信登录"""
        try:
            # 获取微信配置
            wechat_config = current_app.config.get('MINI_PROGRAM_INFO', {})
            app_id = wechat_config.get('WECHAT_APPID')
            app_secret = wechat_config.get('WECHAT_SECRET')
            
            if not app_id or not app_secret:
                return {'success': False, 'message': '微信配置缺失'}
            
            # 调用微信API获取session_key和openid
            url = f"https://api.weixin.qq.com/sns/jscode2session"
            params = {
                'appid': app_id,
                'secret': app_secret,
                'js_code': code,
                'grant_type': 'authorization_code'
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'openid' not in data:
                return {
                    'success': False, 
                    'message': f"微信API调用失败: {data.get('errmsg', '未知错误')}"
                }
            
            openid = data['openid']
            session_key = data['session_key']
            
            # 查找或创建用户
            session = self._get_session()
            user = session.query(User).filter_by(weixin_id=openid).first()
            
            if not user:
                # 创建新用户
                user = User(
                    name=f"微信用户{openid[-4:]}",
                    weixin_id=openid,
                    introduction="这个人很懒，什么都没有留下~"
                )
                session.add(user)
                session.commit()
                print(f"✅ 创建微信新用户: {user.name}")
            else:
                print(f"✅ 微信用户登录: {user.name}")
            
            return {
                'success': True,
                'user': user,
                'openid': openid,
                'session_key': session_key
            }
            
        except Exception as e:
            print(f"❌ 微信登录失败: {e}")
            return {'success': False, 'message': f'微信登录异常: {str(e)}'}
    
    def update_user_profile(self, user_id, profile_data):
        """更新用户资料"""
        try:
            session = self._get_session()
            user = session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return {'success': False, 'message': '用户不存在'}
            
            # 更新允许的字段
            allowed_fields = ['name', 'age', 'email', 'major', 'school', 'introduction', 'gender']
            
            for field in allowed_fields:
                if field in profile_data:
                    setattr(user, field, profile_data[field])
            
            # 如果更新邮箱或手机号，检查唯一性
            if 'email' in profile_data:
                existing = session.query(User).filter(
                    User.email == profile_data['email'],
                    User.id != user_id
                ).first()
                if existing:
                    return {'success': False, 'message': '邮箱已被使用'}
            
            if 'telephone' in profile_data:
                existing = session.query(User).filter(
                    User.telephone == profile_data['telephone'],
                    User.id != user_id
                ).first()
                if existing:
                    return {'success': False, 'message': '手机号已被使用'}
                user.telephone = profile_data['telephone']
            
            session.commit()
            print(f"✅ 用户资料更新成功: {user.name}")
            
            return {'success': True, 'message': '资料更新成功', 'user': user}
            
        except IntegrityError as e:
            session.rollback()
            print(f"❌ 用户资料更新失败(唯一性约束): {e}")
            return {'success': False, 'message': '邮箱或手机号已被使用'}
        except Exception as e:
            if session:
                session.rollback()
            print(f"❌ 用户资料更新失败: {e}")
            return {'success': False, 'message': f'更新失败: {str(e)}'}
    
    def change_password(self, user_id, old_password, new_password):
        """修改密码"""
        try:
            session = self._get_session()
            user = session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return {'success': False, 'message': '用户不存在'}
            
            # 检查旧密码
            if user.password and not user.check_password(old_password):
                return {'success': False, 'message': '原密码错误'}
            
            # 设置新密码
            user.set_password(new_password)
            session.commit()
            
            print(f"✅ 用户密码修改成功: {user.name}")
            return {'success': True, 'message': '密码修改成功'}
            
        except Exception as e:
            if session:
                session.rollback()
            print(f"❌ 密码修改失败: {e}")
            return {'success': False, 'message': f'密码修改失败: {str(e)}'}
    
    def record_login(self, user_id, login_method, ip_address=None, identification=None):
        """记录登录日志"""
        try:
            session = self._get_session()
            
            # 生成访问码
            access_code = str(uuid.uuid4())
            
            # 获取IP地址
            if not ip_address:
                ip_address = request.remote_addr if request else 'unknown'
            
            # 生成登录标识
            if not identification:
                identification = hashlib.md5(f"{user_id}{datetime.now()}{ip_address}".encode()).hexdigest()[:16]
            
            login_log = UserLoginLog(
                user_id=user_id,
                login_method=login_method,
                login_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                ip_address=ip_address,
                identification=identification,
                access_code=access_code
            )
            
            session.add(login_log)
            session.commit()
            
            print(f"✅ 登录记录已保存: 用户{user_id}, 方式{login_method}, IP{ip_address}")
            return access_code
            
        except Exception as e:
            if session:
                session.rollback()
            print(f"❌ 登录记录保存失败: {e}")
            return None
    
    def get_user_profile(self, user_id):
        """获取用户资料"""
        try:
            session = self._get_session()
            user = session.query(User).filter_by(id=user_id).first()
            
            if not user:
                return {'success': False, 'message': '用户不存在'}
            
            # 转换为字典，排除敏感信息
            user_data = {
                'id': user.id,
                'name': user.name,
                'gender': user.gender,
                'telephone': user.telephone,
                'age': user.age,
                'email': user.email,
                'major': user.major,
                'school': user.school,
                'introduction': user.introduction,
                'avater': user.avater
            }
            
            return {'success': True, 'user': user_data}
            
        except Exception as e:
            print(f"❌ 获取用户资料失败: {e}")
            return {'success': False, 'message': f'获取资料失败: {str(e)}'}
    
    def get_login_history(self, user_id, limit=10):
        """获取用户登录历史"""
        try:
            session = self._get_session()
            
            logs = session.query(UserLoginLog).filter_by(user_id=user_id)\
                          .order_by(UserLoginLog.login_time.desc())\
                          .limit(limit).all()
            
            login_history = []
            for log in logs:
                login_history.append({
                    'login_method': log.login_method,
                    'login_time': log.login_time,
                    'ip_address': log.ip_address,
                    'identification': log.identification
                })
            
            return {'success': True, 'history': login_history}
            
        except Exception as e:
            print(f"❌ 获取登录历史失败: {e}")
            return {'success': False, 'message': f'获取历史失败: {str(e)}'}


# 全局用户服务实例
user_service = UserService() 