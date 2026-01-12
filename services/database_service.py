from flask import current_app, jsonify
from app.extensions import db_manager
import pymysql

class DatabaseService:
    def __init__(self):
        self.config = current_app.config['PYMYSQL_CONFIG']
    
    def get_tables(self):
        """获取interview数据库中的所有表"""
        try:
            # 使用连接池获取连接
            conn = db_manager.get_connection()
            try:
                # 确保使用interview数据库
                with conn.cursor() as cursor:
                    cursor.execute("USE interview")
                    cursor.execute("SHOW TABLES")
                    result = cursor.fetchall()
                    
                    # # 添加调试信息
                    # print(f"DEBUG: 数据库查询成功，找到 {len(result)} 个表")
                    # for table in result:
                    #     print(f"DEBUG: 表: {table[0]}")
                    
                    return result
            finally:
                conn.close()
        except Exception as e:
            print(f"ERROR: 获取表列表失败: {e}")
            current_app.logger.error(f"获取表列表失败: {e}")
            # import traceback
            # traceback.print_exc()
            return []
    
    def get_table_data(self, table_name, params):
        """获取表数据（支持分页和搜索）"""
        try:
            page = params.get('page', 1, type=int)
            per_page = params.get('per_page', 10, type=int)
            search = params.get('search', '')
            search_column = params.get('search_column', '')
            
            conn = db_manager.get_connection()
            try:
                # 确保使用interview数据库
                with conn.cursor() as cursor:
                    cursor.execute("USE interview")
                    # 获取表结构
                    cursor.execute(f"DESCRIBE {table_name}")
                    structure_result = cursor.fetchall()
                    columns = [col[0] for col in structure_result]
                    
                    # 构建查询条件
                    where_clause = ""
                    query_params = []
                    
                    if search and search_column:
                        if search_column in columns:
                            where_clause = f"WHERE {search_column} LIKE %s"
                            query_params.append(f"%{search}%")
                    elif search:
                        search_conditions = []
                        for col in columns:
                            search_conditions.append(f"{col} LIKE %s")
                            query_params.append(f"%{search}%")
                        where_clause = f"WHERE {' OR '.join(search_conditions)}"
                    
                    # 获取总记录数
                    count_sql = f"SELECT COUNT(*) FROM {table_name}"
                    if where_clause:
                        count_sql += f" {where_clause}"
                    
                    cursor.execute(count_sql, query_params)
                    total_records = cursor.fetchone()[0]
                    
                    # 计算分页信息
                    total_pages = (total_records + per_page - 1) // per_page
                    offset = (page - 1) * per_page
                    
                    # 获取分页数据
                    data_sql = f"SELECT * FROM {table_name}"
                    if where_clause:
                        data_sql += f" {where_clause}"
                    data_sql += f" LIMIT {per_page} OFFSET {offset}"
                    
                    cursor.execute(data_sql, query_params)
                    data_result = cursor.fetchall()
                    
                    return {
                        'columns': columns,
                        'rows': data_result,
                        'pagination': {
                            'current_page': page,
                            'per_page': per_page,
                            'total_records': total_records,
                            'total_pages': total_pages
                        },
                        'search': {
                            'term': search,
                            'column': search_column
                        }
                    }
            finally:
                conn.close()
            
        except Exception as e:
            current_app.logger.error(f"获取表数据失败: {e}")
            return {'error': str(e)}
    
    def get_table_structure(self, table_name):
        """获取表结构信息"""
        try:
            conn = db_manager.get_connection()
            try:
                # 确保使用interview数据库
                with conn.cursor() as cursor:
                    cursor.execute("USE interview")
                    cursor.execute(f"DESCRIBE {table_name}")
                    result = cursor.fetchall()
                    
                    structure = []
                    for col in result:
                        field_name, field_type, is_null, key, default, extra = col
                        
                        # 判断是否为自增字段
                        is_auto_increment = 'auto_increment' in extra.lower()
                        
                        # 判断是否有默认值
                        has_default = default is not None
                        
                        # 判断是否可以为空
                        is_nullable = is_null == 'YES'
                        
                        structure.append({
                            'name': field_name,
                            'type': field_type,
                            'is_nullable': is_nullable,
                            'key': key,
                            'default': default,
                            'extra': extra,
                            'is_auto_increment': is_auto_increment,
                            'has_default': has_default,
                            'can_omit': is_auto_increment or has_default
                        })
                    
                    return {'structure': structure}
            finally:
                conn.close()
            
        except Exception as e:
            current_app.logger.error(f"获取表结构失败: {e}")
            return {'error': str(e)}
    
    def insert_record(self, table_name, columns, values):
        """插入记录"""
        try:
            placeholders = ', '.join(['%s'] * len(values))
            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            conn = db_manager.get_connection()
            try:
                # 确保使用interview数据库
                with conn.cursor() as cursor:
                    cursor.execute("USE interview")
                    cursor.execute(sql, values)
                    conn.commit()
                
                return {'success': True, 'message': 'Record inserted successfully'}
            finally:
                conn.close()
            
        except Exception as e:
            current_app.logger.error(f"插入记录失败: {e}")
            return {'error': str(e)}
    
    def update_record(self, table_name, set_clause, where_clause, values):
        """更新记录"""
        try:
            sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
            
            conn = db_manager.get_connection()
            try:
                # 确保使用interview数据库
                with conn.cursor() as cursor:
                    cursor.execute("USE interview")
                    cursor.execute(sql, values)
                    conn.commit()
                
                return {'success': True, 'message': 'Record updated successfully'}
            finally:
                conn.close()
            
        except Exception as e:
            current_app.logger.error(f"更新记录失败: {e}")
            return {'error': str(e)}
    
    def delete_record(self, table_name, where_clause, values):
        """删除记录"""
        try:
            sql = f"DELETE FROM {table_name} WHERE {where_clause}"
            
            conn = db_manager.get_connection()
            try:
                # 确保使用interview数据库
                with conn.cursor() as cursor:
                    cursor.execute("USE interview")
                    cursor.execute(sql, values)
                    conn.commit()
                
                return {'success': True, 'message': 'Record deleted successfully'}
            finally:
                conn.close()
            
        except Exception as e:
            current_app.logger.error(f"删除记录失败: {e}")
            return {'error': str(e)}
    
    def batch_insert_record(self, table_name, columns, data):
        """批量插入记录"""
        try:
            if not data or len(data) == 0:
                return {'error': '没有数据需要插入'}
            
            placeholders = ', '.join(['%s'] * len(columns))
            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            conn = db_manager.get_connection()
            try:
                # 确保使用interview数据库
                with conn.cursor() as cursor:
                    cursor.execute("USE interview")
                    
                    inserted_count = 0
                    for row_data in data:
                        # 确保数据长度与列数匹配
                        if len(row_data) != len(columns):
                            continue
                        
                        try:
                            cursor.execute(sql, row_data)
                            inserted_count += 1
                        except Exception as row_error:
                            current_app.logger.error(f"插入行数据失败: {row_error}")
                            continue
                    
                    conn.commit()
                
                return {
                    'success': True, 
                    'message': f'批量插入成功，共插入 {inserted_count} 条记录',
                    'inserted_count': inserted_count
                }
            finally:
                conn.close()
            
        except Exception as e:
            current_app.logger.error(f"批量插入记录失败: {e}")
            return {'error': str(e)}