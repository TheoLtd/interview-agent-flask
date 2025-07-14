from flask import render_template, request, jsonify, redirect, url_for
from app.blueprints.database import database_bp, get_db_service


@database_bp.route('/')
def index():
    """首页 - 重定向到数据库管理器"""
    return redirect(url_for('database.manager'))


@database_bp.route('/manageserver')
def manager():
    """数据库管理器页面"""
    try:
        db_service = get_db_service()
        tables = db_service.get_tables()
        
        # # 添加调试信息
        # print(f"DEBUG: 获取到 {len(tables)} 个表")
        # for table in tables:
        #     print(f"DEBUG: 表名: {table[0]}")
        
        return render_template('database_manager.html', tables=tables)
    except Exception as e:
        print(f"ERROR: 数据库管理器页面错误: {e}")
        # import traceback
        # traceback.print_exc()
        return f"Error:数据库管理器页面错误: {str(e)}"

@database_bp.route('/api/tables/<table_name>')
def get_table_data(table_name):
    """获取表数据API"""
    db_service = get_db_service()
    return jsonify(db_service.get_table_data(table_name, request.args))

@database_bp.route('/api/table-structure/<table_name>')
def get_table_structure(table_name):
    """获取表结构API"""
    db_service = get_db_service()
    return jsonify(db_service.get_table_structure(table_name))

@database_bp.route('/api/insert/<table_name>', methods=['POST'])
def insert_record(table_name):
    """插入记录API"""
    data = request.get_json()
    db_service = get_db_service()
    return jsonify(db_service.insert_record(
        table_name, 
        data['columns'], 
        data['values']
    ))

@database_bp.route('/api/update/<table_name>', methods=['POST'])
def update_record(table_name):
    """更新记录API"""
    data = request.get_json()
    db_service = get_db_service()
    return jsonify(db_service.update_record(
        table_name,
        data['set_clause'],
        data['where_clause'],
        data['values']
    ))

@database_bp.route('/api/delete/<table_name>', methods=['POST'])
def delete_record(table_name):
    """删除记录API"""
    data = request.get_json()
    db_service = get_db_service()
    return jsonify(db_service.delete_record(
        table_name,
        data['where_clause'],
        data['values']
    ))

@database_bp.route('/api/batch-insert/<table_name>', methods=['POST'])
def batch_insert_record(table_name):
    """批量插入记录API"""
    data = request.get_json()
    db_service = get_db_service()
    return jsonify(db_service.batch_insert_record(
        table_name,
        data['columns'],
        data['data']
    ))