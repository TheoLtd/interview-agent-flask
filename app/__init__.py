from flask import Flask, request
from flask_cors import CORS
from app.blueprints.practice import practice_bp
from app.blueprints.interview import interview_bp
from app.blueprints.interview_preset import interview_preset_bp
from app.blueprints.database import database_bp
import glob
import os
from app.config import Config
from app.extensions import db_manager, db
from app.extensions import close_db
import logging
from logging.config import dictConfig
from datetime import datetime

# 日志配置
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        },
        'access': {
            'format': '%(message)s'
        }
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
        'access_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'log/flask/access.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'access'
        }
    },
    'loggers': {
        'access_logger': {
            'handlers': ['access_file'],
            'level': 'INFO',
            'propagate': False
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


def delete_files_in_folder(folder_path):
    files = glob.glob(os.path.join(folder_path, '*'))
    for f in files:
        if os.path.isfile(f):
            os.remove(f)


def create_app():
    # 创建并配置 Flask 应用程序。
    # 返回:
    #     Flask: 配置好的 Flask 应用程序实例。
    app = Flask(__name__,
                static_folder='../static',
                template_folder='../templates'
                )  # 创建 Flask 应用实例
    
    # # 禁用 werkzeug 默认的日志处理器
    # if not app.debug:
    #     werkzeug_logger = logging.getLogger('werkzeug')
    #     werkzeug_logger.disabled = True

    CORS(app, supports_credentials=True)  # 启用跨源资源共享，并允许携带凭证

    # 从文件读取flask配置
    app.config.from_object(Config)
    
    # 初始化扩展
    db_manager.init_app(app)
    db.init_app(app)

    # 注册蓝图
    app.register_blueprint(practice_bp)  # 注册 practice 蓝图
    app.register_blueprint(interview_bp)  # 注册 interview 蓝图
    app.register_blueprint(interview_preset_bp)  # 注册 interview_preset 蓝图
    app.register_blueprint(database_bp)  # 注册 database 蓝图

    # 为特定路由添加文件日志记录，并阻止在终端输出
    access_logger = logging.getLogger('access_logger')

    @app.after_request
    def log_and_silence_noisy_requests(response):
        # 定义需要重定向日志的路由
        noisy_paths = ('/interview/image_detect', '/interview/del_wss')
        
        if request.path.startswith('/interview/video/') or request.path in noisy_paths:
            # 1. 将日志记录到文件
            access_logger.info(
                f'{request.remote_addr} - - '
                f'[{datetime.now().strftime("%d/%b/%Y %H:%M:%S")}] '
                f'"{request.method} {request.path} {request.environ.get("SERVER_PROTOCOL")}" '
                f'{response.status_code} -'
            )
            # 2. 阻止 Werkzeug 默认日志器输出到终端
            request.environ['werkzeug.log_request'] = lambda *args, **kwargs: None
        return response

    # 删除指定文件夹中的文件
    # 后续如果对接数据库就不需要进行删除
    delete_files_in_folder('resource/stream')  # 删除 stream 文件夹中的文件
    delete_files_in_folder('resource/face_image')  # 删除 face_image 文件夹中的文件
    
    # 注册关闭数据库连接的钩子
    app.teardown_appcontext(close_db)
    
    return app  # 返回配置好的应用实例