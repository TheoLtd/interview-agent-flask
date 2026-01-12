# import json
# import docx
# from io import BytesIO
# from flask import Blueprint, logging, Response
# #  import PyPDF2
# import pypdf
import glob
import os
import subprocess
import json
from flask import request, jsonify, send_from_directory, stream_with_context, current_app, session
import time
from avatar import AipaasAuth
from datetime import datetime
from services.DeepSeek import DeepseekAPI
from services.SparkPractice import AIPracticeAPI
from avatar.AvatarWebSocket import avatarWebsocket
from services.FaceDetect import facial_detect, add_arrays
import threading
from . import interview_bp
from . import (
    wsclient
)


def log_to_chat_file(data_to_log):
    """将数据附加到会话中指定的聊天日志文件中"""
    log_file_name = session.get('chat_log_file')
    if not log_file_name:
        print("警告：在会话中找不到 chat_log_file，无法记录聊天。")
        return

    # 使用项目根目录构建正确的路径
    log_dir = os.path.join(os.path.dirname(current_app.root_path), 'log', 'chat')
    log_file_path = os.path.join(log_dir, log_file_name)

    try:
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(f"--- 日志条目: {datetime.now()} ---\n")
            if isinstance(data_to_log, (dict, list)):
                json.dump(data_to_log, f, ensure_ascii=False, indent=4)
            else:
                f.write(str(data_to_log))
            f.write("\n\n")
    except Exception as e:
        print(f"写入聊天日志文件时出错: {e}")


@interview_bp.route('/init', methods=['POST'])
def init():
    # # 调试代码
    # print("=== 初始化调试信息 ===")
    # print("请求方法:", request.method)
    # print("Session ID:", session.get('_id', 'No session ID'))
    # print("Session内容:", dict(session))

    data = request.get_json()
    major = data.get('major')
    intention = data.get('intention')
    job_description = data.get('job_description')
    if not all([major, intention, job_description]):
        return jsonify({'error': 'Missing required fields'}), 400

    # 在 session 中为该用户初始化信息
    user_info = {
        "major": major,
        "intention": intention,
        "job_description": job_description,
        "deepseek_history": []
    }
    session['user_info'] = user_info
    session['facial_expression_list'] = [0] * 8

    # # 调试代码
    # print("设置Session后:")
    # print("Session内容:", dict(session))
    # print("User info:", session.get('user_info'))

    # 为此会话创建日志文件
    log_dir = os.path.join(os.path.dirname(current_app.root_path), 'log', 'chat')
    os.makedirs(log_dir, exist_ok=True)
    timestamp = int(time.time())
    log_file_name = f"chat_{timestamp}.log"
    session['chat_log_file'] = log_file_name

    log_to_chat_file(f"面试会话为用户启动。专业: {major}, 意向: {intention}")

    response = initdeepseek()

    # # 调试代码：查看响应头中的cookie设置
    # print("=== 响应调试信息 ===")
    # print("响应状态码:", response.status_code if hasattr(response, 'status_code') else 'N/A')
    # print("响应头:", dict(response.headers) if hasattr(response, 'headers') else 'N/A')

    return response



@interview_bp.route('/image_detect', methods=['POST'])
def image_detect():
    if 'file' not in request.files:
        return jsonify({'error': 'No image part'}), 400
    file = request.files['file']
    timestamp = request.form.get('timestamp', '')
    print(timestamp)
    print(file.filename)
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        is_exists_path = os.path.exists(current_app.config['UPLOAD_FOLDER_FACE_ROUTE'])
        if not is_exists_path:
            os.makedirs(current_app.config['UPLOAD_FOLDER_FACE_ROUTE'])
        # check the file type:
        if not file.filename.lower().endswith(('jpg','png', 'bmp')):
            return jsonify({'error': 'Invalid file type. Only image files are allowed.'}), 400
        # save the file with the user tag:
        # use the timestamp to avoid file name conflicts
        user = session.get('user_id', 1)
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER_FACE_ROUTE'], file.filename+"_"+timestamp + '.jpg')
        file.save(save_path)
        # if False:
        facial_expression = facial_detect(save_path)

        # 从 session 获取并更新表情列表
        facial_expression_list = session.get('facial_expression_list', [0] * 8)
        facial_expression_list = add_arrays(facial_expression_list, facial_expression)
        session['facial_expression_list'] = facial_expression_list

        return jsonify({'content': 'Success'})
    return jsonify({'error': 'Invalid file type. Only image files are allowed.'}), 400


def initdeepseek():
    # 从 session 中获取用户信息
    user_info = session.get('user_info')
    if not user_info:
        return jsonify({'error': 'User info not initialized in session'}), 400

    # 获取历史对话记录
    history = user_info.get('deepseek_history', [])
    # 读取 prompt.txt 内容
    prompt_path = os.path.join(os.path.dirname(__file__), '../../../services', 'prompt.txt')
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()
    except Exception as e:
        return jsonify({'error': f'Failed to read prompt.txt: {str(e)}'}), 500

    log_to_chat_file({"event": "Initial Prompt", "prompt": prompt})

    # 将 prompt 加入历史记录
    history.append({"role": "user", "content": prompt})
    user_info['deepseek_history'] = history
    # 调用 DeepseekAPI 的 chatwithhistory
    try:
        response = DeepseekAPI.getInstance().chat_with_history(history)
        # 驱动数字人进行开场白
        send_text_in_thread("您好，欢迎来到面试室，我是本轮面试的面试官，请简要介绍一下自己!")
        if response:
            # 将 response 对象转换为字典
            response_dict = vars(response) if hasattr(response, '__dict__') else str(response)
            user_info['deepseek_history'].append(response_dict)
            log_to_chat_file({"event": "历史对话初始化1", "history": user_info['deepseek_history']})
            # 传递 major, intention, job_description，开启第二轮对话
            major = user_info.get('major', '')
            intention = user_info.get('intention', '')
            job_description = user_info.get('job_description', '')
            second_prompt = f"专业：{major}\n求职意向：{intention}\n岗位职责：{job_description}\n请根据这些信息定制合理的面试内容。你这次只需要回复'您好，我是本轮面试的面试官，请简要介绍一下自己!'"
            user_info['deepseek_history'].append({"role": "user", "content": second_prompt})
            second_response = DeepseekAPI.getInstance().chat_with_history(user_info['deepseek_history'])
            if second_response:
                # 同样，将 second_response 对象转换为字典
                second_response_dict = vars(second_response) if hasattr(second_response, '__dict__') else str(second_response)
                user_info['deepseek_history'].append(second_response_dict)
                log_to_chat_file({"event": "历史对话初始化2", "history": user_info['deepseek_history']})

    except Exception as e:
        return jsonify({'error': f'调用Deepseek API失败: {str(e)}'}), 500

    # 将更新后的用户信息存回 session
    session['user_info'] = user_info

    return jsonify({'content': second_response.content})


def send_text_in_thread(text):
    global wsclient
    def target(wsclient: avatarWebsocket, text):
        print("进入")
        print(wsclient.streamUrl)
        if wsclient is not None and not wsclient.is_session_expired():
            wsclient.sendDriverText(text)
        elif wsclient is not None and wsclient.is_session_expired():
            print("会话已超时，无法发送消息")
    if wsclient is not None:
        thread = threading.Thread(target=lambda: target(wsclient, text))
        thread.start()

