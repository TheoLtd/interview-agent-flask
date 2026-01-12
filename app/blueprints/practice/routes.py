# from flask import Blueprint
# import datetime
import json
from flask import request, Response, jsonify, stream_with_context
import pypdf
import time
import docx
from io import BytesIO
from services.DeepSeek import DeepseekAPI
from services.SparkPractice import AIPracticeAPI
from services.SparkMbti import AIMbtiAPI
from services.SparkResumeRefination import AIResumeRefinationAPI
import os
from . import practice_bp

def load_resume_analysis_prompt(resume_content):
    """从文件加载简历分析提示词模板"""
    try:
        # 获取当前文件的目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构建services目录下的提示词文件路径
        prompt_file = os.path.join(current_dir, '..', '..', '..', 'services', 'resume_analysis_prompt.txt')
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        
        # debug code
        print("prompt_template.format(resume_content=resume_content): \n", prompt_template.format(resume_content=resume_content))
        
        # 替换模板中的占位符
        return prompt_template.format(resume_content=resume_content)
    except Exception as e:
        print(f"❌ 加载简历分析提示词失败: {e}")
        # 如果加载失败，返回一个简单的默认提示词
        return f"请分析以下简历内容并给出专业建议：\n\n{resume_content}"


@practice_bp.route('/answer', methods=['GET'])
def handle_answer():
    user_message = request.args.get('page', default=1, type=str)
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # 模拟流式输出
    def generate_response():
        responses = [
            '正在分析您的问题...\n',
            '根据您的描述，我认为...\n',
            '以下是我的建议：\n',
            '1. 首先...\n',
            '2. 其次...\n',
            '3. 最后...\n'
        ]
        for resp in responses:
            time.sleep(0.5)  # 模拟处理延迟
            yield resp.encode('utf-8')
    
    return Response(generate_response(), mimetype='text/event-stream')


@practice_bp.route('/answer_v1', methods=['GET', 'POST'])
def handle_answer_v1():
    # 支持GET和POST两种方式
    if request.method == 'POST':
        # POST方式：从请求体获取数据
        if request.is_json:
            user_message = request.json.get('prompt', '')
        else:
            user_message = request.form.get('prompt', '')
    else:
        # GET方式：从URL参数获取数据（保持向后兼容）
        user_message = request.args.get('prompt', default="", type=str)
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    print(f"📝 刷题对话 - 消息长度: {len(user_message)} 字符")
    
    if user_message:
        AIPractice = AIPracticeAPI.getInstance()
        res = AIPractice.get_answer(user_message)
        print(res)
        if res:
            return jsonify({'content': res})
        else:
            return jsonify({'error': 'AIPractice API error'}), 500


@practice_bp.route('/evaluate', methods=['GET', 'POST'])
def evaluate():
    # 支持GET和POST两种方式
    if request.method == 'POST':
        # POST方式：从请求体获取数据
        if request.is_json:
            history_data = request.json.get('historyData', '')
        else:
            history_data = request.form.get('historyData', '')
    else:
        # GET方式：从URL参数获取数据（保持向后兼容）
        history_data = request.args.get('historyData', default="", type=str)
    
    if not history_data:
        return jsonify({'error': 'No history_data provided'}), 400
    
    print(f"📊 历史数据长度: {len(history_data)} 字符")
    prompt = '''请根据我的根据历史刷题记录分析我的薄弱环节、高频错误点，并给出针对性的提升策略（如重点练习哪些题型、时间管理建议等）。要求分析简洁清晰，建议可操作性强。
                以下是我的历史刷题记录：
                <{}>
             '''.format(history_data)
    
    if history_data:
        Deepseek = DeepseekAPI.getInstance()
        res = Deepseek.safe_generate_content_deepseek2(prompt)
        print(res)
        print(res.text)
        if res:
            return jsonify({'content': res.text})
        else:
            return jsonify({'error': 'Deepseek API error'}), 500


@practice_bp.route('/evaluate_v2', methods=['GET'])
def evaluate_stream():
    # 支持GET和POST两种方式
    if request.method == 'POST':
        # POST方式：从请求体获取数据
        if request.is_json:
            history_data = request.json.get('historyData', '')
        else:
            history_data = request.form.get('historyData', '')
    else:
        # GET方式：从URL参数获取数据（保持向后兼容）
        history_data = request.args.get('historyData', default="", type=str)
    
    if not history_data:
        return jsonify({'error': 'No history_data provided'}), 400
    
    print(f"📊 流式评估 - 历史数据长度: {len(history_data)} 字符")
    prompt = '''请根据我的历史刷题记录分析我的薄弱环节、高频错误点，并给出针对性的提升策略（如重点练习哪些题型、时间管理建议等）。要求分析简洁清晰，建议可操作性强。
                以下是我的历史刷题记录：
                <{}>
             '''.format(history_data)
             
    def generate():
        stream = DeepseekAPI.getInstance().global_deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        all_text = ""
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                all_text += chunk.choices[0].delta.content
                print(all_text)
                yield f"data: {chunk.choices[0].delta.content}\n\n"
    return Response(generate(), mimetype='text/event-stream', headers = {'Cache-Control': 'no-cache','Connection': 'keep-alive'})


