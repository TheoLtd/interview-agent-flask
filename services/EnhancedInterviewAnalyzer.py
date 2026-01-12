# -*- coding: utf-8 -*-
"""
增强版面试分析器
参考langgraph-AI-interview-agent项目的评估方法
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass
from .DeepSeek import DeepseekAPI
import numpy as np


@dataclass
class InterviewScore:
    """面试评分数据结构"""
    technical_knowledge: int  # 技术基础知识
    job_matching: int         # 岗位匹配度
    communication: int        # 语言表达
    logical_thinking: int     # 逻辑思维
    innovation: int          # 创新能力
    stress_resistance: int   # 抗压能力
    
    @property
    def average_score(self) -> int:
        scores = [
            self.technical_knowledge, self.job_matching, self.communication,
            self.logical_thinking, self.innovation, self.stress_resistance
        ]
        return round(sum(scores) / len(scores))
    
    @property
    def score_list(self) -> List[int]:
        return [
            self.technical_knowledge, self.job_matching, self.communication,
            self.logical_thinking, self.innovation, self.stress_resistance
        ]


@dataclass
class EmotionalAnalysis:
    """表情分析数据结构"""
    total_detections: int
    emotion_distribution: List[int]  # [其他, 其他表情, 喜悦, 愤怒, 悲伤, 惊恐, 厌恶, 中性]
    
    @property
    def emotion_percentages(self) -> Dict[str, float]:
        """计算各表情占比"""
        labels = ["其他", "其他表情", "喜悦", "愤怒", "悲伤", "惊恐", "厌恶", "中性"]
        total = sum(self.emotion_distribution)
        if total == 0:
            return {label: 0.0 for label in labels}
        
        return {
            labels[i]: round((count / total) * 100, 1) 
            for i, count in enumerate(self.emotion_distribution)
        }
    
    @property
    def emotional_stability_score(self) -> int:
        """计算情绪稳定性得分"""
        percentages = self.emotion_percentages
        
        # 积极情绪权重
        positive_weight = percentages.get("喜悦", 0) * 1.0 + percentages.get("中性", 0) * 0.8
        
        # 消极情绪权重
        negative_weight = (
            percentages.get("愤怒", 0) * -1.0 + 
            percentages.get("悲伤", 0) * -0.8 + 
            percentages.get("惊恐", 0) * -0.6 + 
            percentages.get("厌恶", 0) * -0.7
        )
        
        # 基础分数 + 情绪调整
        base_score = 70
        emotional_adjustment = (positive_weight + negative_weight) * 0.3
        
        final_score = base_score + emotional_adjustment
        return max(0, min(100, round(final_score)))


class EnhancedInterviewAnalyzer:
    """增强版面试分析器"""
    
    def __init__(self):
        self.deepseek_api = DeepseekAPI.getInstance()
        self.evaluation_dimensions = [
            "技术基础知识", "岗位匹配度", "语言表达", 
            "逻辑思维", "创新能力", "抗压能力"
        ]
    
    def analyze_interview_performance(
        self, 
        interview_history: List[Dict], 
        user_info: Dict,
        facial_expressions: List[int] = None
    ) -> Dict[str, Any]:
        """
        综合分析面试表现
        
        Args:
            interview_history: 面试对话历史
            user_info: 用户信息 (major, intention, job_description)
            facial_expressions: 表情统计列表
            
        Returns:
            完整的面试分析报告
        """
        try:
            # 1. 基础对话分析
            conversation_analysis = self._analyze_conversation_content(
                interview_history, user_info
            )
            
            # 2. 表情分析
            emotional_analysis = None
            if facial_expressions:
                emotional_analysis = self._analyze_facial_expressions(facial_expressions)
            
            # 3. 综合评分计算
            final_scores = self._calculate_comprehensive_scores(
                conversation_analysis, emotional_analysis
            )
            
            # 4. 生成个性化建议
            recommendations = self._generate_personalized_recommendations(
                conversation_analysis, emotional_analysis, user_info
            )
            
            # 5. 生成雷达图数据
            radar_data = self._generate_radar_chart_data(final_scores)
            
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "overall_score": final_scores.average_score,
                "scores": final_scores.score_list,
                "score_breakdown": {
                    "技术基础知识": final_scores.technical_knowledge,
                    "岗位匹配度": final_scores.job_matching,
                    "语言表达": final_scores.communication,
                    "逻辑思维": final_scores.logical_thinking,
                    "创新能力": final_scores.innovation,
                    "抗压能力": final_scores.stress_resistance
                },
                "advantages": conversation_analysis.get("advantages", []),
                "disadvantages": conversation_analysis.get("disadvantages", []),
                "emotional_analysis": emotional_analysis.__dict__ if emotional_analysis else None,
                "recommendations": recommendations,
                "radar_data": radar_data,
                "interview_summary": self._generate_interview_summary(
                    final_scores, emotional_analysis, user_info
                )
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"面试分析失败: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_conversation_content(self, interview_history: List[Dict], user_info: Dict) -> Dict:
        """分析对话内容"""
        
        # 构建更专业的分析提示词，参考langgraph项目
        enhanced_prompt = f"""