@interview_bp.route('/answer', methods=['POST'])
def answer():
    # # 调试代码
    # print("=== 调试信息 ===")
    # print("请求方法:", request.method)
    # print("请求头:", dict(request.headers))
    # print("Cookie:", request.headers.get('Cookie', 'No Cookie'))
    # print("Session ID:", session.get('_id', 'No session ID'))
    # print("Session内容:", dict(session))

    # 从 session 中获取用户信息
    user_info = session.get('user_info')
    # # 调试代码
    # print("User info:", user_info)

    if not user_info:
        # # 调试代码
        # print("User info not initialized in session")
        return jsonify({'error': 'User info not initialized in session'}), 400

    # 获取用户消息，从POST请求体中获取
    user_message = request.json.get('message', '') if request.is_json else request.form.get('message', '')
    # # 调试代码
    # print("User message:", user_message)

    if not user_message:
        # # 调试代码
        # print("Message is required")
        return jsonify({'error': 'Message is required'}), 400

    # 获取历史对话记录
    user_info['deepseek_history'].append({"role": "user", "content": user_message})
    try:
        response = DeepseekAPI.getInstance().chat_with_history(deepseek_history=user_info['deepseek_history'])
        if response:
            response_dict = vars(response) if hasattr(response, '__dict__') else str(response)
            user_info['deepseek_history'].append(response_dict)
            log_to_chat_file({"event": "User/AI turn", "history": user_info['deepseek_history'][-2:]})
            send_text_in_thread(response.content)
    except Exception as e:
        return jsonify({'error': f'调用Deepseek API失败: {str(e)}'}), 500

    # 将更新后的用户信息存回 session
    session['user_info'] = user_info

    return jsonify({'content': response.content})



@interview_bp.route('/init_shuziren', methods=['GET'])
def init_shuziren():
    """
    初始化数字人，优化版本 - 减少FFmpeg初始化时间
    """
    
    cleanup_avatar()
    
    # 在每次初始化数字人时，先清空上一轮生成的 HLS 缓存文件，避免旧切片干扰
    project_root = os.path.dirname(current_app.root_path)
    stream_folder_abs = os.path.join(project_root, 'resource', 'stream')
    delete_files_in_folder(stream_folder_abs)
    global wsclient
    
    # 如果已有客户端且未超时，直接返回
    if wsclient is not None and not wsclient.is_session_expired():
        print("启动process")
        rtmp_to_hls(wsclient.streamUrl, current_app.config['HLS_FOLDER_FILE'])
        return jsonify({
            'content': "true",
            'remaining_time': wsclient.get_session_remaining_time(),
            'session_active': True
        })
    
    # 如果客户端超时，先清理旧连接
    if wsclient is not None and wsclient.is_session_expired():
        print("检测到会话超时，清理旧连接")
        try:
            wsclient.stop()
        except Exception as e:
            print(f"清理旧连接时出错: {e}")
        wsclient = None
    
    url = current_app.config['AVATER_CONFIG']['url']
    appId = current_app.config['AVATER_CONFIG']['appId']
    appKey = current_app.config['AVATER_CONFIG']['appKey']
    appSecret = current_app.config['AVATER_CONFIG']['appSecret']
    anchorId = current_app.config['AVATER_CONFIG']['anchorId']
    vcn = current_app.config['AVATER_CONFIG']['vcn']
    authUrl = AipaasAuth.assemble_auth_url(url, 'GET', appKey, appSecret)
    wsclient = avatarWebsocket(authUrl, protocols='', headers=None)
    try:
        wsclient.appId = appId
        wsclient.anchorId = anchorId
        wsclient.vcn = vcn
        wsclient.start()
        
        # 优化：减少等待时间，增加超时检查
        max_wait_time = 45  # 最大等待30秒
        start_wait = time.time()
        while not wsclient.streamUrl:
            if time.time() - start_wait > max_wait_time:
                raise Exception("Avatar连接超时")
            time.sleep(0.5)  # 减少检查间隔
        
        print(f"Avatar连接成功: {wsclient.streamUrl}")

        # 使用绝对路径确保路径一致性
        project_root = os.path.dirname(current_app.root_path)
        hls_folder_abs = os.path.join(project_root, 'resource', 'stream')
        hls_file_path_abs = os.path.join(hls_folder_abs, 'playlist.m3u8')

        # 启动优化的FFmpeg进程（服务器环境使用稳定版本）
        print("启动优化的FFmpeg进程...")
        # 检测是否为服务器环境
        import platform
        is_server = platform.system() == 'Linux' or 'server' in platform.node().lower()
        
        # 统一使用优化快速版FFmpeg配置
        print("使用优化快速版FFmpeg配置")
        ffmpeg_process = rtmp_to_hls_fast_optimized(wsclient.streamUrl, hls_file_path_abs)
        
        if ffmpeg_process is None:
            raise Exception("FFmpeg启动失败")

        # 优化：更积极的HLS等待策略
        print("等待HLS播放列表文件...")
        timeout = 12  # 减少超时时间到12秒
        start_time = time.time()
        first_segment_ready = False
        playlist_created = False
        
        while time.time() - start_time < timeout:
            # 先检查播放列表是否创建
            if not playlist_created and os.path.exists(hls_file_path_abs):
                playlist_created = True
                print("HLS播放列表已创建，等待第一个切片...")
            
            # 如果播放列表已创建，检查切片
            if playlist_created:
                try:
                    with open(hls_file_path_abs, 'r') as f:
                        content = f.read()
                        if '.ts' in content:  # 有切片文件
                            # 检查切片文件是否实际存在
                            lines = content.split('\n')
                            ts_files = [line.strip() for line in lines if line.strip().endswith('.ts')]
                            if ts_files:
                                ts_path = os.path.join(os.path.dirname(hls_file_path_abs), ts_files[0])
                                if os.path.exists(ts_path) and os.path.getsize(ts_path) > 1024:  # 至少1KB
                                    first_segment_ready = True
                                    break
                except:
                    pass
            
            time.sleep(0.1)  # 更频繁的检查

        if not first_segment_ready:
            if playlist_created:
                print("警告：播放列表已创建但切片未就绪，继续提供服务")
            else:
                print("警告：HLS初始化超时，但继续提供服务")
            # 不返回错误，让前端轮询检查
        else:
            elapsed_time = time.time() - start_wait
            print(f"HLS播放列表就绪，总初始化时间: {elapsed_time:.1f}秒")

        return jsonify({
            'content': "true",
            'remaining_time': wsclient.get_session_remaining_time(),
            'session_active': True,
            'hls_ready': first_segment_ready,
            'initialization_time': round(time.time() - start_wait, 2)
        })
        
    except Exception as e:
        print(f"初始化数字人时发生错误: {e}")
        return jsonify({'error': f'初始化数字人失败: {str(e)}'}), 500


