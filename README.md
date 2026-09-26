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

**新增参数**（都是带默认值的关键字参数，不传时输出与旧版逐字符一致）：

- `deadline_base`（`datetime.date` 或 `datetime.datetime`，默认 `None`）：相对期限的换算基准。`None` 时完全不做换算、不追加任何标记，期限原样输出。其他类型按 `None` 处理，不抛异常。
- `action_item_order`（默认 `"as_is"`）：`"priority_deadline"` 时行动计划按优先级+期限排序。非法值（`"by_task"`、`None`、`123` 等）按 `"as_is"` 处理，不抛异常。

**期限换算**：认 `N小时内` / `N天内` / `N周内`（`周` 与 `星期` 等价），N 支持阿拉伯数字和中文数字（含「两」「十」组合，如 `三天内`、`两周内`、`十二小时内`）。已是 `YYYY-MM-DD` 或 `YYYY/MM/DD` 的原样输出，不二次换算。换算作用于「行动计划」和「补库计划」（紧急与常规两处）。

**跨零点算法**：`date` 基准按当日 00:00 计，`datetime` 基准按其实际时刻计；`N小时内` = 基准时刻 + N 小时后所在的日历日。例：基准 `2026-09-27`（即 00:00）时，`24小时内` → `2026-09-28`（次日），`36小时内` → `2026-09-28`（次日 12:00 所在日），`48小时内` → `2026-09-29`。`N天内` / `N周内` 即基准日 + N 天 / N×7 天。

**认不出的期限**：选「原样保留 + 追加统一标记」。`尽快`、`下个月`、`会后三天内`、`另行通知` 等渲染为 `原文（日期待确认）`，归档方可以按 `（日期待确认）` 一键筛出待人工确认的条目；缺键或空字符串渲染为占位 `（期限未明确）`。选追加标记而不是只原样保留，是因为归档件要能被下游程序化筛查，纯原文无法区分「大模型就这么写的」和「渲染方没认出来」；不丢行、不抛异常，同一输入两次渲染结果一致。标记只在传入 `deadline_base` 时追加，`None` 时原样输出（兼容底线）。

**排序口径**（`action_item_order="priority_deadline"`）：high > medium > low；`priority` 是未知值（`urgent`、`P0`、空字符串等）或缺键时排在 low 之后。同级按换算后的绝对期限升序；没传 `deadline_base` 时，同级内相对期限按时长升序（小时 < 天 < 周，同类按 N 比大小），绝对日期排在相对期限之前按日期升序，认不出的期限排最后。平局规则：优先级和期限排序键都相同（含两条都认不出）时保持原列表先后顺序——排序键显式以原下标收尾，结果确定，不依赖字典或集合的迭代顺序。排序只改顺序、不增删条目，且不修改调用方传入的列表。

**脏数据处理**（一处脏数据最多影响它自己那一行，整份纪要不抛异常）：

- `priority` 未知值或缺键：按「其余」渲染绿点 🟢，排序时排在 low 之后；
- `materials` 是字符串：当作一条物资渲染（不拆成单字）；缺键或非列表非字符串：按空列表渲染；
- 发言段 `start` 是数字字符串：按数字渲染并保留一位小数；不是数字或缺键：该行显示 `- [?s]`；
- 缺 `meeting_summary`：按空值渲染（空字符串）；缺 `action_items`：按空列表渲染，`## 六、行动计划` 标题保留；
- 缺 `vehicle_arrangement` / `distribution_strategy`、条目缺 `material_name`/`code`/`quantity`/`task`/`responsible`、zone 缺 `zone_name`/`adjustment`：渲染为占位 `（未提供）`；
- 缺 `deadline` 或空字符串：渲染为 `（期限未明确）`；
- 发言段缺 `role`：沿用原行为按「未知」处理；缺 `text`：按空字符串渲染；缺整个子字典：按空字典处理。

**测试**：`tests/` 下为纯离线测试（内存合成数据 + `tmp_path`，不联网、不调 `generate_summary`、不需要 `OPENAI_API_KEY`）。`tests/baseline_minutes.md` 是改动前用旧实现跑出的基准输出，`test_default_output_char_identical_to_baseline` 钉住逐字符兼容。验证命令：`~/venvs/gsb-warehouse/bin/python -m pytest tests/ -q`。
