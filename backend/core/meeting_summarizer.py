from typing import Dict, List, Any
import json
import re
from datetime import date, datetime, time, timedelta
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

    # ---------- generate_meeting_minutes 的辅助函数（模块级，便于测试） ----------

    def generate_meeting_minutes(self,
                                  merged_segments: List[Dict],
                                  summary: Dict[str, Any],
                                  *,
                                  deadline_base=None,
                                  action_item_order: str = "as_is") -> str:
        """把结构化 summary 和带角色的发言段渲染成 Markdown 会议纪要。

        参数
        ----
        merged_segments : List[Dict]
            带角色的发言段，位置参数名与顺序保持不变。
        summary : Dict[str, Any]
            大模型生成的结构化摘要，位置参数名与顺序保持不变。
        deadline_base : datetime.date 或 datetime.datetime，可选，默认 None
            相对期限的换算基准。为 None 时完全不做换算、不追加任何标记，
            期限原样输出（兼容底线）。传入后，「行动计划」和「补库计划」
            （紧急与常规两处）里形如「N小时内 / N天内 / N周内」的期限换算成
            YYYY-MM-DD；N 支持阿拉伯数字与中文数字（含「两」「十」组合）。
            已是 YYYY-MM-DD 或 YYYY/MM/DD 的原样输出，不二次换算。
            跨零点规则：date 基准按当日 00:00 计，datetime 基准按其实际时刻计，
            「N小时内」= 基准时刻 + N 小时后所在日历日。例如基准 2026-09-27
            （即 2026-09-27 00:00）时，「24小时内」落在次日 2026-09-28，
            「36小时内」落在 2026-09-28（次日 12:00 所在日）。
            其他类型一律按 None 处理，不抛异常。
        action_item_order : str，可选，默认 "as_is"
            "as_is" 保持 summary 里的原始顺序；"priority_deadline" 按
            优先级 high > medium > low 排序，priority 为未知值（urgent、P0、
            空字符串等）或缺键时排在 low 之后；同级按换算后的绝对期限升序。
            非法值（"by_task"、None、123 等）一律按 "as_is" 处理，不抛异常。
            排序只改顺序、不增删条目，且不修改调用方传入的列表。

        认不出的期限（"尽快"、"下个月"、"会后三天内"、"另行通知"等）：
        仅在传入 deadline_base 时，原样保留并追加统一标记「（日期待确认）」；
        缺键或空字符串渲染为占位「（期限未明确）」。不抛异常、不丢行。

        脏数据处理（一处脏数据最多影响它自己那一行，整份纪要不抛异常）：
        - priority 未知值或缺键：按「其余」渲染绿点，排序时排在 low 之后；
        - warehouse_zones 的 materials 是字符串：当作一条物资渲染，不逐字符拆；
          缺键或非列表非字符串：按空列表渲染；
        - 发言段 start 是数字字符串：按数字渲染并保留一位小数；
          不是数字或缺键：该行的 start 显示为占位「?」；
        - 缺 meeting_summary：按空值渲染（空字符串）；
        - 缺 action_items：按空列表渲染（「## 六、行动计划」标题仍保留）；
        - 缺 logistics_suggestions.vehicle_arrangement / distribution_strategy、
          条目缺 material_name/code/quantity/task/responsible、zone 缺
          zone_name/adjustment：渲染为占位「（未提供）」；
        - 发言段缺 role：沿用原行为按「未知」处理；缺 text：按空字符串渲染；
        - 缺整个子字典（layout_adjustment 等）：按空字典处理。
        """
        base = _normalize_base(deadline_base)
        order = action_item_order if action_item_order in ("as_is", "priority_deadline") else "as_is"

        minutes = f"# 应急物资储备库布局优化会议纪要\n\n"
        minutes += f"## 一、会议概述\n{_as_dict(summary).get('meeting_summary', '')}\n\n"

        minutes += "## 二、参会人员发言\n\n"
        current_role = None
        for seg in _as_list(merged_segments):
            seg = _as_dict(seg)
            role = seg.get("role", "未知")
            if role != current_role:
                minutes += f"\n### {role}：\n"
                current_role = role
            minutes += f"- [{_format_start(seg.get('start'))}s] {seg.get('text', '')}\n"

        layout = _as_dict(_as_dict(summary).get("layout_adjustment"))
        minutes += "\n## 三、布局调整方案\n\n"
        for problem in _as_list(layout.get("current_problems")):
            minutes += f"- **现存问题**：{problem}\n"
        for suggestion in _as_list(layout.get("optimization_suggestions")):
            minutes += f"- **优化建议**：{suggestion}\n"

        minutes += "\n### 仓库区域调整\n\n"
        for zone in _as_list(layout.get("warehouse_zones")):
            zone = _as_dict(zone)
            minutes += (
                f"- **{zone.get('zone_name', '（未提供）')}**："
                f"{', '.join(str(m) for m in _as_materials(zone.get('materials')))}"
                f" - {zone.get('adjustment', '（未提供）')}\n"
            )

        replenishment = _as_dict(_as_dict(summary).get("replenishment_plan"))
        minutes += "\n## 四、补库计划\n\n"
        urgent_items = _as_list(replenishment.get("urgent_items"))
        if urgent_items:
            minutes += "### 紧急补库\n\n"
            for item in urgent_items:
                minutes += _format_replenishment_item(item, base)

        normal_items = _as_list(replenishment.get("normal_items"))
        if normal_items:
            minutes += "\n### 常规补库\n\n"
            for item in normal_items:
                minutes += _format_replenishment_item(item, base)

        logistics = _as_dict(_as_dict(summary).get("logistics_suggestions"))
        minutes += "\n## 五、物流建议\n\n"
        minutes += f"- 配送策略：{logistics.get('distribution_strategy', '（未提供）')}\n"
        minutes += f"- 车辆安排：{logistics.get('vehicle_arrangement', '（未提供）')}\n"

        minutes += "\n## 六、行动计划\n\n"
        actions = [a for a in _as_list(_as_dict(summary).get("action_items"))]
        if order == "priority_deadline":
            actions = _sort_action_items(actions, base)
        for action in actions:
            action = _as_dict(action)
            priority = action.get("priority")
            priority_mark = "🔴" if priority == 'high' else "🟡" if priority == 'medium' else "🟢"
            minutes += (
                f"- {priority_mark} {action.get('task', '（未提供）')}"
                f" | 负责：{action.get('responsible', '（未提供）')}"
                f" | 截止：{_format_deadline(action.get('deadline'), base, missing='deadline' not in action)}\n"
            )

        return minutes


