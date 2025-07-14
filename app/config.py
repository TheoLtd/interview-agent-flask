import os


PYMYSQL_CONFIG={
    'host': 'localhost',
    'port': 3306,
    'user': 'nobody',
    'password': '0000',
    'database': 'interview',
    'charset': 'utf8mb4'
}

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key'
    
    # 数据库连接配置
    PYMYSQL_CONFIG = {
        'host': 'localhost',
        'port': 3306,
        'user': 'nobody',
        'password': '0000',
        'database': 'interview',
        'charset': 'utf8mb4'
    }
    
    # SQLAlchemy配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://nobody:0000@localhost/interview?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_pre_ping': True,
        'pool_recycle': 3600
    }

    # 面试相关文件夹路径配置
    UPLOAD_FOLDER_FACE_ROUTE = 'resource/face_image/'
    HLS_FOLDER_FILE          = 'resource/stream/playlist.m3u8'
    FEEDBACK_FOLDER_ROUTE    = 'resource/feedback/'

    # 面部表情标签
    FACIAL_EXPRESSION_LABEL = [
        "其他(非人脸表情图片)", "其他表情", "喜悦", "愤怒",
        "悲伤", "惊恐", "厌恶", "中性"
    ]