@interview_bp.route('/session_status', methods=['GET'])
def get_session_status():
    """
    获取avatar会话状态和剩余时间
    """
    global wsclient
    
    if wsclient is None:
        return jsonify({
            'session_active': False,
            'remaining_time': 0,
            'elapsed_time': 0,
            'message': '会话未启动',
            'data': None
        })
    
    if wsclient.is_session_expired():
        return jsonify({
            'session_active': False,
            'remaining_time': 0,
            'elapsed_time': wsclient.get_session_elapsed_time(),
            'message': '会话已超时',
            'data': None
        })
    
    remaining_time = wsclient.get_session_remaining_time()
    elapsed_time = wsclient.get_session_elapsed_time()
    
    # 检查HLS文件状态
    project_root = os.path.dirname(current_app.root_path)
    hls_file_path = os.path.join(project_root, 'resource', 'stream', 'playlist.m3u8')
    stream_ready = os.path.exists(hls_file_path)
    
    # 构建完整的会话数据
    session_data = {
        'session_id': getattr(wsclient, 'session_id', None),
        'stream_url': getattr(wsclient, 'streamUrl', None),
        'websocket_url': getattr(wsclient, 'websocketUrl', None),
        'stream_ready': stream_ready,
        'hls_path': '/interview/video/playlist.m3u8' if stream_ready else None
    }
    
    return jsonify({
        'session_active': True,
        'remaining_time': remaining_time,
        'elapsed_time': elapsed_time,
        'remaining_minutes': round(remaining_time / 60, 1),
        'elapsed_minutes': round(elapsed_time / 60, 1),
        'message': f'会话活跃，剩余时间: {round(remaining_time / 60, 1)}分钟',
        'data': session_data
    })

@interview_bp.route('/end_session', methods=['POST'])
def end_session():
    """
    手动结束avatar会话
    """
    global wsclient
    
    if wsclient is None:
        return jsonify({
            'success': False,
            'message': '没有活跃的会话'
        })
    
    try:
        # 发送结束消息
        if not wsclient.is_session_expired():
            wsclient.sendDriverText("面试会话已手动结束，感谢您的参与！")
            time.sleep(2)  # 给一点时间让消息发送完成
        
        # 停止会话
        wsclient.stop()
        wsclient = None
        
        return jsonify({
            'success': True,
            'message': '会话已成功结束'
        })
    except Exception as e:
        print(f"结束会话时出错: {e}")
        return jsonify({
            'success': False,
            'message': f'结束会话时出错: {str(e)}'
        }), 500


def rtmp_to_hls_fast(input_rtmp_url, output_hls_path):
    """
    快速启动的RTMP到HLS转换 - 优化初始化时间
    """
    ffmpeg_cmd = [
        'ffmpeg',
        '-y',                              # 覆盖现有文件
        '-loglevel', 'warning',            # 减少日志输出
        '-fflags', '+genpts+nobuffer',     # 生成时间戳+无缓冲
        '-flags', 'low_delay',             # 低延迟
        '-thread_queue_size', '512',       # 线程队列大小
        '-analyzeduration', '1000000',     # 减少分析时间（1秒）
        '-probesize', '1000000',           # 减少探测大小
        '-i', input_rtmp_url,              # 输入源
        '-c:v', 'libx264',                 # 视频编码
        '-preset', 'ultrafast',            # 最快编码预设
        '-tune', 'zerolatency',            # 零延迟调优
        '-profile:v', 'baseline',          # 基线配置
        '-level', '3.0',                   # H.264级别
        '-x264-params', 'nal-hrd=cbr',     # 恒定比特率
        '-c:a', 'aac',                     # 音频编码
        '-ac', '2',                        # 立体声
        '-ar', '44100',                    # 音频采样率
        '-b:a', '96k',                     # 降低音频比特率
        '-f', 'hls',                       # HLS格式
        '-hls_time', '1',                  # 1秒切片
        '-hls_list_size', '3',             # 只保留3个片段
        '-hls_flags', 'delete_segments+append_list+split_by_time+program_date_time',
        '-hls_segment_type', 'mpegts',     # TS格式
        '-hls_allow_cache', '0',           # 禁用缓存
        '-start_number', '0',              # 从0开始
        '-g', '30',                        # GOP大小
        '-keyint_min', '30',               # 关键帧间隔
        '-sc_threshold', '0',              # 禁用场景检测
        output_hls_path                    # 输出路径
    ]
    
    try:
        # 确保日志目录存在
        log_dir = os.path.join('log', 'ffmpeg_log')
        os.makedirs(log_dir, exist_ok=True)

        # 创建日志文件
        timestamp = int(time.time())
        log_file_name = f"ffmpeg_fast_{timestamp}.log"
        log_file_path = os.path.join(log_dir, log_file_name)

        print(f"启动快速FFmpeg进程，日志: {log_file_path}")

        # 启动FFmpeg进程
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.DEVNULL,
                stderr=log_file,
                bufsize=0  # 无缓冲
            )

        return process
        
    except Exception as e:
        print(f"启动快速FFmpeg进程时发生错误: {e}")
        return None


def rtmp_to_hls_fast_optimized(input_rtmp_url, output_hls_path):
    """
    优化快速版本
    适合生产和开发环境统一使用
    """
    
    # 验证和清理输入URL
    print(f"🔍 FFmpeg接收到的URL: {input_rtmp_url}")
    
    # 确保URL格式正确
    if not input_rtmp_url.startswith('rtmp://'):
        print(f"❌ 错误的URL格式: {input_rtmp_url}")
        return None
    
    # 解析RTMP URL的各个部分
    try:
        # 移除查询参数
        base_url = input_rtmp_url.split('?')[0] if '?' in input_rtmp_url else input_rtmp_url
        
        # 解析URL各个部分
        url_parts = base_url.replace('rtmp://', '').split('/')
        host_port = url_parts[0]
        app_name = url_parts[1] if len(url_parts) > 1 else 'live'
        stream_key = url_parts[2] if len(url_parts) > 2 else ''
        
        # 重构RTMP URL
        clean_rtmp_url = f"rtmp://{host_port}/{app_name}/{stream_key}"
        print(f"🔧 RTMP URL解析结果:")
        print(f"   主机端口: {host_port}")
        print(f"   应用名称: {app_name}")
        print(f"   流密钥: {stream_key}")
        print(f"   清理后URL: {clean_rtmp_url}")
        
        input_rtmp_url = clean_rtmp_url
    except Exception as e:
        print(f"⚠️ RTMP URL解析失败: {e}")
        return None
    
    # 确保输出目录存在并清理
    try:
        output_dir = os.path.dirname(output_hls_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # 清理旧的HLS文件（使用安全的文件删除方法）
        safe_delete_hls_files(output_dir)
        
    except Exception as e:
        print(f"⚠️ 目录操作失败: {e}")
    
    ffmpeg_cmd = [
        'ffmpeg',
        '-y',                              # 覆盖现有文件
        '-loglevel', 'warning',               # 详细日志便于调试
        
        # RTMP输入参数
        '-re',                             # 实时模式
        '-stream_loop', '-1',              # 无限循环（如果流中断）
        '-i', input_rtmp_url,              # 输入源
        
        # 视频编码参数
        '-c:v', 'libx264',                 # 视频编码器
        '-preset', 'ultrafast',            # 最快编码预设
        '-tune', 'zerolatency',            # 零延迟调优
        '-profile:v', 'baseline',          # 基线配置
        '-level', '3.0',                   # H.264级别
        '-x264-params', 'nal-hrd=cbr:force-cfr=1', # 恒定比特率+强制恒定帧率
        '-maxrate', '1000k',               # 最大比特率
        '-bufsize', '500k',                # 缓冲区大小
        '-r', '25',                        # 固定帧率25fps
        '-g', '25',                        # GOP大小25（1秒）
        '-keyint_min', '25',               # 最小关键帧间隔
        '-sc_threshold', '0',              # 禁用场景检测
        
        # 音频编码参数
        '-c:a', 'aac',                     # 音频编码器
        '-ac', '2',                        # 立体声
        '-ar', '44100',                    # 音频采样率
        '-b:a', '128k',                    # 音频比特率
        
        # HLS输出参数
        '-f', 'hls',                       # HLS格式
        '-hls_time', '2',                  # 2秒切片
        '-hls_list_size', '6',             # 保留6个切片
        '-hls_flags', 'delete_segments+append_list+split_by_time+program_date_time',
        '-hls_segment_type', 'mpegts',     # TS格式
        '-hls_allow_cache', '0',           # 禁用缓存
        '-start_number', '0',              # 从0开始
        output_hls_path                    # 输出路径
    ]
    
    try:
        # 确保日志目录存在
        log_dir = os.path.join('log', 'ffmpeg_log')
        os.makedirs(log_dir, exist_ok=True)

        # 创建日志文件
        timestamp = int(time.time())
        log_file_name = f"ffmpeg_fast_optimized_{timestamp}.log"
        log_file_path = os.path.join(log_dir, log_file_name)

        print(f"启动优化快速版FFmpeg进程，日志: {log_file_path}")
        print(f"🎯 最终RTMP URL: {input_rtmp_url}")
        print(f"📂 输出目录: {output_dir}")
        print(f"📄 输出文件: {output_hls_path}")

        # 启动FFmpeg进程
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=log_file,
                bufsize=1,
                universal_newlines=True
            )

        # 等待HLS文件生成
        max_wait = 15  # 最多等待15秒
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if os.path.exists(output_hls_path):
                with open(output_hls_path, 'r') as f:
                    content = f.read()
                    if '.ts' in content:  # 确保至少有一个切片生成
                        print(f"✅ HLS文件已生成并包含切片: {output_hls_path}")
                        return process
            time.sleep(0.5)
        
        print(f"⚠️ 等待HLS文件超时: {output_hls_path}")
        return process

    except Exception as e:
        print(f"❌ 启动FFmpeg进程失败: {e}")
        return None

