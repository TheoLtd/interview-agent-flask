from app.extensions import db
from sqlalchemy import Column, Integer, String, DECIMAL, Text
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()

class Gender(Base):
    '''性别表'''
    __tablename__ = 'gender'
    id  = Column(Integer, autoincrement=True, primary_key=True, comment='性别ID')
    name = Column(String(10), nullable=False, comment='性别名称')

    def __repr__(self):
        return f'<Gender(id={self.id}, name="{self.name}")>'

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(
            name=data.get('name')
        )


class User(Base):
    """用户模型"""
    __tablename__ = 'user'
    id = Column(Integer, autoincrement=True, primary_key=True, comment='用户ID')
    name = Column(String(10), nullable=False, comment='用户名')
    gender = Column(Integer, comment='性别ID')
    telephone = Column(String(20), unique=True, comment='电话号码', index=True)
    weixin_id = Column(String(30), unique=True, comment='微信ID', index=True)
    age = Column(Integer, comment='年龄')
    email = Column(String(40), unique=True, comment='电子邮箱', index=True)
    major = Column(String(10), comment='专业')
    school = Column(String(10), comment='学校')
    password = Column(String(256), comment='密码')
    introduction = Column(String(30), comment='个人简介')
    avater = Column(String(100), comment='头像URL')

    def __repr__(self):
        return f'<User(id={self.id}, name="{self.name}")>'

    def set_password(self, password):
        """设置用户密码"""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """检查用户密码"""
        return check_password_hash(self.password, password)

    @classmethod
    def from_dict(cls, data):
        """从字典创建用户实例"""
        return cls(
            name = data.get('name'),
            gender = data.get('gender', None),
            telephone = data.get('telephone', None),
            weixin_id = data.get('weixin_id'),
            age = data.get('age'),
            email = data.get('email'),
            major = data.get('major'),
            school = data.get('school'),
            password = data.get('password'),
            introduction = data.get('introduction'),
            avater = data.get('avater')
        )


class UserLoginLog(Base):
    """用户登录日志模型"""
    __tablename__ = 'user_login_log'
    id = Column(Integer, autoincrement=True, primary_key=True, comment='日志ID')
    user_id = Column(Integer, nullable=False, comment='用户ID')
    login_method = Column(String(5), nullable=False, comment='登录方式')
    login_time = Column(String(50), nullable=False, comment='登录时间')
    ip_address = Column(String(128), nullable=False, comment='IP地址')
    identification = Column(String(40), nullable=False, comment='登录渠道标识')
    access_code = Column(String(40), nullable=False, comment='访问码')


    def __repr__(self):
        return f'<UserLoginLog(id={self.id}, user_id={self.user_id}, login_method="{self.login_method}, login_time="{self.login_time}, ip_address="{self.ip_address}, identification="{self.identification}, access_code="{self.access_code}")>'

