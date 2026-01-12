#!/usr/bin/env python3
"""
数据库健康检查工具
用于诊断MySQL连接问题
"""

import pymysql
import time
from app.config import Config

def test_basic_connection():
    """测试基本数据库连接"""
    print("🔍 测试基本数据库连接...")
    config = Config.PYMYSQL_CONFIG
    
    try:
        connection = pymysql.connect(**config)
        print("✅ 基本连接成功")
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ MySQL版本: {version[0]}")
            
            cursor.execute("SHOW VARIABLES LIKE 'wait_timeout'")
            wait_timeout = cursor.fetchone()
            print(f"✅ wait_timeout: {wait_timeout[1]}秒")
            
            cursor.execute("SHOW VARIABLES LIKE 'interactive_timeout'")
            interactive_timeout = cursor.fetchone()
            print(f"✅ interactive_timeout: {interactive_timeout[1]}秒")
            
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 基本连接失败: {e}")
        return False

def test_connection_timeout():
    """测试连接超时"""
    print("\n🔍 测试连接超时...")
    config = Config.PYMYSQL_CONFIG
    
    try:
        connection = pymysql.connect(**config)
        print("✅ 连接建立成功")
        
        # 等待一段时间测试连接是否会超时
        print("⏳ 等待60秒测试连接保持...")
        time.sleep(60)
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ 60秒后连接仍然有效: {result[0]}")
            
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 连接超时测试失败: {e}")
        return False

def test_user_table():
    """测试用户表查询"""
    print("\n🔍 测试用户表查询...")
    config = Config.PYMYSQL_CONFIG
    
    try:
        connection = pymysql.connect(**config)
        
        with connection.cursor() as cursor:
            # 检查user表是否存在
            cursor.execute("SHOW TABLES LIKE 'user'")
            table_exists = cursor.fetchone()
            
            if table_exists:
                print("✅ user表存在")
                
                # 测试查询
                cursor.execute("SELECT COUNT(*) FROM user")
                count = cursor.fetchone()
                print(f"✅ user表记录数: {count[0]}")
                
                # 测试具体查询（模拟实际业务查询）
                cursor.execute("SELECT * FROM user WHERE telephone = %s LIMIT 1", ('15775988727',))
                user = cursor.fetchone()
                if user:
                    print(f"✅ 找到测试用户: {user}")
                else:
                    print("ℹ️ 未找到测试用户")
                    
            else:
                print("❌ user表不存在")
                
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 用户表查询失败: {e}")
        return False

def test_sqlalchemy_connection():
    """测试SQLAlchemy连接"""
    print("\n🔍 测试SQLAlchemy连接...")
    
    try:
        from app import create_app
        from app.extensions import db_manager, get_session
        
        app = create_app()
        with app.app_context():
            # 测试会话获取
            session = get_session()
            print("✅ SQLAlchemy会话获取成功")
            
            # 测试简单查询
            from app.models.user import User
            user_count = session.query(User).count()
            print(f"✅ SQLAlchemy查询成功，用户数: {user_count}")
            
            session.close()
            print("✅ 会话关闭成功")
            
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy连接测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 开始数据库健康检查...\n")
    
    tests = [
        ("基本连接测试", test_basic_connection),
        ("用户表查询测试", test_user_table),
        ("SQLAlchemy连接测试", test_sqlalchemy_connection),
        # ("连接超时测试", test_connection_timeout),  # 可选，耗时较长
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"执行: {test_name}")
        print(f"{'='*50}")
        
        result = test_func()
        results.append((test_name, result))
    
    print(f"\n{'='*50}")
    print("测试结果汇总:")
    print(f"{'='*50}")
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 所有测试通过！数据库连接正常。")
    else:
        print("\n⚠️ 存在测试失败，请检查数据库配置。")

if __name__ == '__main__':
    main() 