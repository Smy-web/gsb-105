# 应急物资储备库会议纪要系统 · 纪要渲染子系统

## 这个仓库是什么

应急物资储备库开布局优化会，录音转写、说话人角色判定、物资编码抽取都在别的模块里做完，交给这里两样东西：一份结构化的 `summary`（大模型生成的 JSON）和一份 `merged_segments`（带角色的发言段）。`generate_meeting_minutes` 把它们渲染成 Markdown 会议纪要：一份发给应急管理局归档，一份贴到内网页面给各责任方认领任务。这里裁剪出来的就是「渲染」这一段，上游的转写、角色判定、抽取都不在范围内。

## 目录

- `backend/config.py` — 配置项，pydantic-settings，从环境变量和 `.env` 读。
- `backend/models.py` — 上下游交换的数据形状（pydantic 模型），渲染函数本身不 import 它，留着是让你看清 `summary` 应该长什么样。
- `backend/core/meeting_summarizer.py` — 本次要处理的模块。`generate_summary` 会去调 OpenAI，本任务用不到它；`_generate_mock_summary` 是它联网失败时的离线兜底，产出的就是下面这个形状的 `summary`，可以当样例数据用。

`backend` 和 `backend/core` 都没有 `__init__.py`，按命名空间包用。验证命令必须从仓库根目录、用 `-m` 的形式跑，这样仓库根才会进 `sys.path`。

## 运行环境

离线。`~/venvs/gsb-warehouse` 里只有 `requirements-task.txt` 列出来的包。openai 这个包装了，但**没有 API key，也不要设置 `OPENAI_API_KEY`**：`MeetingSummarizer()` 在 key 为空字符串时能正常构造，这正是测试想要的状态。任何测试都不要调用 `generate_summary`，它会尝试联网。

## 数据形状

`generate_meeting_minutes(merged_segments: List[dict], summary: dict) -> str`

`merged_segments` 每一项：

```json
{"start": 0.0, "end": 4.2, "text": "A区货架离出库口太远。", "role": "仓储方"}
```

`summary` 的完整形状（键名来自 `backend/models.py` 里的 `MeetingSummary`）：

```json
{
  "meeting_summary": "字符串",
  "layout_adjustment": {
    "current_problems": ["字符串"],
    "optimization_suggestions": ["字符串"],
    "warehouse_zones": [{"zone_name": "A区-医疗物资", "materials": ["口罩"], "adjustment": "前移"}]
  },
  "replenishment_plan": {
    "urgent_items": [{"material_name": "医用口罩", "code": "EMG-MED-001", "quantity": "5000只", "deadline": "24小时内"}],
    "normal_items": [{"material_name": "帐篷", "code": "EMG-LIF-004", "quantity": "80顶", "deadline": "30天内"}],
    "procurement_priority": ["医疗物资"]
  },
  "logistics_suggestions": {
    "transport_routes": ["字符串"],
    "distribution_strategy": "字符串",
    "vehicle_arrangement": "字符串"
  },
  "action_items": [{"task": "完成A区搬迁", "responsible": "仓储方", "deadline": "3天内", "priority": "high"}],
  "risk_assessment": {"identified_risks": ["字符串"], "mitigation_measures": ["字符串"]}
}
```

`priority` 在系统里的取值是 `high` / `medium` / `low`，但上游是大模型，实际会混进 `urgent`、`P0`、空字符串和缺键。`deadline` 现在全是「24小时内」「3天内」「7天内」「30天内」这类相对说法。

## 渲染出来的章节结构（下游按这个抓）

邮件渲染和内网页面都按中文序号标题定位段落，标题文字与顺序不能动：

1. `# 应急物资储备库布局优化会议纪要`
2. `## 一、会议概述`
3. `## 二、参会人员发言` — 责任方变化时插一个 `### <role>：` 小标题，每条发言一行 `- [<start 保留一位小数>s] <text>`
4. `## 三、布局调整方案` — 现存问题、优化建议，再加子标题 `### 仓库区域调整`
5. `## 四、补库计划` — 子标题 `### 紧急补库`、`### 常规补库`，对应列表为空时整个子标题连内容一起省略
6. `## 五、物流建议`
7. `## 六、行动计划` — 每条一行，行首是表示优先级的彩色圆点符号（high 红、medium 黄、其余绿），后面跟任务、负责方、截止时间；列表为空时标题仍然保留

## 已定口径与自定口径

上面几节是系统已经定死的口径。除此之外还有若干处需要你自己拿主意（跨零点怎么算、认不出来的期限怎么处理、排序的平局规则、脏数据用什么占位），定了就写进下面这一节，评审看这里。

### 本次做题人填写

（把你的取舍和理由写在这里。）
