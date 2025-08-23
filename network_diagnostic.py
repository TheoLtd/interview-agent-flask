#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RTMP网络连接快速诊断工具
针对 "Cannot assign requested address" 错误的专门诊断
"""

import subprocess
import socket
import time
import sys
import urllib.parse
from datetime import datetime

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_dns_resolution(hostname):
    """测试DNS解析"""
    print(f"🔍 测试DNS解析: {hostname}")
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✅ DNS解析成功: {hostname} -> {ip}")
        return ip
    except socket.gaierror as e:
        print(f"❌ DNS解析失败: {e}")
        return None

def test_tcp_connection(host, port):
    """测试TCP连接"""
    print(f"🔗 测试TCP连接: {host}:{port}")
    try:
        start_time = time.time()
        sock = socket.create_connection((host, port), timeout=10)
        end_time = time.time()
        sock.close()
        latency = round((end_time - start_time) * 1000, 2)
        print(f"✅ TCP连接成功，延迟: {latency}ms")
        return True, latency
    except socket.timeout:
        print(f"❌ TCP连接超时")
        return False, None
    except socket.error as e:
        print(f"❌ TCP连接失败: {e}")
        if "Cannot assign requested address" in str(e):
            print("   💡 这是您遇到的具体错误！")
        return False, None

def test_ping(hostname):
    """测试ping连通性"""
    print(f"🏓 测试Ping连通性: {hostname}")
    try:
        # Linux/Mac ping命令
        result = subprocess.run(['ping', '-c', '3', hostname], 
                              capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            print(f"✅ Ping成功")
            # 提取延迟信息
            lines = result.stdout.split('\n')
            for line in lines:
                if 'time=' in line:
                    print(f"   {line.strip()}")
            return True
        else:
            print(f"❌ Ping失败")
            print(f"   错误: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Ping测试异常: {e}")
        return False

def test_rtmp_with_ffprobe(rtmp_url):
    """使用ffprobe测试RTMP连接"""
    print(f"🎥 测试RTMP流连接: {rtmp_url}")
    
    # 检查ffprobe是否可用
    try:
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffprobe工具不可用，请安装FFmpeg")
        return False
    
    # 测试RTMP连接
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0',
            '-timeout', '10000000',  # 10秒超时
            '-rw_timeout', '10000000',
            rtmp_url
        ]
        
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        end_time = time.time()
        
        if result.returncode == 0:
            duration = round((end_time - start_time) * 1000, 2)
            print(f"✅ RTMP连接成功，用时: {duration}ms")
            return True
        else:
            print(f"❌ RTMP连接失败")
            print(f"   错误: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ RTMP连接超时")
        return False
    except Exception as e:
        print(f"❌ RTMP测试异常: {e}")
        return False

def check_network_interface():
    """检查网络接口状态"""
    print("🌐 检查网络接口状态")
    try:
        # 获取默认路由
        result = subprocess.run(['ip', 'route', 'show', 'default'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ 默认路由: {result.stdout.strip()}")
        else:
            print("❌ 无法获取默认路由信息")
        
        # 检查DNS配置
        try:
            with open('/etc/resolv.conf', 'r') as f:
                dns_content = f.read()
                print(f"📋 DNS配置:")
                for line in dns_content.split('\n'):
                    if line.strip() and not line.startswith('#'):
                        print(f"   {line}")
        except Exception as e:
            print(f"⚠️  无法读取DNS配置: {e}")
            
    except Exception as e:
        print(f"❌ 网络接口检查失败: {e}")

def suggest_fixes():
    """提供修复建议"""
    print_section("🔧 修复建议")
    
    print("基于诊断结果，建议尝试以下修复方案:")
    print()
    print("1. 🔄 重启网络服务:")
    print("   sudo systemctl restart networking")
    print("   sudo systemctl restart systemd-networkd")
    print()
    print("2. 🔄 刷新DNS缓存:")
    print("   sudo systemctl flush-dns")
    print("   sudo resolvectl flush-caches")
    print()
    print("3. 🔍 检查防火墙出站规则:")
    print("   sudo iptables -L OUTPUT")
    print("   sudo ufw status")
    print()
    print("4. 🌐 尝试使用IP地址直接连接:")
    print("   将RTMP URL中的域名替换为IP地址")
    print()
    print("5. 🔧 修改FFmpeg参数:")
    print("   添加 -timeout 和 -rw_timeout 参数")
    print("   添加 -multiple_requests 1 参数")
    print()
    print("6. 📞 如果问题持续，请联系:")
    print("   - 网络管理员检查网络路由")
    print("   - 数字人服务提供商确认服务器状态")

def main():
    if len(sys.argv) < 2:
        print("用法: python network_diagnostic.py <RTMP_URL>")
        print("示例: python network_diagnostic.py rtmp://srs-stream-huabei-1.xf-yun.com:19350/live/stream123")
        sys.exit(1)
    
    rtmp_url = sys.argv[1]
    
    print_section("RTMP网络连接诊断工具")
    print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标URL: {rtmp_url}")
    
    # 解析URL
    try:
        parsed = urllib.parse.urlparse(rtmp_url)
        hostname = parsed.hostname
        port = parsed.port or 1935
        print(f"服务器: {hostname}")
        print(f"端口: {port}")
    except Exception as e:
        print(f"❌ URL解析失败: {e}")
        return
    
    # 执行诊断测试
    print_section("🔍 网络连接诊断")
    
    # 1. DNS解析测试
    ip = test_dns_resolution(hostname)
    
    # 2. Ping测试
    ping_ok = test_ping(hostname)
    
    # 3. TCP连接测试
    tcp_ok, latency = test_tcp_connection(hostname, port)
    
    # 4. RTMP协议测试
    rtmp_ok = test_rtmp_with_ffprobe(rtmp_url)
    
    # 5. 网络接口检查
    print_section("🌐 系统网络状态")
    check_network_interface()
    
    # 诊断总结
    print_section("📋 诊断总结")
    print(f"DNS解析: {'✅ 正常' if ip else '❌ 失败'}")
    print(f"Ping连通: {'✅ 正常' if ping_ok else '❌ 失败'}")
    print(f"TCP连接: {'✅ 正常' if tcp_ok else '❌ 失败'}")
    print(f"RTMP协议: {'✅ 正常' if rtmp_ok else '❌ 失败'}")
    
    if latency:
        print(f"网络延迟: {latency}ms")
    
    # 问题分析
    if not tcp_ok and ping_ok:
        print("\n🎯 问题分析:")
        print("Ping正常但TCP连接失败，可能是:")
        print("- 防火墙阻拦出站连接")
        print("- 端口特定的网络策略")
        print("- 本地网络配置问题")
    elif not ping_ok:
        print("\n🎯 问题分析:")
        print("Ping失败，可能是:")
        print("- 网络连接问题")
        print("- DNS解析问题")
        print("- 防火墙阻拦ICMP")
    elif tcp_ok and not rtmp_ok:
        print("\n🎯 问题分析:")
        print("TCP连接正常但RTMP失败，可能是:")
        print("- RTMP协议层面的问题")
        print("- 服务器端配置问题")
        print("- FFmpeg参数需要调整")
    
    # 提供修复建议
    suggest_fixes()

if __name__ == "__main__":
    main() 