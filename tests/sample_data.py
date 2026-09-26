"""合成样例数据：形状与 _generate_mock_summary 的产出一致，仅供离线测试使用。"""

SAMPLE_SEGMENTS = [
    {"start": 0.0, "end": 4.2, "text": "A区货架离出库口太远，应急响应受影响。", "role": "仓储方"},
    {"start": 4.2, "end": 9.8, "text": "重型物资区通道太窄，搬运困难。", "role": "仓储方"},
    {"start": 9.8, "end": 15.0, "text": "建议优化配送路线，避开拥堵路段。", "role": "物流方"},
    {"start": 15.0, "end": 20.5, "text": "医疗物资需要冷藏车运输。", "role": "物流方"},
    {"start": 20.5, "end": 26.1, "text": "紧急采购口罩和防护服。", "role": "采购部门"},
    {"start": 26.1, "end": 31.0, "text": "库存分类标识要重新做。", "role": "仓储方"},
]

SAMPLE_SUMMARY = {
    "meeting_summary": "本次会议讨论了应急物资储备库布局优化与补库安排。",
    "layout_adjustment": {
        "current_problems": [
            "医疗物资区与出库口距离较远",
            "库存分类标识不清晰",
        ],
        "optimization_suggestions": [
            "将医疗物资调整至靠近出库口的A区",
            "建立数字化库存管理系统",
        ],
        "warehouse_zones": [
            {"zone_name": "A区-医疗物资", "materials": ["口罩", "防护服", "急救包"], "adjustment": "调整至靠近出库口"},
            {"zone_name": "B区-生活物资", "materials": ["食品", "饮用水"], "adjustment": "保持现有布局"},
        ],
    },
    "replenishment_plan": {
        "urgent_items": [
            {"material_name": "医用口罩", "code": "EMG-MED-001", "quantity": "5000只", "deadline": "24小时内"},
        ],
        "normal_items": [
            {"material_name": "帐篷", "code": "EMG-LIF-004", "quantity": "80顶", "deadline": "30天内"},
        ],
        "procurement_priority": ["医疗物资"],
    },
    "logistics_suggestions": {
        "transport_routes": ["优先选择高速路线"],
        "distribution_strategy": "采用分区配送模式",
        "vehicle_arrangement": "配备冷藏车运输医疗物资",
    },
    "action_items": [
        {"task": "完成A区医疗物资搬迁", "responsible": "仓储方", "deadline": "3天内", "priority": "high"},
        {"task": "启动紧急物资采购", "responsible": "采购部门", "deadline": "24小时内", "priority": "high"},
        {"task": "制定配送路线优化方案", "responsible": "物流方", "deadline": "5天内", "priority": "medium"},
        {"task": "建立数字化库存管理系统", "responsible": "IT部门", "deadline": "30天内", "priority": "low"},
    ],
    "risk_assessment": {
        "identified_risks": ["应急物资库存不足"],
        "mitigation_measures": ["建立物资安全库存预警机制"],
    },
}