_MISSING = object()

_CHINESE_DIGITS = {
    "零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
}

_RELATIVE_DEADLINE_RE = re.compile(
    r"^\s*([0-9]+|[零一二两三四五六七八九十]+)\s*(小时|天|周|星期)\s*内\s*$"
)
_ABSOLUTE_DATE_RE = re.compile(r"^\s*(\d{4})[-/](\d{1,2})[-/](\d{1,2})\s*$")

_PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
_UNKNOWN_PRIORITY_RANK = 3


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _as_list(value):
    return value if isinstance(value, list) else []


def _as_materials(value):
    """materials 是字符串时当作一条物资；非列表非字符串按空列表。"""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return value
    return []


def _format_start(value):
    """数字（含数字字符串）保留一位小数；其余渲染为占位 ?。"""
    if isinstance(value, bool):
        return "?"
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return "?"


def _parse_chinese_number(text):
    """解析 0-99 的中文数字（含「两」「十」组合），无法解析返回 None。"""
    if not text:
        return None
    if "十" in text:
        left, _, right = text.partition("十")
        if left and left not in _CHINESE_DIGITS:
            return None
        if right and right not in _CHINESE_DIGITS:
            return None
        tens = _CHINESE_DIGITS.get(left, 1) if left else 1
        ones = _CHINESE_DIGITS.get(right, 0) if right else 0
        return tens * 10 + ones
    if text in _CHINESE_DIGITS:
        return _CHINESE_DIGITS[text]
    return None


def _parse_relative_deadline(text):
    """解析「N小时内 / N天内 / N周内」，返回 (小时数, ) 或 None。"""
    match = _RELATIVE_DEADLINE_RE.match(text)
    if not match:
        return None
    token, unit = match.group(1), match.group(2)
    if token.isdigit():
        n = int(token)
    else:
        n = _parse_chinese_number(token)
        if n is None:
            return None
    factor = 1 if unit == "小时" else 24 if unit == "天" else 24 * 7
    return n * factor


def _parse_absolute_date(text):
    match = _ABSOLUTE_DATE_RE.match(text)
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def _normalize_base(deadline_base):
    """date 按当日 00:00 计；datetime 按其实际时刻计；其他类型按 None。"""
    if isinstance(deadline_base, datetime):
        return deadline_base
    if isinstance(deadline_base, date):
        return datetime.combine(deadline_base, time.min)
    return None


def _format_deadline(raw, base, missing=False):
    """渲染期限文本。base 为 None 时原样输出，不换算也不追加标记。"""
    if missing or raw is None:
        return "（期限未明确）"
    text = raw if isinstance(raw, str) else str(raw)
    if not text.strip():
        return "（期限未明确）"
    stripped = text.strip()
    if _parse_absolute_date(stripped) is not None:
        return stripped
    if base is None:
        return stripped
    hours = _parse_relative_deadline(stripped)
    if hours is not None:
        return (base + timedelta(hours=hours)).date().isoformat()
    return f"{stripped}（日期待确认）"


def _deadline_sort_key(raw, base):
    """期限排序键：可解析的排前，认不出的排后。值可比较且确定。"""
    if isinstance(raw, str):
        text = raw.strip()
        absolute = _parse_absolute_date(text)
        if absolute is not None:
            return (0, absolute.toordinal())
        hours = _parse_relative_deadline(text)
        if hours is not None:
            if base is not None:
                return (0, (base + timedelta(hours=hours)).date().toordinal())
            return (1, hours)
    return (2, 0)


def _sort_action_items(actions, base):
    """按优先级与期限排序。只改顺序、不增删条目，不修改原列表。

    平局规则：优先级相同且期限排序键相同（含两条都认不出）时，
    保持它们在原列表中的先后顺序（显式按下标收尾，稳定且确定）。
    """
    indexed = list(enumerate(actions))
    indexed.sort(key=lambda pair: (
        _PRIORITY_RANK.get(_as_dict(pair[1]).get("priority"), _UNKNOWN_PRIORITY_RANK),
        _deadline_sort_key(_as_dict(pair[1]).get("deadline"), base),
        pair[0],
    ))
    return [action for _, action in indexed]


def _format_replenishment_item(item, base):
    item = _as_dict(item)
    deadline_missing = "deadline" not in item
    return (
        f"- {item.get('material_name', '（未提供）')}"
        f" ({item.get('code', '（未提供）')})"
        f" - 数量：{item.get('quantity', '（未提供）')}"
        f" - 期限：{_format_deadline(item.get('deadline'), base, missing=deadline_missing)}\n"
    )