你是一名资深的技术面试官和HR专家，拥有10年以上的人才评估经验。请根据以下面试对话，进行专业的多维度评估。

## 📋 **评估维度与标准**

### 1. 技术基础知识 (Technical Knowledge)
- **概念理解**: 对技术概念、框架、工具的理解深度
- **实践经验**: 是否有实际项目经验支撑理论知识
- **技术广度**: 技术栈的完整性和前沿性
- **学习能力**: 对新技术的学习和适应能力

### 2. 岗位匹配度 (Job Fit)
- **技能匹配**: 技能组合与岗位要求的契合度
- **经验相关性**: 过往经验与目标岗位的关联性
- **成长潜力**: 候选人的发展空间和岗位成长匹配度
- **文化适应**: 对公司文化和团队协作的理解

### 3. 语言表达 (Communication)
- **表达清晰度**: 能否清晰、准确地表达技术概念
- **结构化思维**: 回答是否有逻辑层次和条理
- **专业术语使用**: 技术术语使用的准确性和恰当性
- **互动能力**: 与面试官的沟通互动质量

### 4. 逻辑思维 (Logical Thinking)
- **问题分析**: 分析问题的系统性和全面性
- **解决方案**: 提出解决方案的逻辑性和可行性
- **因果关系**: 对技术选型、架构设计的推理能力
- **批判性思维**: 对问题的深度思考和质疑能力

### 5. 创新能力 (Innovation)
- **创新思维**: 对问题的创新性解决思路
- **技术前瞻**: 对技术发展趋势的敏感度
- **优化意识**: 对现有方案的改进和优化思路
- **学习探索**: 主动学习和探索新技术的意愿

### 6. 抗压能力 (Stress Resistance)
- **压力处理**: 面对挑战性问题时的冷静程度
- **问题适应**: 对不熟悉问题的应对策略
- **情绪控制**: 在紧张环境下的情绪管理能力
- **韧性表现**: 面对挫折和困难的坚持能力

## 📥 **候选人信息**
- **专业背景**: {user_info.get('major', 'N/A')}
- **求职意向**: {user_info.get('intention', 'N/A')}
- **目标岗位**: {user_info.get('job_description', 'N/A')}

## 💬 **面试对话记录**
{json.dumps(interview_history, ensure_ascii=False, indent=2)}

## 📊 **输出要求**

请严格按照以下JSON格式输出评估结果：

