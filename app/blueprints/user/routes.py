from flask import request, jsonify, Response
import time
import os
from . import user_bp
from services.SpugMessage import SpugMessage
from services.VerificationCodeService import verification_service
from services.UserService import user_service

@user_bp.route('/login/getSendMessage', methods=['GET'])
def get_send_message():
    try:
        # 从query参数获取手机号
        phone = request.args.get('phoneNumber')
        if not phone:
            return jsonify({"success": False, "message": "手机号不能为空", "code": 400}), 400
        
        message = SpugMessage(phone)
        result = message.send_message()
        
        print(f"SpugMessage返回结果: {result}")
        
        if result and result.get('status') == 'success':
            return jsonify({"success": True, "message": "验证码发送成功", "code": 200})
        else:
            error_msg = result.get('message', '发送失败') if result else '发送失败'
            print(f"❌ 短信发送失败: {error_msg}")
            return jsonify({"success": False, "message": error_msg, "code": 500})
            
    except Exception as e:
        print(f"发送短信验证码失败: {str(e)}")
        return jsonify({"success": False, "message": "服务器内部错误", "code": 500}), 500


@user_bp.route('/login/postCodeVerify', methods=['GET'])
def verify_code():
    try:
        # 从query参数获取验证码和手机号
        code = request.args.get('code')
        phone = request.args.get('phoneNumber')
        
        if not code:
            return jsonify({"success": False, "message": "验证码不能为空", "code": 400}), 400
        
        if not phone:
            return jsonify({"success": False, "message": "手机号不能为空", "code": 400}), 400
        
        # 验证码验证
        verify_result = verification_service.verify_code(phone, code, code_type="sms")
        # debug code
        print(f"🔍 验证结果: {verify_result}")
        
        if verify_result['success']:
            # 手机号验证成功，创建或获取用户
            user = user_service.create_or_get_user_by_phone(phone)
            if not user:
                return jsonify({
                    "success": False,
                    "message": "用户创建失败",
                    "code": 500
                }), 500
            
            # 生成JWT token
            token = user_service.generate_jwt_token(user.id)
            if not token:
                return jsonify({
                    "success": False,
                    "message": "Token生成失败",
                    "code": 500
                }), 500
            
            # 记录登录日志
            user_service.record_login(user.id, "SMS", request.remote_addr)
            
            return jsonify({
                "success": True,
                "message": "登录成功",
                "data": {
                    "token": token,
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "telephone": user.telephone
                    }
                },
                "code": 200
            })
        else:
            # 根据不同的错误码返回相应的HTTP状态码
            http_status = 400
            if verify_result.get('code') == 'TOO_MANY_ATTEMPTS':
                http_status = 429
            elif verify_result.get('code') in ['CODE_NOT_EXISTS', 'CODE_EXPIRED']:
                http_status = 410  # Gone
            
            return jsonify({
                "success": False,
                "message": verify_result['message'],
                "code": http_status,
                "error_code": verify_result.get('code'),
                "remaining_attempts": verify_result.get('remaining_attempts')
            }), http_status
            
    except Exception as e:
        print(f"验证码验证失败: {str(e)}")
        return jsonify({"success": False, "message": "服务器内部错误", "code": 500}), 500


@user_bp.route('/login/postPasswordLogin', methods=['POST'])
def password_login():
    """账号密码登录"""
    try:
        data = request.get_json()
        if not data or 'data' not in data:
            return jsonify({"success": False, "message": "请求数据格式错误", "code": 400}), 400
        
        login_data = data['data']
        account = login_data.get('account')
        password = login_data.get('password')
        
        print(f"🔍 收到密码登录请求: 账号={account}")
        
        if not account or not password:
            return jsonify({"success": False, "message": "账号和密码不能为空", "code": 400}), 400
        
        # 用户认证
        user = user_service.authenticate_user(account, password)
        if not user:
            return jsonify({"success": False, "message": "账号或密码错误", "code": 401}), 401
        
        # 生成JWT token
        token = user_service.generate_jwt_token(user.id)
        if not token:
            return jsonify({"success": False, "message": "Token生成失败", "code": 500}), 500
        
        # 记录登录日志
        user_service.record_login(user.id, "PWD", request.remote_addr)
        
        return jsonify({
            "success": True,
            "message": "登录成功",
            "data": {
                "token": token,
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "telephone": user.telephone,
                    "email": user.email
                }
            },
            "code": 200
        })
        
    except Exception as e:
        print(f"密码登录失败: {str(e)}")
        return jsonify({"success": False, "message": "服务器内部错误", "code": 500}), 500


@user_bp.route('/api/wechat/login', methods=['POST'])
def wechat_login():
    """微信登录"""
    try:
        data = request.get_json()
        code = data.get('code') if data else None
        
        print(f"🔍 收到微信登录请求: code={code}")
        
        if not code:
            return jsonify({"code": -1, "msg": "微信授权码不能为空"}), 400
        
        # 微信登录处理
        result = user_service.wechat_login(code)
        
        if not result['success']:
            return jsonify({"code": -1, "msg": result['message']}), 400
        
        user = result['user']
        openid = result['openid']
        session_key = result['session_key']
        
        # 记录登录日志
        user_service.record_login(user.id, "WX", request.remote_addr)
        
        return jsonify({
            "code": 0,
            "msg": "登录成功",
            "openid": openid,
            "session_key": session_key,
            "user": {
                "id": user.id,
                "name": user.name,
                "weixin_id": user.weixin_id
            }
        })
        
    except Exception as e:
        print(f"微信登录失败: {str(e)}")
        return jsonify({"code": -1, "msg": f"微信登录异常: {str(e)}"}), 500


