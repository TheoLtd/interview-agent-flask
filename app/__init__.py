from flask import Flask
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
    CORS(app)  # 启用跨源资源共享

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

    # 删除指定文件夹中的文件
    # 后续如果对接数据库就不需要进行删除
    delete_files_in_folder('resource/stream')  # 删除 stream 文件夹中的文件
    delete_files_in_folder('resource/face_image')  # 删除 face_image 文件夹中的文件
    
    # 注册关闭数据库连接的钩子
    app.teardown_appcontext(close_db)
    
    return app  # 返回配置好的应用实例