```json
{{
  "scores": [技术基础知识分数, 岗位匹配度分数, 语言表达分数, 逻辑思维分数, 创新能力分数, 抗压能力分数],
  "advantages": [
    {{
      "title": "优势标题",
      "desc": "具体描述，包含行为证据和具体表现，30-100字",
      "category": "技术基础知识|岗位匹配度|语言表达|逻辑思维|创新能力|抗压能力"
    }}
  ],
  "disadvantages": [
    {{
      "title": "改进点标题", 
      "desc": "具体描述和改进建议，30-100字",
      "category": "技术基础知识|岗位匹配度|语言表达|逻辑思维|创新能力|抗压能力",
      "improvement_suggestion": "具体的改进建议"
    }}
  ],
  "overall_assessment": "整体评价，总结候选人的综合表现，100-200字"
}}
```

## ⚠️ **评分标准**
- 90-100分: 优秀，明显超出岗位要求
- 80-89分: 良好，满足岗位要求且有亮点
- 70-79分: 合格，基本满足岗位要求
- 60-69分: 一般，部分满足要求但有明显不足
- 60分以下: 不合格，存在重大问题或基础薄弱

请基于具体的对话内容进行客观、专业的评估。
"""
        
        try:
            response = self.deepseek_api.chat_return_json(enhanced_prompt)
            if response and response.content:
                return json.loads(response.content)
            else:
                return self._get_default_conversation_analysis()
        except Exception as e:
            print(f"对话内容分析失败: {e}")
            return self._get_default_conversation_analysis()
    
    def _analyze_facial_expressions(self, facial_expressions: List[int]) -> EmotionalAnalysis:
        """分析表情数据"""
        total_detections = sum(facial_expressions)
        
        return EmotionalAnalysis(
            total_detections=total_detections,
            emotion_distribution=facial_expressions
        )
    
    def _calculate_comprehensive_scores(
        self, 
        conversation_analysis: Dict, 
        emotional_analysis: EmotionalAnalysis = None
    ) -> InterviewScore:
        """计算综合评分"""
        
        base_scores = conversation_analysis.get("scores", [70, 70, 70, 70, 70, 70])
        
        # 确保有6个分数
        while len(base_scores) < 6:
            base_scores.append(70)
        
        # 表情分析对抗压能力的影响
        if emotional_analysis:
            emotional_score = emotional_analysis.emotional_stability_score
            # 抗压能力分数调整 (索引5)
            base_scores[5] = round((base_scores[5] * 0.7) + (emotional_score * 0.3))
        
        return InterviewScore(
            technical_knowledge=base_scores[0],
            job_matching=base_scores[1], 
            communication=base_scores[2],
            logical_thinking=base_scores[3],
            innovation=base_scores[4],
            stress_resistance=base_scores[5]
        )
    
    def _generate_personalized_recommendations(
        self, 
        conversation_analysis: Dict,
        emotional_analysis: EmotionalAnalysis,
        user_info: Dict
    ) -> List[Dict]:
        """生成个性化建议"""
        
        recommendations = []
        
        # 基于对话分析的建议
        disadvantages = conversation_analysis.get("disadvantages", [])
        for item in disadvantages:
            if "improvement_suggestion" in item:
                recommendations.append({
                    "type": "technical",
                    "title": f"改进建议: {item['title']}",
                    "content": item["improvement_suggestion"],
                    "priority": "high" if "技术" in item.get("category", "") else "medium"
                })
        
        # 基于表情分析的建议
        if emotional_analysis:
            emotion_percentages = emotional_analysis.emotion_percentages
            
            if emotion_percentages.get("惊恐", 0) > 20:
                recommendations.append({
                    "type": "emotional",
                    "title": "压力管理建议",
                    "content": "面试中表现出较多紧张情绪，建议加强面试技巧训练，通过模拟练习提升自信心",
                    "priority": "medium"
                })
            
            if emotion_percentages.get("中性", 0) < 30:
                recommendations.append({
                    "type": "emotional", 
                    "title": "情绪表达建议",
                    "content": "适当的情绪表达有助于建立良好的沟通氛围，建议在保持专业的同时展现更多积极情绪",
                    "priority": "low"
                })
        
        # 基于专业背景的建议
        major = user_info.get("major", "")
        intention = user_info.get("intention", "")
        
        if major and intention:
            recommendations.append({
                "type": "career",
                "title": "职业发展建议",
                "content": f"基于{major}专业背景和{intention}求职意向，建议重点提升相关技术栈的深度，关注行业最新发展趋势",
                "priority": "medium"
            })
        
        return recommendations[:5]  # 限制建议数量
    
    def _generate_radar_chart_data(self, scores: InterviewScore) -> List[Dict]:
        """生成雷达图数据"""
        
        dimensions = [
            {"label": "技术基础", "value": scores.technical_knowledge, "color": "#3b82f6"},
            {"label": "岗位匹配", "value": scores.job_matching, "color": "#ef4444"},
            {"label": "语言表达", "value": scores.communication, "color": "#10b981"},
            {"label": "逻辑思维", "value": scores.logical_thinking, "color": "#f59e0b"},
            {"label": "创新能力", "value": scores.innovation, "color": "#8b5cf6"},
            {"label": "抗压能力", "value": scores.stress_resistance, "color": "#06b6d4"}
        ]
        
        return dimensions
    
    def _generate_interview_summary(
        self, 
        scores: InterviewScore,
        emotional_analysis: EmotionalAnalysis,
        user_info: Dict
    ) -> str:
        """生成面试总结"""
        
        avg_score = scores.average_score
        
        if avg_score >= 85:
            performance_level = "优秀"
            summary_prefix = "表现优异，各项能力均达到较高水准"
        elif avg_score >= 75:
            performance_level = "良好"
            summary_prefix = "整体表现良好，具备岗位所需的基本能力"
        elif avg_score >= 65:
            performance_level = "一般"
            summary_prefix = "基本符合要求，但仍有提升空间"
        else:
            performance_level = "需要改进"
            summary_prefix = "存在一些不足，需要重点提升相关能力"
        
        # 找出最强和最弱的维度
        score_dict = {
            "技术基础知识": scores.technical_knowledge,
            "岗位匹配度": scores.job_matching,
            "语言表达": scores.communication,
            "逻辑思维": scores.logical_thinking,
            "创新能力": scores.innovation,
            "抗压能力": scores.stress_resistance
        }
        
        strongest = max(score_dict, key=score_dict.get)
        weakest = min(score_dict, key=score_dict.get)
        
        emotional_summary = ""
        if emotional_analysis:
            emotion_percentages = emotional_analysis.emotion_percentages
            if emotion_percentages.get("喜悦", 0) > 15:
                emotional_summary = "，面试过程中情绪表现积极"
            elif emotion_percentages.get("惊恐", 0) > 20:
                emotional_summary = "，面试过程中略显紧张"
            else:
                emotional_summary = "，面试过程中情绪表现平稳"
        
        return f"{summary_prefix}。在{strongest}方面表现突出，{weakest}方面有待加强{emotional_summary}。综合评分{avg_score}分，整体水平{performance_level}。"
    
    def _get_default_conversation_analysis(self) -> Dict:
        """获取默认的对话分析结果"""
        return {
            "scores": [70, 70, 70, 70, 70, 70],
            "advantages": [
                {
                    "title": "基础表达",
                    "desc": "能够进行基本的技术交流和问题回答",
                    "category": "语言表达"
                }
            ],
            "disadvantages": [
                {
                    "title": "分析不足",
                    "desc": "面试时间较短或回答内容有限，建议提供更详细的技术描述",
                    "category": "技术基础知识",
                    "improvement_suggestion": "增加具体项目经验的分享，提供更多技术细节"
                }
            ],
            "overall_assessment": "由于面试内容有限，评估结果仅供参考。建议进行更深入的技术交流以获得更准确的评估。"
        } 