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
        # 'appId': 'db4f89ef',
        # 'appKey': '53aa48c511bcb1cedc81fe7702342e1f',
        # 'appSecret': 'ZDIwNzBiZmVlZmQyNGVkYzE4YWUyMDcx',
        'appId': 'd5dcadda',
        'appKey': '9e826e8908aa5e9b4adb6309d713ef29',
        'appSecret': 'MjhlMzVlOGU1YWJmNTcwNjE0MzNiMDcw',
        'anchorId': 'cnrmkf0e2000000006',
        'vcn': 'x4_panting'
    }

    # API_KEY = "9f638064e25b1ae24d828e89c1b21026"
    # API_SECRET = "Y2VlMWVmZTJkNTJlMWJlYjc0YjJkOTA3"
    # "flow_id": "7341661804480536578"

    SPARK_PRACTICE_API = {
        'host': 'xingchen-api.xf-yun.com',
        'path': '/workflow/v1/chat/completions',
        'api_key': '9f638064e25b1ae24d828e89c1b21026',
        # 'api_key': '253673d89c9e36cba2fb4aa83c30977a',
        'api_secret': 'Y2VlMWVmZTJkNTJlMWJlYjc0YjJkOTA3',
        # 'api_secret': 'ZTE0ZmU1MzNiZjlhNTgxNTExYWU3YTcw',
        'flow_id': '7341661804480536578'
        # 'flow_id': '7347256464096796674'
    }

    RESUME_REFINATION_API = {
        'host': 'xingchen-api.xf-yun.com',
        'path': '/workflow/v1/chat/completions',
        'api_secret': 'YzY0NzEyMDZmNzc5MDdjYTUwNDU5MWZk',
        'api_key': '580f7a3948f1ab7419a281456f4fd8aa',
        'flow_id': '7358336534640013314'
    }

    SPARK_MBTI_API = {
        "api_key": "0a87ff1a9bdeb34ce22139bce83bf698",
        "api_secret": "ZDlkZDJiMjY0OWRjNzkzNTBlYmI5ZTY3",
        'host': 'xingchen-api.xf-yun.com',
        'path': '/workflow/v1/chat/completions',
        "flow_id": "7348687728526802946"
    }

    FACIAL_DETECT_API = {
        'url': "http://api.xf-yun.com/v1/private/{}",
        'server_id': "s67c9c78c",
        'appid': 'db4f89ef',
        'apisecret': 'ZDIwNzBiZmVlZmQyNGVkYzE4YWUyMDcx',
        'apikey': '53aa48c511bcb1cedc81fe7702342e1f',
    }

    MINI_PROGRAM_INFO = {
        'WECHAT_APPID' : "wx08a49c2b8918c480",
        # check the secret
        'WECHAT_SECRET' : "d5b0c6f8e4a3c2e6f4f9e1b8a2c7d4e5",
    }

    SPUG_API = {
        'ID' : 'My5R7m0knl8V2DgG'
    }

    # Redis配置
    REDIS_CONFIG = {
        'enabled': os.environ.get('REDIS_ENABLED', 'false').lower() == 'true',  # 默认不启用Redis
        'host': os.environ.get('REDIS_HOST') or 'localhost',
        'port': int(os.environ.get('REDIS_PORT') or 6379),
        'db': int(os.environ.get('REDIS_DB') or 0),
        'password': os.environ.get('REDIS_PASSWORD') or None,
        'decode_responses': True,  # 自动解码响应为字符串
        'socket_connect_timeout': 5,
        'socket_timeout': 5
    }