def safe_delete_hls_files(directory):
    """
    安全地删除HLS相关文件
    """
    try:
        # 获取目录中的所有文件
        files = glob.glob(os.path.join(directory, '*'))
        
        for f in files:
            try:
                # 只删除.ts和.m3u8文件
                if f.endswith('.ts') or f.endswith('.m3u8'):
                    try:
                        os.remove(f)
                        print(f"🧹 清理文件: {f}")
                    except PermissionError:
                        print(f"⚠️ 文件正在使用中，跳过: {f}")
                    except Exception as e:
                        print(f"⚠️ 删除文件失败: {f} - {e}")
            except Exception as e:
                print(f"⚠️ 处理文件失败: {f} - {e}")
                
    except Exception as e:
        print(f"⚠️ 清理目录失败: {directory} - {e}")

def delete_files_in_folder(folder_path):
    """
    删除文件夹中的文件（带重试机制）
    """
    max_retries = 3
    retry_delay = 1  # 秒
    
    for retry in range(max_retries):
        try:
            safe_delete_hls_files(folder_path)
            return
        except Exception as e:
            if retry < max_retries - 1:
                print(f"⚠️ 删除文件失败，将在{retry_delay}秒后重试: {e}")
                time.sleep(retry_delay)
            else:
                print(f"❌ 删除文件最终失败: {e}")
                break


def rtmp_to_hls_stable_fast_deprecated(input_rtmp_url, output_hls_path):
    """
    优化稳定版本 - 在保持稳定性的同时减少初始化时间
    """
    ffmpeg_cmd = [
        'ffmpeg',
        '-y',                              # 覆盖现有文件
        '-loglevel', 'warning',            # 减少日志输出
        '-reconnect', '1',                 # 启用重连
        '-reconnect_at_eof', '1',          # EOF时重连
        '-reconnect_streamed', '1',        # 流式重连
        '-reconnect_delay_max', '1',       # 减少重连延迟到1秒
        '-fflags', '+genpts+nobuffer',     # 生成时间戳+减少缓冲
        '-thread_queue_size', '512',       # 适中的线程队列
        '-analyzeduration', '1000000',     # 减少分析时间到1秒
        '-probesize', '1000000',           # 减少探测大小
        '-max_delay', '1000000',           # 最大延迟1秒
        '-i', input_rtmp_url,              # 输入源
        '-c:v', 'libx264',                 # 视频编码
        '-preset', 'ultrafast',            # 最快编码预设
        '-tune', 'zerolatency',            # 零延迟调优
        '-profile:v', 'baseline',          # 基线配置
        '-level', '3.1',                   # H.264级别
        '-x264-params', 'nal-hrd=cbr:force-cfr=1:no-scenecut=1', # 优化参数
        '-r', '25',                        # 固定帧率25fps
        '-b:v', '600k',                    # 降低比特率加快启动
        '-maxrate', '800k',                # 降低最大比特率
        '-bufsize', '1200k',               # 减少缓冲区大小
        '-c:a', 'aac',                     # 音频编码
        '-ac', '2',                        # 立体声
        '-ar', '44100',                    # 音频采样率
        '-b:a', '96k',                     # 降低音频比特率
        '-f', 'hls',                       # HLS格式
        '-hls_time', '1.5',                # 1.5秒切片（平衡稳定性和速度）
        '-hls_list_size', '4',             # 保留4个片段
        '-hls_flags', 'delete_segments+append_list+split_by_time',
        '-hls_segment_type', 'mpegts',     # TS格式
        '-hls_allow_cache', '0',           # 禁用缓存
        '-hls_segment_filename', os.path.join(os.path.dirname(output_hls_path), 'seg_%03d.ts'),
        '-start_number', '0',              # 从0开始
        '-avoid_negative_ts', 'make_zero', # 避免负时间戳
        '-vsync', 'cfr',                   # 恒定帧率
        '-map', '0:v:0',                   # 映射第一个视频流
        '-map', '0:a:0',                   # 映射第一个音频流
        '-shortest',                       # 最短流结束时停止
        output_hls_path                    # 输出路径
    ]
    
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_hls_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # 确保日志目录存在
        log_dir = os.path.join('log', 'ffmpeg_log')
        os.makedirs(log_dir, exist_ok=True)

        # 创建日志文件
        timestamp = int(time.time())
        log_file_name = f"ffmpeg_stable_fast_{timestamp}.log"
        log_file_path = os.path.join(log_dir, log_file_name)

        print(f"启动优化稳定版FFmpeg进程，日志: {log_file_path}")

        # 启动FFmpeg进程
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=log_file,
                bufsize=0,  # 无缓冲
                universal_newlines=True
            )

        return process
        
    except Exception as e:
        print(f"启动优化稳定版FFmpeg进程时发生错误: {e}")
        return None


