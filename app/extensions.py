import pymysql
import redis
from flask import g, current_app
from DBUtils.PooledDB import PooledDB
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from flask_sqlalchemy import SQLAlchemy

# 创建SQLAlchemy实例
db = SQLAlchemy()

# Redis连接池
redis_client = None

class DatabaseManager:
    def __init__(self):
        self.pool = None
        self.engine = None
        self.session_factory = None
        self._initialized = False
    
    def init_app(self, app):
        """初始化数据库连接池"""
        config = app.config['PYMYSQL_CONFIG']
        
        # 创建PyMySQL连接池
        self.pool = PooledDB(
            creator=pymysql,
            maxconnections=20,
            mincached=2,
            maxcached=5,
            maxshared=3,
            blocking=True,
            maxusage=None,
            setsession=[],
            ping=1,  # 启用连接检查，1表示每次使用前检查连接
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config.get('database', 'interview'),
            charset=config['charset'],
            autocommit=True
        )
        
        # 创建SQLAlchemy引擎
        db_url = f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config.get('database', '')}?charset={config['charset']}"
        
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # 每次连接前检查连接是否有效
            pool_recycle=1800,   # 减少连接回收时间到30分钟
            pool_timeout=30,     # 获取连接的超时时间
            echo=False           # 生产环境关闭SQL日志
        )
        
        # 创建会话工厂
        self.session_factory = sessionmaker(bind=self.engine)
        
        # 检查interview数据库是否存在
        self._check_interview_database(app)
        
        self._initialized = True
    
    def _check_interview_database(self, app):
        """检查interview数据库是否存在，不存在则创建"""
        try:
            # 先连接到MySQL服务器（不指定数据库）
            temp_config = app.config['PYMYSQL_CONFIG'].copy()
            temp_config.pop('database', None)
            
            with pymysql.connect(**temp_config) as conn:
                with conn.cursor() as cursor:
                    # 检查interview数据库是否存在
                    cursor.execute("SHOW DATABASES LIKE 'interview'")
                    result = cursor.fetchone()
                    
                    if not result:
                        print("❌ 数据库 'interview' 不存在")
                        # 创建interview数据库
                        cursor.execute("CREATE DATABASE interview CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                        print("✅ 数据库 'interview' 创建成功")
                    else:
                        print("✅ 数据库 'interview' 已存在")
                        
        except Exception as e:
            print(f"❌ 检查数据库时出错: {e}")
            raise
    
    def get_connection(self):
        """获取PyMySQL连接"""
        if not self._initialized:
            raise RuntimeError("DatabaseManager not initialized")
        return self.pool.connection()
    
    def get_connection_context(self):
        if not self._initialized:
            raise RuntimeError("DatabaseManager not initialized")
        return self.pool.connection()
    
    def get_session(self):
        """获取SQLAlchemy会话"""
        if not self._initialized:
            raise RuntimeError("DatabaseManager not initialized")
        return self.session_factory()
    
    def execute_raw_sql(self, sql, params=None):
        """执行原始SQL查询"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params or ())
                return cursor.fetchall()
    
    def execute_raw_sql_with_result(self, sql, params=None):
        """执行原始SQL查询并返回结果"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params or ())
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                return {'columns': columns, 'rows': rows}

# 全局数据库管理器实例
db_manager = DatabaseManager()

def get_db():
    """获取数据库连接（Flask g对象）"""
    if 'db' not in g:
        g.db = db_manager.get_connection()
    return g.db

def get_session():
    """获取SQLAlchemy会话（Flask g对象）"""
    if 'session' not in g:
        g.session = db_manager.get_session()
    return g.session

def close_db(e=None):
    """关闭数据库连接"""
    db = g.pop('db', None)
    if db is not None:
        db.close()
    
    session = g.pop('session', None)
    if session is not None:
        session.close()

class RedisManager:
    """Redis管理器"""
    def __init__(self):
        self.client = None
        self._initialized = False
    
    def init_app(self, app):
        """初始化Redis连接"""
        config = app.config['REDIS_CONFIG']
        
        # 检查是否启用Redis
        if not config.get('enabled', False):
            print("⚠️ Redis已禁用，将使用内存存储")
            self.client = None
            self._initialized = False
            return
            
        try:
            self.client = redis.Redis(
                host=config['host'],
                port=config['port'],
                db=config['db'],
                password=config['password'],
                decode_responses=config['decode_responses'],
                socket_connect_timeout=config['socket_connect_timeout'],
                socket_timeout=config['socket_timeout'],
                connection_pool=redis.ConnectionPool(
                    host=config['host'],
                    port=config['port'],
                    db=config['db'],
                    password=config['password'],
                    decode_responses=config['decode_responses'],
                    max_connections=20
                )
            )
            
            # 测试连接
            self.client.ping()
            print("✅ Redis连接成功")
            self._initialized = True
            
        except Exception as e:
            print(f"❌ Redis连接失败: {e}")
            print("⚠️ 将使用内存存储作为后备方案")
            self.client = None
            self._initialized = False
    
    def get_client(self):
        """获取Redis客户端"""
        return self.client
    
    def is_available(self):
        """检查Redis是否可用"""
        return self._initialized and self.client is not None

# 全局Redis管理器实例
redis_manager = RedisManager()

def get_redis():
    """获取Redis客户端"""
    return redis_manager.get_client()

def init_extensions(app):
    """初始化所有扩展"""
    # 初始化数据库
    db_manager.init_app(app)
    db.init_app(app)
    
    # 初始化Redis
    redis_manager.init_app(app)