@practice_bp.route('/resume', methods=['POST'])
def handle_resume():
    """增强版简历优化接口"""
    print("🔄 收到简历分析请求")
    print(f"📝 请求方法: {request.method}")
    print(f"🌐 请求来源: {request.remote_addr}")
    print(f"📁 请求文件数量: {len(request.files)}")
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # 检查文件类型
        if not file.filename.lower().endswith(('.pdf', '.docx')):
            return jsonify({'error': 'Invalid file type. Only PDF and DOCX files are allowed.'}), 400
        
        # 解析文件内容
        content = ''
        if file.filename.lower().endswith('.pdf'):
            # debug code
            print("pdf file")
            pdf_reader = pypdf.PdfReader(BytesIO(file.read()))
            for page in pdf_reader.pages:
                content += page.extract_text() + '\n'
        elif file.filename.lower().endswith('.docx'):
            # debug code
            print("docx file")
            doc = docx.Document(BytesIO(file.read()))
            content = '\n'.join([para.text for para in doc.paragraphs])
        
        if not content.strip():
            return jsonify({'error': 'Failed to extract content from file'}), 400
        
        # 保存简历内容
        save_dir = os.path.join(os.path.dirname(__file__), '../../resource/resume')
        os.makedirs(save_dir, exist_ok=True)
        timestamp = int(time.time())
        filename = f"resume-{timestamp}.txt"
        filepath = os.path.join(save_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 从文件加载简历分析提示词模板
        enhanced_prompt = load_resume_analysis_prompt(content)
        
        print(f"📄 处理简历文件: {file.filename}")
        print(f"📝 简历内容长度: {len(content)} 字符")
        
        # # 使用DeepSeek API进行分析
        # deepseek = DeepseekAPI.getInstance()
        # response = deepseek.chat_return_json(enhanced_prompt)
        
        # 使用简历优化API进行分析
        AIResumeRefination = AIResumeRefinationAPI.getInstance()
        response_content = AIResumeRefination.get_answer(enhanced_prompt)
        
        # 创建与DeepSeek API兼容的响应对象
        class ResumeResponse:
            def __init__(self, content):
                self.content = content
        
        response = ResumeResponse(response_content) if response_content else None
        
        if response and response.content:
            try:
                # debug code
                print("开始尝试解析简历分析结果")
                
                # 尝试解析JSON响应
                analysis_result = json.loads(response.content)
                
                # 保存分析结果
                analysis_filename = f"resume_analysis_{timestamp}.json"
                analysis_filepath = os.path.join(save_dir, analysis_filename)
                
                with open(analysis_filepath, 'w', encoding='utf-8') as f:
                    json.dump(analysis_result, f, ensure_ascii=False, indent=2)
                
                return jsonify({
                    'success': True,
                    'content': analysis_result,
                    'type': 'enhanced_analysis',
                    'files': {
                        'resume': filename,
                        'analysis': analysis_filename
                    },
                    'message': 'Enhanced resume analysis completed successfully'
                })
                
            except json.JSONDecodeError:
                print("非json格式, 使用原始文本")
                # 如果不是JSON格式，使用原始文本
                return jsonify({
                    'success': True,
                    'content': {
                        'analysis_text': response.content,
                        'summary': response.content[:200] + '...' if len(response.content) > 200 else response.content
                    },
                    'type': 'text_analysis',
                    'files': {'resume': filename},
                    'message': 'Resume analysis completed (text format)'
                })
        else:
            return jsonify({'error': 'AI analysis service unavailable'}), 500
    
    except Exception as e:
        print(f"Resume analysis error: {str(e)}")
        return jsonify({
            'error': f'Resume analysis failed: {str(e)}',
            'suggestion': 'Please try again or contact support'
        }), 500


@practice_bp.route('/mbti_test', methods=['GET', 'POST'])
def mbti_test():
    # 支持GET和POST两种方式
    if request.method == 'POST':
        # POST方式：从请求体获取数据
        if request.is_json:
            user_message = request.json.get('prompt', '').strip()
        else:
            user_message = request.form.get('prompt', '').strip()
    else:
        # GET方式：从URL参数获取数据（保持向后兼容）
        user_message = request.args.get('prompt', default="", type=str).strip()
    
    # 如果用户未提供额外信息，给予默认提示，方便模型自行发问或直接给出结果
    if not user_message:
        user_message = "（用户暂未提供额外信息，请先提出合适的问题或根据通用情况预测 MBTI 类型）"

    print(f"🧠 MBTI测试 - 消息长度: {len(user_message)} 字符")

    # 构造 Prompt，将用户输入拼接进去
    mbti_prompt = f"""你是一名专业心理测评师，请参考下方用户信息判断其可能的 MBTI 类型，并给出简要的类型解析与职业建议；若用户信息不足，可先给出不超过 10 道带选项的问题，随后直接给出最终结论。
## 用户信息
{user_message}

## 输出规则
1. **格式要求**：必须使用Markdown结构化输出
2. **长度控制**：总输出不超过200字
3. **内容分级**：按优先级标注（mbti类型, 简单的性格分析, 适合的职业）
    """

    AIMbti = AIMbtiAPI.getInstance()
    res = AIMbti.get_answer(mbti_prompt)
    print(res)
    if res:
        return jsonify({'content': res})
    else:
        return jsonify({'error': 'MBTI API error'}), 500