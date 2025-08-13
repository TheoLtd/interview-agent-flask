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
        if wsclient is not None:
            wsclient.sendDriverText(text)
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
    初始化数字人，获取推流地址并转换为HLS
    """
    # 在每次初始化数字人时，先清空上一轮生成的 HLS 缓存文件，避免旧切片干扰
    project_root = os.path.dirname(current_app.root_path)
    stream_folder_abs = os.path.join(project_root, 'resource', 'stream')
    delete_files_in_folder(stream_folder_abs)
    global wsclient
    if wsclient is not None:
        print("启动process")
        rtmp_to_hls(wsclient.streamUrl, current_app.config['HLS_FOLDER_FILE'])
        return jsonify({'content': "true"})
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
        while not wsclient.streamUrl:
            time.sleep(1)
            pass
        print(wsclient.streamUrl)
        
        # 使用绝对路径确保路径一致性
        project_root = os.path.dirname(current_app.root_path)
        hls_folder_abs = os.path.join(project_root, 'resource', 'stream')
        hls_file_path_abs = os.path.join(hls_folder_abs, 'playlist.m3u8')
        
        # 传递绝对路径给 ffmpeg
        rtmp_to_hls(wsclient.streamUrl, hls_file_path_abs)

        # 等待HLS播放列表文件被FFmpeg创建
        timeout = 25  # 秒
        start_time = time.time()
        while not os.path.exists(hls_file_path_abs):
            if time.time() - start_time > timeout:
                print("错误：等待HLS播放列表文件超时")
                return jsonify({'error': '创建HLS流超时'}), 500
            time.sleep(0.5)
        
        print("HLS播放列表文件已找到，推流准备就绪")
        return jsonify({'content': "true"})
    except Exception as e:
        print(f"初始化数字人时发生错误: {e}")
        return jsonify({'error': '初始化数字人失败'}), 500

def rtmp_to_hls(input_rtmp_url, output_hls_path):
    """
    将 RTMP 流转换为 HLS 格式, 并将日志输出到文件

    参数:
        input_rtmp_url: 输入RTMP地址 (e.g. "rtmp://example.com/live/stream")
        output_hls_path: 输出HLS目录和文件名 (e.g. "static/stream/playlist.m3u8")
    """

    ffmpeg_cmd = [
        'ffmpeg',
        '-loglevel', 'error',          # 设置日志级别为error
        '-i', input_rtmp_url,          # 输入源
        '-c:v', 'libx264',             # 视频编码
        '-c:a', 'aac',                 # 音频编码
        '-f', 'hls',                   # 输出格式为HLS
        '-hls_time', '1',              # 每个TS切片2秒
        '-hls_list_size', '6',         # 播放列表保留3个片段
        '-hls_flags', 'delete_segments+append_list', # 自动删除旧片段
        output_hls_path                # 输出路径
    ]
    try:
        # 确保日志目录存在
        log_dir = os.path.join('log', 'ffmpeg_log')
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建带时间戳的日志文件名
        timestamp = int(time.time())
        log_file_name = f"ffmpeg_{timestamp}.log"
        log_file_path = os.path.join(log_dir, log_file_name)

        print(f"启动FFmpeg，日志将记录到 {log_file_path}")

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
    # 从 session 中获取用户信息
    user_id = session.get('user_id', 1)
    
    # 从数据库中获取最新的面试历史记录
    user_info = session.get('user_info')
    if not user_info:
        # # 调试代码
        # print("User info not initialized in session")
        return jsonify({'error': 'User info not initialized in session'}), 400

    if len(user_info['deepseek_history'])<=3:
        # # 调试代码
        # print("no history")
        return jsonify({'error': 'no history'}), 400

    # 读取 prompt.txt 内容
    prompt_path = os.path.join(os.path.dirname(__file__), '../../../services', 'feedbackPrompt.txt')
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()
            history_str = json.dumps(user_info['deepseek_history'][3:], ensure_ascii=False)
            prompt += history_str
    except Exception as e:
        return jsonify({'error': f'Failed to read prompt.txt: {str(e)}'}), 500
    try:
        response = DeepseekAPI.getInstance().chat_return_json(prompt)
        if response:
            log_to_chat_file({"event": "Feedback Generated", "feedback_response": response.content})
            timestamp = int(time.time())
            filename = f"feedback-{timestamp}.txt"
            filepath = os.path.join(current_app.config['FEEDBACK_FOLDER_ROUTE'], filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(response.content)
    except Exception as e:
        return jsonify({'error': f'调用DeepseekAPI失败: {str(e)}'}), 500
    return jsonify({'content': response.content})

@interview_bp.route('/feedback2', methods=['GET'])
def feedback2():
    # 从 session 获取用户信息和表情列表
    user_info = session.get('user_info', {})
    facial_expression_list = session.get('facial_expression_list', [])

    txt_files = glob.glob(os.path.join(current_app.config['FEEDBACK_FOLDER_ROUTE'], "*.txt"))

    if not txt_files:
        return "No feedback files found."

    latest_file = max(txt_files, key=os.path.getctime)

    with open(latest_file, 'r', encoding='utf-8') as f:
        feedback_content = f.read()

    response = f"""
    <p><strong>面试反馈:</strong></p>
    <p>{feedback_content}</p>
    <p><strong>major:</strong> {user_info.get('major', 'N/A')}</p>
    <p><strong>intention:</strong> {user_info.get('intention', 'N/A')}</p>
    <p><strong>job_description:</strong> {user_info.get('job_description', 'N/A')}</p>
    <p><strong>facial_expression_list:</strong> {facial_expression_list}</p>
    """
    return response


def delete_files_in_folder(folder_path):
    files = glob.glob(os.path.join(folder_path, '*'))
    for f in files:
        if os.path.isfile(f):
            os.remove(f)
