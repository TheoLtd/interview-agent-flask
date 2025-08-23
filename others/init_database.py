"""
数据库初始化脚本
创建用户相关的数据库表
"""

from app import create_app
from app.models.user import Base, User, Gender, UserLoginLog
from sqlalchemy import create_engine

def init_database():
    """初始化数据库表"""
    app = create_app()
    
    with app.app_context():
        # 获取数据库配置
        config = app.config['PYMYSQL_CONFIG']
        
        # 创建数据库引擎
        db_url = f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?charset={config['charset']}"
        engine = create_engine(db_url)
        
        print("🔧 正在创建数据库表...")
        
        # 创建所有表
        Base.metadata.create_all(engine)
        
        print("✅ 数据库表创建完成！")
        
        # 初始化性别数据
        init_gender_data(engine)

def init_gender_data(engine):
    """初始化性别数据"""
    try:
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 检查是否已有性别数据
        existing = session.query(Gender).first()
        if existing:
            print("✅ 性别数据已存在，跳过初始化")
            session.close()
            return
        
        # 添加性别数据
        genders = [
            Gender(name='未知'),
            Gender(name='男'),
            Gender(name='女'),
            Gender(name='其他')
        ]
        
        for gender in genders:
            session.add(gender)
        
        session.commit()
        session.close()
        
        print("✅ 性别数据初始化完成")
        
    except Exception as e:
        print(f"❌ 性别数据初始化失败: {e}")

if __name__ == "__main__":
    init_database() 