def rtmp_to_hls(input_rtmp_url, output_hls_path, low_latency=True):
    """
    将 RTMP 流转换为 HLS 格式, 并将日志输出到文件
    优化版本，支持低延迟配置

    参数:
        input_rtmp_url: 输入RTMP地址 (e.g. "rtmp://example.com/live/stream")
        output_hls_path: 输出HLS目录和文件名 (e.g. "static/stream/playlist.m3u8")
        low_latency: 是否启用低延迟模式 (默认True)
    """

    if low_latency:
        # 低延迟配置
        ffmpeg_cmd = [
            'ffmpeg',
            '-loglevel', 'error',              # 设置日志级别为error
            '-fflags', 'nobuffer',             # 禁用缓冲，减少延迟
            '-flags', 'low_delay',             # 低延迟标志
            '-avioflags', 'direct',            # 直接IO，减少缓冲
            '-i', input_rtmp_url,              # 输入源
            '-c:v', 'libx264',                 # 视频编码
            '-preset', 'ultrafast',            # 最快编码预设
            '-tune', 'zerolatency',            # 零延迟调优
            '-profile:v', 'baseline',          # 基线配置文件，更好的兼容性
            '-level', '3.0',                   # H.264级别
            '-c:a', 'aac',                     # 音频编码
            '-ac', '2',                        # 立体声
            '-ar', '44100',                    # 音频采样率
            '-b:a', '128k',                    # 音频比特率
            '-f', 'hls',                       # 输出格式为HLS
            '-hls_time', '1',                  # 每个TS切片1秒（减少延迟）
            '-hls_list_size', '3',             # 播放列表保留3个片段（减少缓冲）
            '-hls_flags', 'delete_segments+append_list+split_by_time', # 优化标志
            '-hls_segment_type', 'mpegts',     # 使用MPEG-TS格式
            '-hls_allow_cache', '0',           # 禁用缓存
            '-start_number', '0',              # 从0开始编号
            '-g', '30',                        # GOP大小，影响延迟
            '-keyint_min', '30',               # 最小关键帧间隔
            '-sc_threshold', '0',              # 禁用场景检测
            output_hls_path                    # 输出路径
        ]
    else:
        # 标准配置（保持原有配置）
        ffmpeg_cmd = [
            'ffmpeg',
            '-loglevel', 'error',          # 设置日志级别为error
            '-i', input_rtmp_url,          # 输入源
            '-c:v', 'libx264',             # 视频编码
            '-c:a', 'aac',                 # 音频编码
            '-f', 'hls',                   # 输出格式为HLS
            '-hls_time', '2',              # 每个TS切片2秒
            '-hls_list_size', '6',         # 播放列表保留6个片段
            '-hls_flags', 'delete_segments+append_list', # 自动删除旧片段
            output_hls_path                # 输出路径
        ]
    
    try:
        # 确保日志目录存在
        log_dir = os.path.join('log', 'ffmpeg_log')
        os.makedirs(log_dir, exist_ok=True)

        # 创建带时间戳的日志文件名
        timestamp = int(time.time())
        mode_suffix = "_low_latency" if low_latency else "_standard"
        log_file_name = f"ffmpeg_{timestamp}{mode_suffix}.log"
        log_file_path = os.path.join(log_dir, log_file_name)

        print(f"启动FFmpeg（{'低延迟' if low_latency else '标准'}模式），日志将记录到 {log_file_path}")

        # 以写入模式打开新的日志文件
        log_file_handle = open(log_file_path, 'w', encoding='utf-8')

        # 启动FFmpeg进程
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.DEVNULL,
            stderr=log_file_handle,
        )

        return process
    except Exception as e:
        print(f"启动FFmpeg进程时发生错误: {e}")
        return None


# 请求hls推流文件
@interview_bp.route('/video/<path:filename>')
def video(filename):
    # 使用绝对路径来提供文件
    project_root = os.path.dirname(current_app.root_path)
    video_folder_abs = os.path.join(project_root, 'resource', 'stream')
    response = send_from_directory(video_folder_abs, filename)

    # 禁用HLS播放列表文件的缓存
    if filename.endswith('.m3u8'):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response


# 删除websocket连接
@interview_bp.route('/del_wss', methods=['GET'])
def del_wss():
    """
    关闭WebSocket连接
    """
    global wsclient
    if wsclient:
        wsclient.close()
        wsclient = None
    delete_files_in_folder('resource/stream')
    return jsonify({"content":"true"})



@interview_bp.route('/feedback', methods=['GET'])
def feedback():
    # # 调试代码
    # print("=== 调试信息 ===")
    # print("请求方法:", request.method)
    # print("请求头:", dict(request.headers))
    # print("Cookie:", request.headers.get('Cookie', 'No Cookie'))
    # print("Session ID:", session.get('_id', 'No session ID'))
    # print("Session内容:", dict(session))

    """
    根据面试历史生成反馈
    """
    try:
        # 从 session 中获取用户信息
        user_info = session.get('user_info')
        if not user_info:
            return jsonify({'error': 'User info not initialized in session'}), 400

        # 检查面试历史
        deepseek_history = user_info.get('deepseek_history', [])
        if len(deepseek_history) <= 3:
            return jsonify({'error': 'Insufficient interview history for analysis'}), 400

        # 获取表情分析数据
        facial_expression_list = session.get('facial_expression_list', [])

        # 使用增强分析器
        from services.EnhancedInterviewAnalyzer import EnhancedInterviewAnalyzer
        analyzer = EnhancedInterviewAnalyzer()
        
        # 生成面试分析报告
        analysis_result = analyzer.analyze_interview_performance(
            interview_history=deepseek_history[3:],  # 跳过初始化消息
            user_info=user_info,
            facial_expressions=facial_expression_list if sum(facial_expression_list) > 0 else None
        )

        if not analysis_result.get('success'):
            return jsonify({
                'error': analysis_result.get('error', 'Analysis failed'),
                'fallback_content': _generate_fallback_feedback(user_info, deepseek_history)
            }), 500

        # 保存分析结果到文件
        timestamp = int(time.time())
        filename = f"enhanced_feedback_{timestamp}.json"
        filepath = os.path.join(current_app.config['FEEDBACK_FOLDER_ROUTE'], filename)
        
        # 确保目录存在
        os.makedirs(current_app.config['FEEDBACK_FOLDER_ROUTE'], exist_ok=True)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)

        # 记录日志
        log_to_chat_file({
            "event": "Enhanced Feedback Generated", 
            "overall_score": analysis_result.get('overall_score'),
            "timestamp": analysis_result.get('timestamp'),
            "file": filename
        })

        return jsonify({
            'success': True,
            'content': analysis_result,
            'message': 'Enhanced interview analysis completed successfully'
        })

    except Exception as e:
        print(f"Enhanced feedback generation failed: {str(e)}")
        # 降级到原有的简单反馈
        return _generate_simple_feedback(user_info, deepseek_history)

