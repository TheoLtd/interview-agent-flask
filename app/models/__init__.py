# 模型包初始化文件

# 导入所有模型
from .interview_preset import InterviewPresetRecommended
from .user import User, Gender, UserLoginLog

# 导出所有模型类
__all__ = ['InterviewPresetRecommended', 'User', 'Gender', 'UserLoginLog']