def verify_token(f):
    """Token验证装饰器"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"success": False, "message": "缺少认证token", "code": 401}), 401
        
        token = auth_header.split(' ')[1]
        payload = user_service.verify_jwt_token(token)
        
        if 'error' in payload:
            return jsonify({"success": False, "message": payload['error'], "code": 401}), 401
        
        # 将用户ID传递给路由函数
        request.current_user_id = payload['user_id']
        return f(*args, **kwargs)
    
    return decorated_function


@user_bp.route('/user/profile', methods=['GET'])
@verify_token
def get_user_profile():
    """获取用户资料"""
    try:
        user_id = request.current_user_id
        result = user_service.get_user_profile(user_id)
        
        if result['success']:
            return jsonify({
                "success": True,
                "data": result['user'],
                "code": 200
            })
        else:
            return jsonify({
                "success": False,
                "message": result['message'],
                "code": 404
            }), 404
            
    except Exception as e:
        print(f"获取用户资料失败: {str(e)}")
        return jsonify({"success": False, "message": "服务器内部错误", "code": 500}), 500


@user_bp.route('/user/profile', methods=['PUT'])
@verify_token
def update_user_profile():
    """更新用户资料"""
    try:
        user_id = request.current_user_id
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "请求数据不能为空", "code": 400}), 400
        
        print(f"🔍 更新用户资料: 用户{user_id}, 数据={data}")
        
        result = user_service.update_user_profile(user_id, data)
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": result['message'],
                "code": 200
            })
        else:
            return jsonify({
                "success": False,
                "message": result['message'],
                "code": 400
            }), 400
            
    except Exception as e:
        print(f"更新用户资料失败: {str(e)}")
        return jsonify({"success": False, "message": "服务器内部错误", "code": 500}), 500


@user_bp.route('/user/password', methods=['PUT'])
@verify_token
def change_password():
    """修改密码"""
    try:
        user_id = request.current_user_id
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "请求数据不能为空", "code": 400}), 400
        
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not new_password:
            return jsonify({"success": False, "message": "新密码不能为空", "code": 400}), 400
        
        print(f"🔍 修改密码: 用户{user_id}")
        
        result = user_service.change_password(user_id, old_password, new_password)
        
        if result['success']:
            return jsonify({
                "success": True,
                "message": result['message'],
                "code": 200
            })
        else:
            return jsonify({
                "success": False,
                "message": result['message'],
                "code": 400
            }), 400
            
    except Exception as e:
        print(f"修改密码失败: {str(e)}")
        return jsonify({"success": False, "message": "服务器内部错误", "code": 500}), 500


@user_bp.route('/user/login-history', methods=['GET'])
@verify_token
def get_login_history():
    """获取登录历史"""
    try:
        user_id = request.current_user_id
        limit = request.args.get('limit', 10, type=int)
        
        result = user_service.get_login_history(user_id, limit)
        
        if result['success']:
            return jsonify({
                "success": True,
                "data": result['history'],
                "code": 200
            })
        else:
            return jsonify({
                "success": False,
                "message": result['message'],
                "code": 404
            }), 404
            
    except Exception as e:
        print(f"获取登录历史失败: {str(e)}")
        return jsonify({"success": False, "message": "服务器内部错误", "code": 500}), 500


@user_bp.route('/user/register', methods=['POST'])
def register_user():
    """用户注册"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "请求数据不能为空", "code": 400}), 400
        
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        telephone = data.get('telephone')
        
        if not all([name, email, password]):
            return jsonify({"success": False, "message": "姓名、邮箱和密码不能为空", "code": 400}), 400
        
        print(f"🔍 用户注册: 姓名={name}, 邮箱={email}")
        
        # 检查邮箱是否已存在
        from app.extensions import get_session
        from app.models.user import User
        
        session = get_session()
        existing_user = session.query(User).filter(
            (User.email == email) | (User.name == name)
        ).first()
        
        if existing_user:
            return jsonify({"success": False, "message": "用户名或邮箱已存在", "code": 409}), 409
        
        # 创建新用户
        new_user = User(
            name=name,
            email=email,
            telephone=telephone,
            introduction="这个人很懒，什么都没有留下~"
        )
        new_user.set_password(password)
        
        # 添加其他字段
        for field in ['age', 'major', 'school', 'gender']:
            if field in data:
                setattr(new_user, field, data[field])
        
        session.add(new_user)
        session.commit()
        
        print(f"✅ 用户注册成功: {new_user.name}")
        
        # 生成token
        token = user_service.generate_jwt_token(new_user.id)
        
        # 记录登录日志
        user_service.record_login(new_user.id, "REG", request.remote_addr)
        
        return jsonify({
            "success": True,
            "message": "注册成功",
            "data": {
                "token": token,
                "user": {
                    "id": new_user.id,
                    "name": new_user.name,
                    "email": new_user.email,
                    "telephone": new_user.telephone
                }
            },
            "code": 200
        })
        
    except Exception as e:
        print(f"用户注册失败: {str(e)}")
        return jsonify({"success": False, "message": "服务器内部错误", "code": 500}), 500


@user_bp.route('/debug/verification/<phone_number>', methods=['GET'])
def debug_verification(phone_number):
    """调试验证码存储状态"""
    try:
        key = f"verification_code:sms:{phone_number}"
        
        # 检查内存存储
        memory_data = verification_service.memory_storage.get(key)
        
        # 检查Redis（如果可用）
        redis_data = None
        redis_client = verification_service._get_redis_client()
        if redis_client and verification_service.redis_manager.is_available():
            redis_data = redis_client.get(key)
        
        return jsonify({
            "phone_number": phone_number,
            "storage_key": key,
            "memory_data": memory_data,
            "redis_data": redis_data,
            "all_memory_keys": list(verification_service.memory_storage.keys()),
            "redis_available": redis_client is not None and verification_service.redis_manager.is_available()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
