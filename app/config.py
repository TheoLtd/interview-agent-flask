import os


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
    
    # 数字人配置
    AVATER_CONFIG = {
        'url': 'wss://avatar.cn-huadong-1.xf-yun.com/v1/interact',
        'appId': 'db4f89ef',
        'appKey': '53aa48c511bcb1cedc81fe7702342e1f',
        'appSecret': 'ZDIwNzBiZmVlZmQyNGVkYzE4YWUyMDcx',
        'anchorId': 'cnr5dg8n2000000003',
        'vcn': 'x4_xiaozhong'
    }
    
    SPARK_PRACTICE_API = {
        'url': 'https://xingchen-api.xf-yun.com/v1/chat/completions',
        'api_key': '253673d89c9e36cba2fb4aa83c30977a',
        'api_secret': 'ZTE0ZmU1MzNiZjlhNTgxNTExYWU3YTcw',
        'flow_id': '7347256464096796674'
    }