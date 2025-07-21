from flask import current_app
from app.extensions import db_manager
from app.models import InterviewPresetRecommended
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

class InterviewPresetService:
    """面试预设服务类"""
    
    def __init__(self):
        self.config = current_app.config['PYMYSQL_CONFIG']
    
    def get_all_presets(self, page=1, per_page=10, search=None):
        """获取所有面试预设（支持分页和搜索）"""
        conn = None
        try:
            conn = db_manager.get_connection_context()
            with conn.cursor() as cursor:
                cursor.execute("USE interview")
                
                # 构建查询条件
                where_clause = ""
                query_params = []
                
                if search:
                    search_conditions = [
                        "name LIKE %s",
                        "brief LIKE %s", 
                        "tags LIKE %s",
                        "major LIKE %s",
                        "intension LIKE %s",
                        "responsibility LIKE %s"
                    ]
                    where_clause = f"WHERE {' OR '.join(search_conditions)}"
                    query_params.extend([f"%{search}%"] * len(search_conditions))
                
                # 获取总记录数
                count_sql = "SELECT COUNT(*) FROM interview_preset_recommended"
                if where_clause:
                    count_sql += f" {where_clause}"
                
                cursor.execute(count_sql, query_params)
                total_records = cursor.fetchone()[0]
                
                # 计算分页信息
                total_pages = (total_records + per_page - 1) // per_page
                offset = (page - 1) * per_page
                
                # 获取分页数据
                data_sql = "SELECT * FROM interview_preset_recommended"
                if where_clause:
                    data_sql += f" {where_clause}"
                data_sql += f" ORDER BY id DESC LIMIT {per_page} OFFSET {offset}"
                
                cursor.execute(data_sql, query_params)
                rows = cursor.fetchall()
                
                # 转换为字典格式
                columns = ['id', 'name', 'brief', 'difficulty', 'tags', 'heat', 'major', 'intension', 'responsibility']
                result = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    # 处理decimal类型
                    if row_dict['difficulty'] is not None:
                        row_dict['difficulty'] = float(row_dict['difficulty'])
                    if row_dict['heat'] is not None:
                        row_dict['heat'] = float(row_dict['heat'])
                    result.append(row_dict)
                
                return {
                    'data': result,
                    'pagination': {
                        'current_page': page,
                        'per_page': per_page,
                        'total_records': total_records,
                        'total_pages': total_pages
                    },
                    'search': search
                }
                
        except Exception as e:
            current_app.logger.error(f"获取面试预设失败: {e}")
            return {'error': str(e)}
        finally:
            if conn:
                conn.close()
    
    def get_preset_by_id(self, preset_id):
        """根据ID获取面试预设"""
        conn = None
        try:
            conn = db_manager.get_connection_context()
            with conn.cursor() as cursor:
                cursor.execute("USE interview")
                cursor.execute(
                    "SELECT * FROM interview_preset_recommended WHERE id = %s",
                    (preset_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    columns = ['id', 'name', 'brief', 'difficulty', 'tags', 'heat', 'major', 'intension', 'responsibility']
                    result = dict(zip(columns, row))
                    # 处理decimal类型
                    if result['difficulty'] is not None:
                        result['difficulty'] = float(result['difficulty'])
                    if result['heat'] is not None:
                        result['heat'] = float(result['heat'])
                    return result
                return None
                
        except Exception as e:
            current_app.logger.error(f"获取面试预设失败: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def create_preset(self, data):
        """创建新的面试预设"""
        conn = None
        try:
            conn = db_manager.get_connection_context()
            with conn.cursor() as cursor:
                cursor.execute("USE interview")
                
                sql = """
                INSERT INTO interview_preset_recommended 
                (name, brief, difficulty, tags, heat, major, intension, responsibility)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                values = (
                    data.get('name'),
                    data.get('brief'),
                    data.get('difficulty'),
                    data.get('tags'),
                    data.get('heat'),
                    data.get('major'),
                    data.get('intension'),
                    data.get('responsibility')
                )
                
                cursor.execute(sql, values)
                conn.commit()
                
                # 获取新插入记录的ID
                preset_id = cursor.lastrowid
                
                return {
                    'success': True,
                    'message': '面试预设创建成功',
                    'id': preset_id
                }
                
        except Exception as e:
            current_app.logger.error(f"创建面试预设失败: {e}")
            return {'error': str(e)}
        finally:
            if conn:
                conn.close()
    
    def update_preset(self, preset_id, data):
        """更新面试预设"""
        conn = None
        try:
            conn = db_manager.get_connection_context()
            with conn.cursor() as cursor:
                cursor.execute("USE interview")
                
                sql = """
                UPDATE interview_preset_recommended 
                SET name = %s, brief = %s, difficulty = %s, tags = %s, 
                    heat = %s, major = %s, intension = %s, responsibility = %s
                WHERE id = %s
                """
                
                values = (
                    data.get('name'),
                    data.get('brief'),
                    data.get('difficulty'),
                    data.get('tags'),
                    data.get('heat'),
                    data.get('major'),
                    data.get('intension'),
                    data.get('responsibility'),
                    preset_id
                )
                
                cursor.execute(sql, values)
                conn.commit()
                
                return {
                    'success': True,
                    'message': '面试预设更新成功'
                }
                
        except Exception as e:
            current_app.logger.error(f"更新面试预设失败: {e}")
            return {'error': str(e)}
        finally:
            if conn:
                conn.close()
    
    def delete_preset(self, preset_id):
        """删除面试预设"""
        conn = None
        try:
            conn = db_manager.get_connection_context()
            with conn.cursor() as cursor:
                cursor.execute("USE interview")
                cursor.execute(
                    "DELETE FROM interview_preset_recommended WHERE id = %s",
                    (preset_id,)
                )
                conn.commit()
                
                return {
                    'success': True,
                    'message': '面试预设删除成功'
                }
                
        except Exception as e:
            current_app.logger.error(f"删除面试预设失败: {e}")
            return {'error': str(e)}
        finally:
            if conn:
                conn.close()
    
    def get_presets_by_major(self, major):
        """根据专业获取面试预设"""
        conn = None
        try:
            conn = db_manager.get_connection_context()
            with conn.cursor() as cursor:
                cursor.execute("USE interview")
                cursor.execute(
                    "SELECT * FROM interview_preset_recommended WHERE major LIKE %s ORDER BY heat DESC",
                    (f"%{major}%",)
                )
                rows = cursor.fetchall()
                
                columns = ['id', 'name', 'brief', 'difficulty', 'tags', 'heat', 'major', 'intension', 'responsibility']
                result = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    if row_dict['difficulty'] is not None:
                        row_dict['difficulty'] = float(row_dict['difficulty'])
                    if row_dict['heat'] is not None:
                        row_dict['heat'] = float(row_dict['heat'])
                    result.append(row_dict)
                
                return result
                
        except Exception as e:
            current_app.logger.error(f"根据专业获取面试预设失败: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def search_presets_by_name0(self, keyword, page=1, per_page=10):
        """根据面试岗位名称进行模糊搜索"""
        conn = None
        try:
            conn = db_manager.get_connection_context()
            with conn.cursor() as cursor:
                cursor.execute("USE interview")
                
                # 构建搜索条件 - 只针对name字段进行模糊搜索
                where_clause = "WHERE name LIKE %s"
                search_param = f"%{keyword}%"
                
                # 获取总记录数
                count_sql = "SELECT COUNT(*) FROM interview_preset_recommended"
                count_sql += f" {where_clause}"
                
                cursor.execute(count_sql, (search_param,))
                total_records = cursor.fetchone()[0]
                
                # 计算分页信息
                total_pages = (total_records + per_page - 1) // per_page
                offset = (page - 1) * per_page
                
                # 获取分页数据
                data_sql = "SELECT * FROM interview_preset_recommended"
                data_sql += f" {where_clause}"
                data_sql += f" ORDER BY heat DESC, id DESC LIMIT {per_page} OFFSET {offset}"
                
                cursor.execute(data_sql, (search_param,))
                rows = cursor.fetchall()
                
                # 转换为字典格式
                columns = ['id', 'name', 'brief', 'difficulty', 'tags', 'heat', 'major', 'intension', 'responsibility']
                result = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    # 处理decimal类型
                    if row_dict['difficulty'] is not None:
                        row_dict['difficulty'] = float(row_dict['difficulty'])
                    if row_dict['heat'] is not None:
                        row_dict['heat'] = float(row_dict['heat'])
                    result.append(row_dict)
                
                return {
                    'data': result,
                    'pagination': {
                        'current_page': page,
                        'per_page': per_page,
                        'total_records': total_records,
                        'total_pages': total_pages
                    },
                    'search': {
                        'keyword': keyword,
                        'field': 'name'
                    }
                }
                
        except Exception as e:
            current_app.logger.error(f"搜索面试预设失败: {e}")
            return {'error': str(e)}
        finally:
            if conn:
                conn.close()
    
    def search_presets_by_name(self, keyword, page=1, per_page=10):
        """根据面试岗位名称或专业进行模糊搜索"""
        conn = None
        try:
            conn = db_manager.get_connection_context()
            with conn.cursor() as cursor:
                cursor.execute("USE interview")
                where_clause = "WHERE name LIKE %s OR major LIKE %s"
                search_param = f"%{keyword}%"
                count_sql = "SELECT COUNT(*) FROM interview_preset_recommended " + where_clause
                cursor.execute(count_sql, (search_param, search_param))
                total_records = cursor.fetchone()[0]
                total_pages = (total_records + per_page - 1) // per_page
                offset = (page - 1) * per_page
                data_sql = (
                    "SELECT * FROM interview_preset_recommended "
                    + where_clause +
                    " ORDER BY heat DESC, id DESC LIMIT %s OFFSET %s"
                )
                cursor.execute(data_sql, (search_param, search_param, per_page, offset))
                rows = cursor.fetchall()
                columns = ['id', 'name', 'brief', 'difficulty', 'tags', 'heat', 'major', 'intension', 'responsibility']
                result = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    if row_dict['difficulty'] is not None:
                        row_dict['difficulty'] = float(row_dict['difficulty'])
                    if row_dict['heat'] is not None:
                        row_dict['heat'] = float(row_dict['heat'])
                    result.append(row_dict)
                return {
                    'data': result,
                    'pagination': {
                        'current_page': page,
                        'per_page': per_page,
                        'total_records': total_records,
                        'total_pages': total_pages
                    },
                    'search': {
                        'keyword': keyword,
                        'field': 'name_or_major'
                    }
                }
        except Exception as e:
            current_app.logger.error(f"搜索面试预设失败: {e}")
            return {'error': str(e)}
        finally:
            if conn:
                conn.close()
    
    def get_random_presets(self, num=3):
        """获取指定数量的随机面试预设"""
        conn = None
        try:
            conn = db_manager.get_connection_context()
            with conn.cursor() as cursor:
                cursor.execute("USE interview")
                
                # 首先获取总记录数
                cursor.execute("SELECT COUNT(*) FROM interview_preset_recommended")
                total_count = cursor.fetchone()[0]
                
                if total_count == 0:
                    return []
                
                # 如果请求数量大于总记录数，返回所有记录
                if num >= total_count:
                    cursor.execute("SELECT * FROM interview_preset_recommended ORDER BY RAND()")
                else:
                    # 使用RAND()函数随机获取指定数量的记录
                    cursor.execute(
                        "SELECT * FROM interview_preset_recommended ORDER BY RAND() LIMIT %s",
                        (num,)
                    )
                
                rows = cursor.fetchall()
                
                # 转换为字典格式
                columns = ['id', 'name', 'brief', 'difficulty', 'tags', 'heat', 'major', 'intension', 'responsibility']
                result = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    # 处理decimal类型
                    if row_dict['difficulty'] is not None:
                        row_dict['difficulty'] = float(row_dict['difficulty'])
                    if row_dict['heat'] is not None:
                        row_dict['heat'] = float(row_dict['heat'])
                    result.append(row_dict)
                
                return {
                    'data': result,
                    'total_requested': num,
                    'total_available': total_count,
                    'actual_returned': len(result)
                }
                
        except Exception as e:
            current_app.logger.error(f"获取随机面试预设失败: {e}")
            return {'error': str(e)}
        finally:
            if conn:
                conn.close() 

    def get_suggestions(self, q, limit=5):
        """根据输入内容模糊匹配 name 或 major 字段，返回前 limit 条推荐（含岗位和专业）"""
        conn = None
        try:
            conn = db_manager.get_connection_context()
            with conn.cursor() as cursor:
                cursor.execute("USE interview")
                sql = (
                    "SELECT name, major FROM interview_preset_recommended "
                    "WHERE name LIKE %s OR major LIKE %s "
                    "ORDER BY heat DESC, id DESC LIMIT %s"
                )
                cursor.execute(sql, (f"%{q}%", f"%{q}%", limit))
                rows = cursor.fetchall()
                # rows: [(name1, major1), (name2, major2), ...]
                return [{"name": row[0], "major": row[1]} for row in rows]
        except Exception as e:
            current_app.logger.error(f"获取面试预设联想推荐失败: {e}")
            return []
        finally:
            if conn:
                conn.close() 