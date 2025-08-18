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
import os
from . import practice_bp


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


@practice_bp.route('/answer_v1', methods=['GET'])
def handle_answer_v1():
    user_message = request.args.get('prompt', default="", type=str)
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    if user_message:
        AIPractice = AIPracticeAPI.getInstance()
        res = AIPractice.get_answer(user_message)
        print(res)
        if res:
            return jsonify({'content': res})
        else:
            return jsonify({'error': 'Deepseek API error'}), 500


@practice_bp.route('/evaluate', methods=['GET'])
def evaluate():
    history_data = request.args.get('historyData', default="", type=str)
    if not history_data:
        return jsonify({'error': 'No history_data provided'}), 400
    
    print(history_data)
    prompt = '''请根据我的根据历史刷题记录分析我的薄弱环节、高频错误点，并给出针对性的提升策略（如重点练习哪些题型、时间管理建议等）。要求分析简洁清晰，建议可操作性强。
                以下是我的历史刷题记录：
                <{}>
             '''.format(history_data)
    print(prompt)
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
    history_data = request.args.get('historyData', default="", type=str)
    if not history_data:
        return jsonify({'error': 'No history_data provided'}), 400
    
    print(history_data)
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
            pdf_reader = pypdf.PdfReader(BytesIO(file.read()))
            for page in pdf_reader.pages:
                content += page.extract_text() + '\n'
        elif file.filename.lower().endswith('.docx'):
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
        
        # 构建增强版提示词
        enhanced_prompt = f"""
你是一名资深的HR专家和职业规划师，拥有15年以上的招聘和简历评估经验。请对以下简历进行全面、专业的分析和优化建议。

## 📋 **分析维度**

### 1. 简历结构与格式 (Resume Structure & Format)
- 版面设计的专业性和可读性
- 信息层次和逻辑结构
- 格式一致性和视觉效果

### 2. 内容完整性 (Content Completeness)
- 必要信息的完整程度
- 关键经历的覆盖面
- 技能和成就的展示

### 3. 专业匹配度 (Professional Alignment)
- 经历与目标岗位的匹配度
- 技能栈的相关性和深度
- 职业发展路径的清晰度

### 4. 成果量化 (Achievement Quantification)
- 工作成果的具体化程度
- 数据指标的运用
- 影响力的体现

### 5. 语言表达 (Language & Expression)
- 专业术语的准确性
- 表达的简洁有力
- 动词和描述的效果

## 📊 **输出要求**

请严格按照以下JSON格式输出分析结果：

```json
{{
  "overall_score": 整体评分(0-100),
  "dimension_scores": {{
    "structure_format": 结构格式分数(0-100),
    "content_completeness": 内容完整性分数(0-100),
    "professional_alignment": 专业匹配度分数(0-100),
    "achievement_quantification": 成果量化分数(0-100),
    "language_expression": 语言表达分数(0-100)
  }},
  "strengths": [
    {{
      "category": "优势类别",
      "title": "优势标题",
      "description": "具体描述，30-80字",
      "evidence": "支撑证据或具体表现"
    }}
  ],
  "improvements": [
    {{
      "category": "改进类别",
      "title": "改进点标题",
      "description": "问题描述，30-80字", 
      "suggestion": "具体改进建议，50-100字",
      "priority": "high|medium|low",
      "expected_impact": "预期改进效果"
    }}
  ],
  "optimization_recommendations": [
    {{
      "section": "简历部分(如教育背景、工作经历等)",
      "current_issue": "当前问题",
      "recommended_action": "具体优化行动",
      "example": "优化示例或模板"
    }}
  ],
  "keyword_suggestions": [
    "建议添加的关键词1",
    "建议添加的关键词2"
  ],
  "summary": "综合评价和建议，100-200字"
}}
```

## 💼 **简历内容**

{content}

请基于以上简历内容，进行深入、专业的分析，给出具体可操作的优化建议。
"""
        
        print(f"📄 处理简历文件: {file.filename}")
        print(f"📝 简历内容长度: {len(content)} 字符")
        
        # 使用DeepSeek API进行分析
        deepseek = DeepseekAPI.getInstance()
        response = deepseek.chat_return_json(enhanced_prompt)
        
        if response and response.content:
            try:
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
                # 如果不是JSON格式，使用原始文本
                return jsonify({
                    'success': True,
                    'content': {
                        'analysis_text': response.content,
                        'overall_score': 75,  # 默认分数
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


@practice_bp.route('/mbti_test', methods=['GET'])
def mbti_test():
    user_message = request.args.get('prompt', default="", type=str).strip()
    # 如果用户未提供额外信息，给予默认提示，方便模型自行发问或直接给出结果
    if not user_message:
        user_message = "（用户暂未提供额外信息，请先提出合适的问题或根据通用情况预测 MBTI 类型）"

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