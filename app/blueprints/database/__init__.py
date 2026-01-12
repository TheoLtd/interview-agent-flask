from flask import Blueprint

database_bp = Blueprint('database', __name__, url_prefix='/db')

# 延迟创建服务实例s
def get_db_service():
    from services.database_service import DatabaseService
    return DatabaseService()

# 导入路由
from . import routes