@interview_bp.route('/feedback2', methods=['GET'])
def feedback2():

    try:
        # 从 session 获取用户信息和表情列表
        user_info = session.get('user_info', {})
        facial_expression_list = session.get('facial_expression_list', [])

        # 优先查找增强版反馈文件
        enhanced_files = glob.glob(os.path.join(current_app.config['FEEDBACK_FOLDER_ROUTE'], "enhanced_feedback_*.json"))
        
        if enhanced_files:
            # 获取最新的增强版反馈
            latest_enhanced_file = max(enhanced_files, key=os.path.getctime)
            
            with open(latest_enhanced_file, 'r', encoding='utf-8') as f:
                enhanced_feedback = json.load(f)
            
            # 格式化返回增强版分析结果
            return jsonify({
                'type': 'enhanced',
                'content': enhanced_feedback,
                'user_info': user_info,
                'facial_expression_list': facial_expression_list,
                'message': 'Enhanced interview analysis result'
            })
        
        # 降级到原有的简单反馈
        txt_files = glob.glob(os.path.join(current_app.config['FEEDBACK_FOLDER_ROUTE'], "*.txt"))

        if not txt_files:
            return jsonify({
                'type': 'fallback',
                'content': _generate_fallback_feedback(user_info, []),
                'message': 'No feedback files found, using fallback content'
            })

        latest_file = max(txt_files, key=os.path.getctime)

        with open(latest_file, 'r', encoding='utf-8') as f:
            feedback_content = f.read()

        # 尝试解析JSON格式的反馈
        try:
            feedback_json = json.loads(feedback_content)
            return jsonify({
                'type': 'simple_json',
                'content': feedback_json,
                'user_info': user_info,
                'facial_expression_list': facial_expression_list
            })
        except json.JSONDecodeError:
            # 如果不是JSON格式，返回原始文本
            return jsonify({
                'type': 'simple_text',
                'content': {
                    'feedback_text': feedback_content,
                    'scores': [70, 70, 70, 70, 70, 70],  # 默认分数
                    'advantages': [],
                    'disadvantages': []
                },
                'user_info': user_info,
                'facial_expression_list': facial_expression_list
            })
            
    except Exception as e:
        print(f"Feedback2 error: {str(e)}")
        return jsonify({
            'type': 'error',
            'error': str(e),
            'content': _generate_fallback_feedback(user_info, [])
        }), 500


@interview_bp.route('/feedback/enhanced', methods=['GET'])
def enhanced_feedback():
    """
    专门的增强版反馈接口
    """
    try:
        # 从session获取数据
        user_info = session.get('user_info')
        if not user_info:
            return jsonify({'error': 'User info not found'}), 400
            
        deepseek_history = user_info.get('deepseek_history', [])
        if len(deepseek_history) <= 3:
            return jsonify({'error': 'Insufficient interview data'}), 400
            
        facial_expression_list = session.get('facial_expression_list', [])
        
        # 使用增强分析器直接生成
        from services.EnhancedInterviewAnalyzer import EnhancedInterviewAnalyzer
        analyzer = EnhancedInterviewAnalyzer()
        
        analysis_result = analyzer.analyze_interview_performance(
            interview_history=deepseek_history[3:],
            user_info=user_info,
            facial_expressions=facial_expression_list if sum(facial_expression_list) > 0 else None
        )
        
        return jsonify(analysis_result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Enhanced feedback generation failed: {str(e)}'
        }), 500


def _generate_fallback_feedback(user_info: dict, deepseek_history: list) -> dict:
    """生成降级反馈内容"""
    return {
        "overall_score": 70,
        "scores": [70, 70, 70, 70, 70, 70],
        "advantages": [
            {
                "title": "基础交流",
                "desc": "能够进行基本的面试对话和问题回答"
            }
        ],
        "disadvantages": [
            {
                "title": "分析受限",
                "desc": "由于技术原因，无法进行深度分析，建议重新生成反馈"
            }
        ],
        "interview_summary": "由于分析过程中出现技术问题，当前为简化版反馈。建议稍后重试以获得详细分析报告。"
    }


def _generate_simple_feedback(user_info: dict, deepseek_history: list):
    """生成简单反馈 - 使用原有逻辑作为降级方案"""
    try:
        # 使用原有的简单反馈逻辑
        prompt_path = os.path.join(os.path.dirname(__file__), '../../../services', 'feedbackPrompt.txt')
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()
            history_str = json.dumps(deepseek_history[3:], ensure_ascii=False)
            prompt += history_str
            
        response = DeepseekAPI.getInstance().chat_return_json(prompt)
        if response:
            return jsonify({'content': response.content, 'type': 'simple_feedback'})
        else:
            return jsonify({'error': 'Failed to generate feedback'}), 500
            
    except Exception as e:
        return jsonify({
            'error': f'Simple feedback generation failed: {str(e)}',
            'content': _generate_fallback_feedback(user_info, deepseek_history)
        }), 500


def delete_files_in_folder(folder_path):
    files = glob.glob(os.path.join(folder_path, '*'))
    for f in files:
        if os.path.isfile(f):
            os.remove(f)



@interview_bp.route('/preload_avatar', methods=['POST'])
def preload_avatar():
    """
    预加载Avatar连接 - 在用户进入面试前提前建立连接
    """
    global wsclient
    
    # 如果已有连接且正常，直接返回
    if wsclient is not None and not wsclient.is_session_expired():
        return jsonify({
            'success': True,
            'message': 'Avatar连接已存在',
            'preloaded': True,
            'data': {
                'session_id': getattr(wsclient, 'session_id', None),
                'stream_url': wsclient.streamUrl,
                'websocket_url': getattr(wsclient, 'websocketUrl', None)
            }
        })
    
    try:
        # 清理旧连接
        if wsclient is not None:
            try:
                wsclient.stop()
            except:
                pass
            wsclient = None
        
        # 建立新连接
        url = current_app.config['AVATER_CONFIG']['url']
        appId = current_app.config['AVATER_CONFIG']['appId']
        appKey = current_app.config['AVATER_CONFIG']['appKey']
        appSecret = current_app.config['AVATER_CONFIG']['appSecret']
        anchorId = current_app.config['AVATER_CONFIG']['anchorId']
        vcn = current_app.config['AVATER_CONFIG']['vcn']
        
        authUrl = AipaasAuth.assemble_auth_url(url, 'GET', appKey, appSecret)
        wsclient = avatarWebsocket(authUrl, protocols='', headers=None)
        
        # 生成唯一的会话ID
        session_id = f"avatar_{int(time.time())}_{os.urandom(4).hex()}"
        wsclient.session_id = session_id
        
        wsclient.appId = appId
        wsclient.anchorId = anchorId
        wsclient.vcn = vcn
        wsclient.start()
        
        # 等待连接建立
        max_wait = 15
        start_time = time.time()
        while not wsclient.streamUrl and time.time() - start_time < max_wait:
            time.sleep(0.5)
        
        if wsclient.streamUrl:
            print(f"Avatar预加载成功，立即启动FFmpeg: {wsclient.streamUrl}")
            
            # 清理旧的HLS文件
            project_root = os.path.dirname(current_app.root_path)
            stream_folder_abs = os.path.join(project_root, 'resource', 'stream')
            delete_files_in_folder(stream_folder_abs)
            
            # 立即启动FFmpeg
            hls_file_path_abs = os.path.join(stream_folder_abs, 'playlist.m3u8')
            ffmpeg_process = rtmp_to_hls_fast_optimized(wsclient.streamUrl, hls_file_path_abs)
            
            if ffmpeg_process:
                # 等待HLS文件生成
                hls_ready = False
                wait_start = time.time()
                while time.time() - wait_start < 10:  # 最多等待10秒
                    if os.path.exists(hls_file_path_abs):
                        with open(hls_file_path_abs, 'r') as f:
                            if '.ts' in f.read():
                                hls_ready = True
                                break
                    time.sleep(0.5)
                
                return jsonify({
                    'success': True,
                    'message': 'Avatar预加载成功，数字人画面已就绪',
                    'preloaded': True,
                    'ffmpeg_started': True,
                    'hls_ready': hls_ready,
                    'data': {
                        'session_id': session_id,
                    'stream_url': wsclient.streamUrl,
                        'websocket_url': getattr(wsclient, 'websocketUrl', None),
                        'hls_path': '/interview/video/playlist.m3u8'
                    }
                })
            else:
                return jsonify({
                    'success': True,
                    'message': 'Avatar预加载成功，但FFmpeg启动失败',
                    'preloaded': True,
                    'ffmpeg_started': False,
                    'data': {
                        'session_id': session_id,
                        'stream_url': wsclient.streamUrl,
                        'websocket_url': getattr(wsclient, 'websocketUrl', None)
                    }
                })
        else:
            return jsonify({
                'success': False,
                'message': 'Avatar预加载超时'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Avatar预加载失败: {str(e)}'
        }), 500


