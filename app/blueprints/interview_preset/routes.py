from flask import request, jsonify
from app.blueprints.interview_preset import interview_preset_bp, get_interview_service
import random

@interview_preset_bp.route('/api/presets')
def get_presets():
    """获取所有面试预设"""
    service = get_interview_service()

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')

    result = service.get_all_presets(page=page, per_page=per_page, search=search)
    return jsonify(result)

@interview_preset_bp.route('/api/presets/<int:preset_id>')
def get_preset(preset_id):
    """获取单个面试预设"""
    service = get_interview_service()
    result = service.get_preset_by_id(preset_id)

    if result:
        return jsonify(result)
    else:
        return jsonify({'error': '面试预设不存在'}), 404

@interview_preset_bp.route('/api/presets', methods=['POST'])
def create_preset():
    """创建新的面试预设"""
    service = get_interview_service()
    data = request.get_json()

    result = service.create_preset(data)
    return jsonify(result)

@interview_preset_bp.route('/api/presets/<int:preset_id>', methods=['PUT'])
def update_preset(preset_id):
    """更新面试预设"""
    service = get_interview_service()
    data = request.get_json()

    result = service.update_preset(preset_id, data)
    return jsonify(result)

@interview_preset_bp.route('/api/presets/<int:preset_id>', methods=['DELETE'])
def delete_preset(preset_id):
    """删除面试预设"""
    service = get_interview_service()

    result = service.delete_preset(preset_id)
    return jsonify(result)

@interview_preset_bp.route('/api/presets/major/<major>')
def get_presets_by_major(major):
    """根据专业获取面试预设"""
    service = get_interview_service()
    result = service.get_presets_by_major(major)
    return jsonify(result)

@interview_preset_bp.route('/api/presets/random_some')
def get_presets_random_some_default():
    """获取默认数量的随机面试预设（默认3个）"""
    service = get_interview_service()
    result = service.get_random_presets(3)
    
    # 检查是否有错误
    if isinstance(result, dict) and 'error' in result:
        return jsonify(result), 500
    
    return jsonify(result)

@interview_preset_bp.route('/api/presets/random_some/<int:num>')
def get_presets_random_some(num):
    """获取指定数量的随机面试预设"""
    service = get_interview_service()
    
    # 验证参数
    if num <= 0:
        return jsonify({'error': '数量必须大于0'}), 400
    
    
    result = service.get_random_presets(num)
    
    # 检查是否有错误
    if isinstance(result, dict) and 'error' in result:
        return jsonify(result), 500
    
    return jsonify(result)

@interview_preset_bp.route('/api/presets/search')
def search_presets_by_name():
    """根据面试岗位名称进行模糊搜索"""
    service = get_interview_service()
    
    # 获取查询参数
    keyword = request.args.get('keyword', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 验证参数
    if not keyword or keyword.strip() == '':
        return jsonify({'error': '搜索关键词不能为空'}), 400
    
    # 限制搜索关键词长度
    if len(keyword) > 50:
        return jsonify({'error': '搜索关键词长度不能超过50个字符'}), 400
    
    # 限制每页数量
    if per_page > 100:
        per_page = 100
    
    result = service.search_presets_by_name(keyword.strip(), page, per_page)
    
    # 检查是否有错误
    if isinstance(result, dict) and 'error' in result:
        return jsonify(result), 500
    
    return jsonify(result)
    

@interview_preset_bp.route('/api/presets/suggest')
def suggest_presets():
    """根据输入内容返回预设名称联想推荐"""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'suggestions': []})
    service = get_interview_service()
    suggestions = service.get_suggestions(q, limit=5)
    return jsonify({'suggestions': suggestions})
    