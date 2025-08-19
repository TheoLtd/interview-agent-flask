#!/usr/bin/env python3
"""
生产环境部署检查脚本
用于诊断API部署问题
"""
import requests
import json
from datetime import datetime

def check_api_endpoint(base_url, endpoint, method='GET', data=None):
    """检查API端点"""
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    print(f"\n{'='*60}")
    print(f"检查: {method} {url}")
    print(f"{'='*60}")
    
    try:
        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ 请求成功")
            try:
                json_data = response.json()
                print(f"响应数据: {json.dumps(json_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应文本: {response.text[:500]}")
        else:
            print(f"❌ 请求失败")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误")
    except Exception as e:
        print(f"❌ 异常: {str(e)}")

def check_flask_routes():
    """检查Flask路由配置"""
    print(f"\n{'='*60}")
    print("检查本地Flask路由配置")
    print(f"{'='*60}")
    
    try:
        from app import create_app
        app = create_app()
        
        # 查找practice相关的路由
        practice_routes = []
        for rule in app.url_map.iter_rules():
            if 'practice' in rule.rule:
                practice_routes.append({
                    'endpoint': rule.rule,
                    'methods': list(rule.methods - {'HEAD', 'OPTIONS'})
                })
        
        print("Practice相关路由:")
        for route in practice_routes:
            methods_str = ', '.join(route['methods'])
            print(f"  {route['endpoint']} -> {methods_str}")
            
        # 特别检查evaluate路由
        evaluate_routes = [r for r in practice_routes if 'evaluate' in r['endpoint']]
        if evaluate_routes:
            print(f"\n✅ 找到 {len(evaluate_routes)} 个evaluate路由")
            for route in evaluate_routes:
                if 'POST' in route['methods']:
                    print(f"✅ {route['endpoint']} 支持POST方法")
                else:
                    print(f"❌ {route['endpoint']} 不支持POST方法")
        else:
            print("❌ 未找到evaluate路由")
            
    except Exception as e:
        print(f"❌ 检查路由失败: {str(e)}")

def main():
    print("🚀 生产环境部署检查开始...")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查本地路由配置
    check_flask_routes()
    
    # 生产环境URL
    production_url = "https://interviewassistant.top"
    
    # 测试数据
    test_data = {
        "historyData": "测试数据>;<问题1>;<答案1>;<问题2>;<答案2"
    }
    
    # 检查基础连通性
    print(f"\n{'='*60}")
    print("检查服务器连通性")
    print(f"{'='*60}")
    try:
        response = requests.get(production_url, timeout=5)
        print(f"✅ 服务器连通，状态码: {response.status_code}")
    except Exception as e:
        print(f"❌ 服务器连接失败: {str(e)}")
        return
    
    # 检查各个API端点
    endpoints_to_check = [
        # GET请求测试
        ("practice/evaluate?historyData=test", "GET", None),
        ("practice/answer_v1?prompt=test", "GET", None),
        ("practice/mbti_test?prompt=test", "GET", None),
        
        # POST请求测试
        ("practice/evaluate", "POST", test_data),
        ("practice/answer_v1", "POST", {"prompt": "test"}),
        ("practice/mbti_test", "POST", {"prompt": "test"}),
    ]
    
    for endpoint, method, data in endpoints_to_check:
        check_api_endpoint(production_url, endpoint, method, data)
    
    print(f"\n{'='*60}")
    print("检查建议:")
    print(f"{'='*60}")
    print("1. 如果GET请求正常但POST请求405错误:")
    print("   -> Flask应用代码已更新但服务未重启")
    print("   -> 执行: sudo systemctl restart your-flask-service")
    print()
    print("2. 如果所有请求都超时或504错误:")
    print("   -> Flask应用可能崩溃或未启动")
    print("   -> 检查: sudo systemctl status your-flask-service")
    print("   -> 查看日志: sudo journalctl -u your-flask-service -f")
    print()
    print("3. 如果502错误:")
    print("   -> Nginx配置问题或Flask应用端口不匹配")
    print("   -> 检查Nginx配置和Flask应用端口")
    print()
    print("4. 如果404错误:")
    print("   -> 路由配置问题或应用未正确加载")
    print("   -> 检查Flask应用的蓝图注册")

if __name__ == "__main__":
    main() 