@interview_bp.route('/use_preloaded_avatar', methods=['POST'])
def use_preloaded_avatar():
    """
    使用预加载的数字人会话
    """
    data = request.get_json()
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({
            'success': False,
            'message': '缺少session_id参数'
        }), 400
    
    global wsclient
    
    try:
        # 检查当前会话是否有效
        if wsclient is not None and not wsclient.is_session_expired():
            # 检查session_id是否匹配
            if getattr(wsclient, 'session_id', None) == session_id:
                # 会话有效且匹配，直接返回成功
                return jsonify({
                    'success': True,
                    'message': '使用预加载会话成功',
                    'stream_url': wsclient.streamUrl,
                    'websocket_url': wsclient.websocketUrl if hasattr(wsclient, 'websocketUrl') else None
                })
            else:
                # session_id不匹配，需要清理当前会话
                try:
                    wsclient.stop()
                except:
                    pass
                wsclient = None
        
        # 如果没有有效会话，返回错误
        return jsonify({
            'success': False,
            'message': '预加载会话无效或已过期',
            'error': 'invalid_session'
        }), 400
        
    except Exception as e:
        print(f"使用预加载会话时出错: {e}")
        return jsonify({
            'success': False,
            'message': f'使用预加载会话失败: {str(e)}'
        }), 500

@interview_bp.route('/reinit_avatar', methods=['POST'])
def reinit_avatar():
    """
    重新初始化数字人（不包括对话内容）
    仅重新建立WebSocket连接和视频流
    """
    global wsclient
    
    try:
        # 1. 清理旧连接
        if wsclient is not None:
            try:
                wsclient.stop()
            except:
                pass
            wsclient = None
        
        # 2. 清理旧的HLS文件
        project_root = os.path.dirname(current_app.root_path)
        stream_folder_abs = os.path.join(project_root, 'resource', 'stream')
        delete_files_in_folder(stream_folder_abs)
        
        # 3. 建立新连接
        url = current_app.config['AVATER_CONFIG']['url']
        appId = current_app.config['AVATER_CONFIG']['appId']
        appKey = current_app.config['AVATER_CONFIG']['appKey']
        appSecret = current_app.config['AVATER_CONFIG']['appSecret']
        anchorId = current_app.config['AVATER_CONFIG']['anchorId']
        vcn = current_app.config['AVATER_CONFIG']['vcn']
        
        authUrl = AipaasAuth.assemble_auth_url(url, 'GET', appKey, appSecret)
        wsclient = avatarWebsocket(authUrl, protocols='', headers=None)
        
        wsclient.appId = appId
        wsclient.anchorId = anchorId
        wsclient.vcn = vcn
        wsclient.start()
        
        # 4. 等待连接建立
        max_wait = 15
        start_time = time.time()
        while not wsclient.streamUrl and time.time() - start_time < max_wait:
            time.sleep(0.5)
        
        if not wsclient.streamUrl:
            raise Exception("Avatar连接超时")
        
        # 5. 启动FFmpeg
        hls_file_path_abs = os.path.join(stream_folder_abs, 'playlist.m3u8')
        ffmpeg_process = rtmp_to_hls_fast_optimized(wsclient.streamUrl, hls_file_path_abs)
        
        if ffmpeg_process is None:
            raise Exception("FFmpeg启动失败")
        
        # 6. 等待HLS文件生成
        hls_ready = False
        wait_start = time.time()
        while time.time() - wait_start < 10:  # 最多等待10秒
            if os.path.exists(hls_file_path_abs):
                with open(hls_file_path_abs, 'r') as f:
                    if '.ts' in f.read():
                        hls_ready = True
                        break
            time.sleep(0.5)
        
        return jsonify({
                'success': True,
                'message': '数字人重新初始化成功',
                'stream_url': wsclient.streamUrl,
                'websocket_url': getattr(wsclient, 'websocketUrl', None),
                'hls_ready': hls_ready
            })
        
    except Exception as e:
        print(f"重新初始化数字人失败: {e}")
        # 确保清理资源
        if wsclient is not None:
            try:
                wsclient.stop()
            except:
                pass
            wsclient = None
        
        return jsonify({
            'success': False,
            'message': f'重新初始化数字人失败: {str(e)}'
        }), 500

@interview_bp.route('/cleanup_avatar', methods=['POST'])
def cleanup_avatar():
    """
    清理数字人资源（断开WebSocket连接）
    """
    global wsclient
    
    try:
        if wsclient is not None:
            try:
                wsclient.stop()
            except Exception as e:
                print(f"停止WebSocket连接时出错: {e}")
            wsclient = None
        
        # 清理HLS文件
        project_root = os.path.dirname(current_app.root_path)
        stream_folder_abs = os.path.join(project_root, 'resource', 'stream')
        delete_files_in_folder(stream_folder_abs)
    
        return jsonify({
                'success': True,
                'message': '数字人资源已清理'
            })
        
    except Exception as e:
        print(f"清理数字人资源失败: {e}")
        
    return jsonify({
            'success': False,
            'message': f'清理数字人资源失败: {str(e)}'
        }), 500


