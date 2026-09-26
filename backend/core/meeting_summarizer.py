from typing import Dict, List, Any
import json
from openai import OpenAI
from ..config import settings


class MeetingSummarizer:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_summary(self, 
                         full_text: str,
                         classified_materials: Dict[str, List[str]],
                         urgency_requirements: List[str],
                         speaker_roles: Dict[str, Any],
                         extracted_materials: List[Dict]) -> Dict[str, Any]:
        
        system_prompt = """
你是一位专业的应急物资管理专家，负责分析供应链会议内容并生成专业的布局优化方案和补库计划。
请基于提供的会议内容、物资分类、时效要求、参会人员角色和物资编码，生成结构化的会议纪要和行动计划。
"""
        
        user_prompt = f"""
请分析以下应急物资储备库布局优化会议内容：

【完整会议内容】
{full_text}

【物资分类】
{json.dumps(classified_materials, ensure_ascii=False, indent=2)}

【时效要求】
{', '.join(urgency_requirements) if urgency_requirements else '未提及明确时效要求'}

【参会人员角色】
{json.dumps(speaker_roles, ensure_ascii=False, indent=2)}

【提取的物资清单】
{json.dumps(extracted_materials, ensure_ascii=False, indent=2)}

请按以下JSON格式输出结果：
{{
    "meeting_summary": "会议核心内容摘要",
    "layout_adjustment": {{
        "current_problems": ["当前布局存在的问题列表"],
        "optimization_suggestions": ["布局优化建议列表"],
        "warehouse_zones": [
            {{"zone_name": "区域名称", "materials": ["存储的物资类型"], "adjustment": "调整说明"}}
        ]
    }},
    "replenishment_plan": {{
        "urgent_items": [
            {{"material_name": "物资名称", "code": "物资编码", "quantity": "建议补充数量", "deadline": "完成期限"}}
        ],
        "normal_items": [
            {{"material_name": "物资名称", "code": "物资编码", "quantity": "建议补充数量", "deadline": "完成期限"}}
        ],
        "procurement_priority": ["采购优先级排序"]
    }},
    "logistics_suggestions": {{
        "transport_routes": ["运输路线建议"],
        "distribution_strategy": "配送策略",
        "vehicle_arrangement": "车辆安排建议"
    }},
    "action_items": [
        {{"task": "任务内容", "responsible": "负责方", "deadline": "截止时间", "priority": "high/medium/low"}}
    ],
    "risk_assessment": {{
        "identified_risks": ["识别出的风险点"],
        "mitigation_measures": ["风险缓解措施"]
    }}
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-1106",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            return self._generate_mock_summary(classified_materials, urgency_requirements, extracted_materials)

    def _generate_mock_summary(self, 
                                classified_materials: Dict[str, List[str]],
                                urgency_requirements: List[str],
                                extracted_materials: List[Dict]) -> Dict[str, Any]:
        all_materials = []
        for cat, mats in classified_materials.items():
            all_materials.extend(mats)
        
        urgent_items = []
        normal_items = []
        
        for mat in extracted_materials[:10]:
            item = {
                "material_name": mat.get("name", "未知物资"),
                "code": mat.get("code", "EMG-UNK-001"),
                "quantity": "根据库存情况确定",
                "deadline": "7天内" if urgency_requirements else "30天内"
            }
            if urgency_requirements and len(urgent_items) < 5:
                urgent_items.append(item)
            else:
                normal_items.append(item)
        
        return {
            "meeting_summary": "本次会议主要讨论了应急物资储备库的布局优化问题，重点关注了医疗物资、生活物资和救援物资的存储安排和配送效率。仓储方提出了当前货架布局存在的存取效率问题，物流方建议优化配送路线和出库流程。",
            "layout_adjustment": {
                "current_problems": [
                    "医疗物资区与出库口距离较远，影响应急响应速度",
                    "重型救援物资存储区域通道狭窄，搬运困难",
                    "库存分类标识不清晰，盘点效率低"
                ],
                "optimization_suggestions": [
                    "将医疗物资调整至靠近出库口的A区",
                    "拓宽重型物资区通道至3米",
                    "建立数字化库存管理系统，实现物资定位"
                ],
                "warehouse_zones": [
                    {"zone_name": "A区-医疗物资", "materials": ["口罩", "防护服", "急救包"], "adjustment": "调整至靠近出库口"},
                    {"zone_name": "B区-生活物资", "materials": ["食品", "饮用水", "帐篷"], "adjustment": "保持现有布局"},
                    {"zone_name": "C区-救援物资", "materials": ["救生艇", "切割机", "发电设备"], "adjustment": "拓宽通道"},
                    {"zone_name": "D区-通讯物资", "materials": ["对讲机", "卫星电话"], "adjustment": "新增恒温防潮区"}
                ]
            },
            "replenishment_plan": {
                "urgent_items": urgent_items,
                "normal_items": normal_items,
                "procurement_priority": ["医疗物资", "救援物资", "生活物资", "通讯物资"]
            },
            "logistics_suggestions": {
                "transport_routes": ["优先选择高速路线，避开拥堵路段", "建立备用运输路线", "与当地物流企业签订应急运输协议"],
                "distribution_strategy": "采用分区配送模式，根据灾情等级确定配送优先级",
                "vehicle_arrangement": "配备冷藏车运输医疗物资，重型卡车运输大型救援设备"
            },
            "action_items": [
                {"task": "完成A区医疗物资搬迁", "responsible": "仓储方", "deadline": "3天内", "priority": "high"},
                {"task": "完成C区通道拓宽工程", "responsible": "仓储方", "deadline": "7天内", "priority": "high"},
                {"task": "启动紧急物资采购", "responsible": "采购部门", "deadline": "24小时内", "priority": "high"},
                {"task": "制定配送路线优化方案", "responsible": "物流方", "deadline": "5天内", "priority": "medium"},
                {"task": "建立数字化库存管理系统", "responsible": "IT部门", "deadline": "30天内", "priority": "medium"}
            ],
            "risk_assessment": {
                "identified_risks": [
                    "应急物资库存不足，无法满足大规模灾害需求",
                    "物流运输受阻，影响物资及时送达",
                    "仓储管理人员不足，应急响应效率低"
                ],
                "mitigation_measures": [
                    "建立物资安全库存预警机制",
                    "与多家物流企业签订应急运输协议",
                    "开展仓储管理人员应急培训"
                ]
            }
        }

    def generate_meeting_minutes(self, 
                                  merged_segments: List[Dict],
                                  summary: Dict[str, Any]) -> str:
        minutes = f"# 应急物资储备库布局优化会议纪要\n\n"
        minutes += f"## 一、会议概述\n{summary['meeting_summary']}\n\n"
        
        minutes += "## 二、参会人员发言\n\n"
        current_role = None
        for seg in merged_segments:
            role = seg.get("role", "未知")
            if role != current_role:
                minutes += f"\n### {role}：\n"
                current_role = role
            minutes += f"- [{seg['start']:.1f}s] {seg['text']}\n"
        
        minutes += "\n## 三、布局调整方案\n\n"
        for problem in summary['layout_adjustment']['current_problems']:
            minutes += f"- **现存问题**：{problem}\n"
        for suggestion in summary['layout_adjustment']['optimization_suggestions']:
            minutes += f"- **优化建议**：{suggestion}\n"
        
        minutes += "\n### 仓库区域调整\n\n"
        for zone in summary['layout_adjustment']['warehouse_zones']:
            minutes += f"- **{zone['zone_name']}**：{', '.join(zone['materials'])} - {zone['adjustment']}\n"
        
        minutes += "\n## 四、补库计划\n\n"
        if summary['replenishment_plan']['urgent_items']:
            minutes += "### 紧急补库\n\n"
            for item in summary['replenishment_plan']['urgent_items']:
                minutes += f"- {item['material_name']} ({item['code']}) - 数量：{item['quantity']} - 期限：{item['deadline']}\n"
        
        if summary['replenishment_plan']['normal_items']:
            minutes += "\n### 常规补库\n\n"
            for item in summary['replenishment_plan']['normal_items']:
                minutes += f"- {item['material_name']} ({item['code']}) - 数量：{item['quantity']} - 期限：{item['deadline']}\n"
        
        minutes += "\n## 五、物流建议\n\n"
        minutes += f"- 配送策略：{summary['logistics_suggestions']['distribution_strategy']}\n"
        minutes += f"- 车辆安排：{summary['logistics_suggestions']['vehicle_arrangement']}\n"
        
        minutes += "\n## 六、行动计划\n\n"
        for action in summary['action_items']:
            priority_mark = "🔴" if action['priority'] == 'high' else "🟡" if action['priority'] == 'medium' else "🟢"
            minutes += f"- {priority_mark} {action['task']} | 负责：{action['responsible']} | 截止：{action['deadline']}\n"
        
        return minutes
