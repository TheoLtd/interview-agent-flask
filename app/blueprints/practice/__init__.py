from flask import Blueprint

practice_bp = Blueprint('practice', __name__, url_prefix='/practice')

# 在蓝图定义后导入路由
from . import routes