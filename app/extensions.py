import pymysql
from flask import g, current_app
from DBUtils.PooledDB import PooledDB
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from flask_sqlalchemy import SQLAlchemy

# 创建SQLAlchemy实例
db = SQLAlchemy()

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
            ping=0,
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
            pool_pre_ping=True,
            pool_recycle=3600
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
        """获取支持上下文管理器的PyMySQL连接"""
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
