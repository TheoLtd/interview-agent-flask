from flask import Blueprint, g

interview_bp = Blueprint('interview', __name__, url_prefix='/interview')

# TODO: wsclient 是一个全局状态，这在并发环境下会导致严重问题。
#  如果多个用户同时开始面试，后一个用户的连接会覆盖前一个。
#  正确的做法是为每个用户会话（或WebSocket连接）管理一个独立的客户端实例，
#  而不是使用单个全局实例。
wsclient = None

# 在蓝图定义后导入路由
from . import routes
