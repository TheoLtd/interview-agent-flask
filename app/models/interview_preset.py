from app.extensions import db
from sqlalchemy import Column, Integer, String, DECIMAL, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class InterviewPresetRecommended(Base):
    """面试预设推荐表模型"""
    __tablename__ = 'interview_preset_recommended'

    # 主键，自增
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 名称
    name = Column(String(90), nullable=True, comment='名称')

    # 简介
    brief = Column(String(90), nullable=True, comment='简介')

    # 难度等级 (decimal(3,2))
    difficulty = Column(DECIMAL(3, 2), nullable=True, comment='难度等级')

    # 标签
    tags = Column(String(90), nullable=True, comment='标签')

    # 热度 (decimal(3,2))
    heat = Column(DECIMAL(3, 2), nullable=True, comment='热度')

    # 专业
    major = Column(String(255), nullable=True, comment='专业')

    # 意图
    intension = Column(String(255), nullable=True, comment='意图')

    # 职责描述
    responsibility = Column(Text, nullable=True, comment='职责描述')

    def __repr__(self):
        return f'<InterviewPresetRecommended(id={self.id}, name="{self.name}")>'

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'brief': self.brief,
            'difficulty': float(self.difficulty) if self.difficulty else None,
            'tags': self.tags,
            'heat': float(self.heat) if self.heat else None,
            'major': self.major,
            'intension': self.intension,
            'responsibility': self.responsibility
        }

    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(
            name=data.get('name'),
            brief=data.get('brief'),
            difficulty=data.get('difficulty'),
            tags=data.get('tags'),
            heat=data.get('heat'),
            major=data.get('major'),
            intension=data.get('intension'),
            responsibility=data.get('responsibility')
        )