@interview_bp.route('/recommend_learning_route', methods=['POST'])
def recommend_learning_route():
    """
    根据最新面试反馈和用户信息生成个性化学习路线推荐
    接收参数：
    - major: 用户专业
    - intention: 求职意向
    - job_description: 岗位描述
    """
    try:
        # 从POST请求中获取用户信息
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        major = data.get('major', '')
        intention = data.get('intention', '')
        job_description = data.get('job_description', '')
        
        # 验证必需参数
        if not all([major, intention]):
            return jsonify({
                'error': 'Missing required parameters: major and intention are required',
                'received': {
                    'major': major,
                    'intention': intention,
                    'job_description': job_description
                }
            }), 400
        
        print(f"接收到用户信息: 专业={major}, 意向={intention}, 岗位描述={job_description[:50]}...")

        # 查找最新的面试反馈文件
        feedback_folder = current_app.config.get('FEEDBACK_FOLDER_ROUTE', 'feedback')
        
        # 确保反馈文件夹存在
        if not os.path.exists(feedback_folder):
            print(f"反馈文件夹不存在: {feedback_folder}")
            return jsonify({
                'error': 'Feedback folder not found',
                'success': False,
                'learning_route': _generate_fallback_learning_route(major, intention),
                'user_info': {
                    'major': major,
                    'intention': intention,
                    'job_description': job_description[:100] + "..." if len(job_description) > 100 else job_description
                },
                'message': 'Generated fallback learning route due to missing feedback data'
            })
        
        print(f"查找反馈文件，文件夹: {feedback_folder}")
        
        feedback_data = None
        
        # 1. 优先查找增强版反馈文件
        enhanced_files = glob.glob(os.path.join(feedback_folder, "enhanced_feedback_*.json"))
        if enhanced_files:
            latest_enhanced_file = max(enhanced_files, key=os.path.getctime)
            print(f"找到增强版反馈文件: {latest_enhanced_file}")
            with open(latest_enhanced_file, 'r', encoding='utf-8') as f:
                feedback_data = json.load(f)
        else:
            # 2. 查找简单反馈文件
            txt_files = glob.glob(os.path.join(feedback_folder, "*.txt"))
            if txt_files:
                latest_file = max(txt_files, key=os.path.getctime)
                print(f"找到简单反馈文件: {latest_file}")
                with open(latest_file, 'r', encoding='utf-8') as f:
                    feedback_content = f.read()
                    try:
                        feedback_data = json.loads(feedback_content)
                    except json.JSONDecodeError:
                        feedback_data = {"text_feedback": feedback_content}
            else:
                print("未找到任何反馈文件")

        if not feedback_data:
            print("没有找到反馈数据，使用通用学习路线")
            fallback_route = _generate_fallback_learning_route(major, intention)
            return jsonify({
                'success': True,
                'learning_route': fallback_route,
                'user_info': {
                    'major': major,
                    'intention': intention,
                    'job_description': job_description[:100] + "..." if len(job_description) > 100 else job_description
                },
                'message': 'Generated general learning route (no feedback data found)',
                'warning': 'Using fallback recommendations'
            })

        # 读取学习路线推荐的 prompt 模板
        prompt_path = os.path.join(os.path.dirname(__file__), '../../../services', 'learning_route_prompt.txt')
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
        except FileNotFoundError:
            # 如果文件不存在，使用内置的 prompt
            prompt_template = """
根据面试反馈结果，为用户生成个性化的学习路线推荐。请返回一个JSON格式的学习资源映射，格式如下：
{
"学习内容描述": "学习资源链接",
"学习内容描述": "学习资源链接"
}

用户信息：
专业：{major}
求职意向：{intention}
岗位描述：{job_description}

面试反馈数据：
{feedback_summary}

请根据用户的专业背景、求职意向和面试反馈中的薄弱环节(主要针对薄弱环节)，推荐最相关的学习资源。
学习资源应该包括：
1. 在线课程（优先推荐B站、慕课网、极客时间等中文平台）
2. 技术书籍
3. 实战项目
4. 官方文档或教程

请确保推荐的内容具体、实用，链接真实有效。返回的JSON格式要规范，每个学习内容描述要清晰明确。
"""

        # 准备反馈摘要
        if isinstance(feedback_data, dict):
            if 'interview_summary' in feedback_data:
                feedback_summary = feedback_data['interview_summary']
            elif 'disadvantages' in feedback_data:
                # 提取主要薄弱环节
                disadvantages = feedback_data.get('disadvantages', [])
                feedback_summary = "主要薄弱环节：" + "；".join([item.get('title', '') + "：" + item.get('desc', '') for item in disadvantages[:3]])
            else:
                feedback_summary = json.dumps(feedback_data, ensure_ascii=False)[:500]  # 限制长度
        else:
            feedback_summary = str(feedback_data)[:500]

        # 构建完整的 prompt
        full_prompt = prompt_template.format(
            major=major,
            intention=intention,
            job_description=job_description,
            feedback_summary=feedback_summary
        )

        # 调用 DeepSeek API 生成学习路线
        response = DeepseekAPI.getInstance().chat_return_json(full_prompt)
        
        if not response:
            return jsonify({'error': 'Failed to generate learning route from DeepSeek API'}), 500

        # 解析 DeepSeek 返回的内容
        try:
            # 如果返回的是字符串，尝试解析为 JSON
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # 尝试解析 JSON
            if isinstance(content, str):
                # 提取JSON部分（可能包含其他文本）
                start_idx = content.find('{')
                end_idx = content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_content = content[start_idx:end_idx]
                    learning_route = json.loads(json_content)
                else:
                    # 如果没有找到JSON格式，返回错误
                    raise ValueError("No JSON format found in response")
            else:
                learning_route = content

            # 记录日志
            log_to_chat_file({
                "event": "Learning Route Generated",
                "user_major": major,
                "user_intention": intention,
                "learning_route_count": len(learning_route) if isinstance(learning_route, dict) else 0
            })

            return jsonify({
                'success': True,
                'learning_route': learning_route,
                'user_info': {
                    'major': major,
                    'intention': intention,
                    'job_description': job_description[:100] + "..." if len(job_description) > 100 else job_description
                },
                'message': 'Learning route generated successfully'
            })

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Failed to parse learning route JSON: {e}")
            print(f"Raw response: {content}")
            
            # 降级处理：返回通用学习建议
            fallback_route = _generate_fallback_learning_route(major, intention)
            return jsonify({
                'success': True,
                'learning_route': fallback_route,
                'user_info': {
                    'major': major,
                    'intention': intention,
                    'job_description': job_description[:100] + "..." if len(job_description) > 100 else job_description
                },
                'message': 'Generated fallback learning route due to parsing error',
                'warning': 'Used fallback recommendations'
            })

    except Exception as e:
        print(f"Learning route generation failed: {str(e)}")
        return jsonify({
            'error': f'Learning route generation failed: {str(e)}',
            'success': False
        }), 500


def _generate_fallback_learning_route(major, intention):
    """
    生成降级学习路线（当 AI 生成失败时使用）
    """
    fallback_routes = {
        "计算机": {
            "数据结构与算法基础": "https://www.bilibili.com/video/BV1H4411N7oD/",
            "计算机网络原理": "https://www.bilibili.com/video/BV19E411D78Q/",
            "操作系统原理": "https://www.bilibili.com/video/BV1YE411D7nH/",
            "数据库系统概念": "https://www.bilibili.com/video/BV1NJ411J79W/"
        },
        "软件工程": {
            "Java编程基础": "https://www.bilibili.com/video/BV12J41137hu/",
            "Spring框架学习": "https://www.bilibili.com/video/BV1WZ4y1P7Bp/",
            "MySQL数据库实战": "https://www.bilibili.com/video/BV1Kr4y1i7ru/",
            "前端开发入门": "https://www.bilibili.com/video/BV14J4114768/"
        },
        "默认": {
            "编程基础入门": "https://www.bilibili.com/video/BV1YW411x7eN/",
            "算法与数据结构": "https://www.bilibili.com/video/BV1H4411N7oD/",
            "计算机基础知识": "https://www.bilibili.com/video/BV19E411D78Q/",
            "项目实战练习": "https://github.com/topics/beginner-project"
        }
    }
    
    # 根据专业选择合适的学习路线
    for key in fallback_routes:
        if key in major:
            return fallback_routes[key]
    
    # 如果没有匹配的专业，返回默认路线
    return fallback_routes["默认"]
