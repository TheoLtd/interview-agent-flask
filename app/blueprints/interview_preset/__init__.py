from flask import Blueprint
from services.interview_preset_service import InterviewPresetService

interview_preset_bp = Blueprint('interview_preset', __name__, url_prefix='/interview_preset')

def get_interview_service():
    return InterviewPresetService()

# 导入路由
from . import routes 