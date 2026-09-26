# -*- coding: utf-8 -*-
"""generate_meeting_minutes 的离线测试：只用内存合成数据，不联网、不调 generate_summary。"""
import copy
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.core.meeting_summarizer import MeetingSummarizer  # noqa: E402
from sample_data import SAMPLE_SEGMENTS, SAMPLE_SUMMARY  # noqa: E402

BASELINE_PATH = Path(__file__).resolve().parent / "baseline_minutes.md"


@pytest.fixture()
def summarizer():
    # OPENAI_API_KEY 为空字符串时即可构造，不联网
    return MeetingSummarizer()


@pytest.fixture()
def summary():
    return copy.deepcopy(SAMPLE_SUMMARY)


@pytest.fixture()
def segments():
    return copy.deepcopy(SAMPLE_SEGMENTS)


def action_lines(minutes):
    section = minutes.split("## 六、行动计划", 1)[1]
    return [line for line in section.splitlines() if line.startswith("- ")]


def tasks_in_order(minutes):
    return [re.match(r"- \S+ (.*?) \| 负责：", line).group(1) for line in action_lines(minutes)]


# ---------- 兼容性：不传新参数时逐字符一致 ----------

def test_default_output_char_identical_to_baseline(summarizer, segments, summary):
    baseline = BASELINE_PATH.read_text(encoding="utf-8")
    assert summarizer.generate_meeting_minutes(segments, summary) == baseline


def test_return_type_is_str(summarizer, segments, summary):
    assert isinstance(summarizer.generate_meeting_minutes(segments, summary), str)


def test_render_is_deterministic(summarizer, segments, summary):
    kwargs = {"deadline_base": date(2026, 9, 27), "action_item_order": "priority_deadline"}
    first = summarizer.generate_meeting_minutes(segments, summary, **kwargs)
    second = summarizer.generate_meeting_minutes(segments, summary, **kwargs)
    assert first == second


# ---------- deadline_base ----------

def test_deadline_base_none_keeps_relative_verbatim(summarizer, segments, summary):
    out = summarizer.generate_meeting_minutes(segments, summary, deadline_base=None)
    assert "截止：3天内" in out
    assert "期限：24小时内" in out
    assert "日期待确认" not in out


def test_relative_deadlines_converted_in_all_three_sections(summarizer, segments, summary):
    out = summarizer.generate_meeting_minutes(segments, summary, deadline_base=date(2026, 9, 27))
    # 行动计划
    assert "截止：2026-09-30" in out  # 3天内
    # 紧急补库
    assert "期限：2026-09-28" in out  # 24小时内
    # 常规补库
    assert "期限：2026-10-27" in out  # 30天内


def test_chinese_numeral_deadlines(summarizer, segments, summary):
    summary["action_items"] = [
        {"task": "甲", "responsible": "A", "deadline": "三天内", "priority": "high"},
        {"task": "乙", "responsible": "B", "deadline": "两周内", "priority": "high"},
        {"task": "丙", "responsible": "C", "deadline": "十二小时内", "priority": "high"},
    ]
    out = summarizer.generate_meeting_minutes(segments, summary, deadline_base=date(2026, 9, 27))
    assert "截止：2026-09-30" in out
    assert "截止：2026-10-11" in out
    assert "截止：2026-09-27" in out


def test_hours_cross_midnight(summarizer, segments, summary):
    summary["action_items"] = [
        {"task": "t24", "responsible": "A", "deadline": "24小时内", "priority": "high"},
        {"task": "t36", "responsible": "B", "deadline": "36小时内", "priority": "high"},
        {"task": "t48", "responsible": "C", "deadline": "48小时内", "priority": "high"},
    ]
    # date 基准按当日 00:00 计：24h -> 次日，36h -> 次日，48h -> 第三日
    out = summarizer.generate_meeting_minutes(segments, summary, deadline_base=date(2026, 9, 27))
    tasks = tasks_in_order(out)
    deadlines = {t: re.search(r"截止：(\S+)", l).group(1) for t, l in zip(tasks, action_lines(out))}
    assert deadlines["t24"] == "2026-09-28"
    assert deadlines["t36"] == "2026-09-28"
    assert deadlines["t48"] == "2026-09-29"
    # datetime 基准按实际时刻计：20:00 + 6h 跨零点落次日
    summary["action_items"] = [
        {"task": "t6", "responsible": "A", "deadline": "6小时内", "priority": "high"},
    ]
    out = summarizer.generate_meeting_minutes(
        segments, summary, deadline_base=datetime(2026, 9, 27, 20, 0))
    assert "截止：2026-09-28" in out


def test_absolute_deadline_not_reconverted(summarizer, segments, summary):
    summary["action_items"] = [
        {"task": "甲", "responsible": "A", "deadline": "2026-10-01", "priority": "high"},
        {"task": "乙", "responsible": "B", "deadline": "2026/10/05", "priority": "high"},
    ]
    out = summarizer.generate_meeting_minutes(segments, summary, deadline_base=date(2026, 9, 27))
    assert "截止：2026-10-01" in out
    assert "截止：2026/10/05" in out


def test_unrecognized_deadline_marked_not_raised(summarizer, segments, summary):
    summary["action_items"] = [
        {"task": "甲", "responsible": "A", "deadline": "尽快", "priority": "high"},
        {"task": "乙", "responsible": "B", "deadline": "会后三天内", "priority": "high"},
        {"task": "丙", "responsible": "C", "deadline": "", "priority": "high"},
        {"task": "丁", "responsible": "D", "priority": "high"},  # 缺 deadline 键
    ]
    out = summarizer.generate_meeting_minutes(segments, summary, deadline_base=date(2026, 9, 27))
    assert "截止：尽快（日期待确认）" in out
    assert "截止：会后三天内（日期待确认）" in out
    assert out.count("截止：（期限未明确）") == 2
    assert len(action_lines(out)) == 4  # 不丢行


# ---------- action_item_order ----------

def test_order_as_is_default(summarizer, segments, summary):
    out = summarizer.generate_meeting_minutes(segments, summary)
    assert tasks_in_order(out) == [a["task"] for a in SAMPLE_SUMMARY["action_items"]]


def _unordered_summary(summary):
    summary["action_items"] = [
        {"task": "低-晚", "responsible": "A", "deadline": "30天内", "priority": "low"},
        {"task": "中-早", "responsible": "B", "deadline": "5天内", "priority": "medium"},
        {"task": "高-晚", "responsible": "C", "deadline": "7天内", "priority": "high"},
        {"task": "未知优先级", "responsible": "D", "deadline": "1天内", "priority": "urgent"},
        {"task": "高-早", "responsible": "E", "deadline": "24小时内", "priority": "high"},
        {"task": "缺优先级", "responsible": "F", "deadline": "2天内"},
    ]
    return summary


def test_order_priority_deadline_with_base(summarizer, segments, summary):
    summary = _unordered_summary(summary)
    out = summarizer.generate_meeting_minutes(
        segments, summary, deadline_base=date(2026, 9, 27),
        action_item_order="priority_deadline")
    assert tasks_in_order(out) == ["高-早", "高-晚", "中-早", "低-晚", "未知优先级", "缺优先级"]


def test_order_priority_deadline_without_base(summarizer, segments, summary):
    # 没传 deadline_base：同级相对期限按时长升序（小时 < 天 < 周，同类按 N）
    summary["action_items"] = [
        {"task": "两周", "responsible": "A", "deadline": "两周内", "priority": "high"},
        {"task": "三天", "responsible": "B", "deadline": "3天内", "priority": "high"},
        {"task": "一天", "responsible": "C", "deadline": "1天内", "priority": "high"},
        {"task": "十二小时", "responsible": "D", "deadline": "12小时内", "priority": "high"},
    ]
    out = summarizer.generate_meeting_minutes(
        segments, summary, action_item_order="priority_deadline")
    assert tasks_in_order(out) == ["十二小时", "一天", "三天", "两周"]


def test_order_tie_keeps_original_relative_order(summarizer, segments, summary):
    summary["action_items"] = [
        {"task": "先", "responsible": "A", "deadline": "3天内", "priority": "high"},
        {"task": "后", "responsible": "B", "deadline": "三天内", "priority": "high"},
        {"task": "认不出甲", "responsible": "C", "deadline": "尽快", "priority": "high"},
        {"task": "认不出乙", "responsible": "D", "deadline": "另行通知", "priority": "high"},
    ]
    out = summarizer.generate_meeting_minutes(
        segments, summary, action_item_order="priority_deadline",
        deadline_base=date(2026, 9, 27))
    assert tasks_in_order(out) == ["先", "后", "认不出甲", "认不出乙"]


def test_order_preserves_multiset(summarizer, segments, summary):
    summary = _unordered_summary(summary)
    before = Counter(a["task"] for a in summary["action_items"])
    out = summarizer.generate_meeting_minutes(
        segments, summary, deadline_base=date(2026, 9, 27),
        action_item_order="priority_deadline")
    assert Counter(tasks_in_order(out)) == before
    assert len(action_lines(out)) == len(summary["action_items"])


def test_order_does_not_mutate_caller_list(summarizer, segments, summary):
    summary = _unordered_summary(summary)
    original = [a["task"] for a in summary["action_items"]]
    summarizer.generate_meeting_minutes(
        segments, summary, deadline_base=date(2026, 9, 27),
        action_item_order="priority_deadline")
    assert [a["task"] for a in summary["action_items"]] == original


@pytest.mark.parametrize("bad_order", ["by_task", None, 123, "PRIORITY_DEADLINE"])
def test_invalid_order_falls_back_to_as_is(summarizer, segments, summary, bad_order):
    out = summarizer.generate_meeting_minutes(segments, summary, action_item_order=bad_order)
    assert tasks_in_order(out) == [a["task"] for a in SAMPLE_SUMMARY["action_items"]]


# ---------- 脏数据 ----------

def test_materials_string_rendered_as_single_item(summarizer, segments, summary):
    summary["layout_adjustment"]["warehouse_zones"][0]["materials"] = "口罩"
    out = summarizer.generate_meeting_minutes(segments, summary)
    assert "**：口罩 - " in out
    assert "口, 罩" not in out


def test_numeric_string_start_formatted(summarizer, segments, summary):
    segments[0]["start"] = "12.5"
    out = summarizer.generate_meeting_minutes(segments, summary)
    assert "- [12.5s] A区货架离出库口太远" in out


def test_non_numeric_start_uses_placeholder(summarizer, segments, summary):
    segments[0]["start"] = "abc"
    del segments[1]["start"]
    out = summarizer.generate_meeting_minutes(segments, summary)
    assert "- [?s] A区货架离出库口太远" in out
    assert "- [?s] 重型物资区通道太窄" in out
    assert "仓储方" in out  # 其余行照常渲染


def test_missing_keys_do_not_crash(summarizer, segments, summary):
    del summary["meeting_summary"]
    del summary["action_items"][0]["priority"]
    del summary["layout_adjustment"]["warehouse_zones"][0]["materials"]
    del summary["logistics_suggestions"]["vehicle_arrangement"]
    out = summarizer.generate_meeting_minutes(segments, summary)
    assert "## 一、会议概述\n\n" in out  # 缺 meeting_summary 按空值渲染
    assert "- 🟢 完成A区医疗物资搬迁" in out  # 缺 priority 按绿点
    assert "**A区-医疗物资**： - 调整至靠近出库口" in out  # 缺 materials 按空列表
    assert "- 车辆安排：（未提供）" in out
    assert "## 六、行动计划" in out


def test_missing_action_items_keeps_section_header(summarizer, segments, summary):
    del summary["action_items"]
    out = summarizer.generate_meeting_minutes(segments, summary)
    assert "## 六、行动计划" in out
    assert action_lines(out) == []


def test_empty_replenishment_sublists_omitted(summarizer, segments, summary):
    summary["replenishment_plan"]["urgent_items"] = []
    summary["replenishment_plan"]["normal_items"] = []
    out = summarizer.generate_meeting_minutes(segments, summary)
    assert "### 紧急补库" not in out
    assert "### 常规补库" not in out
    assert "## 四、补库计划" in out


def test_unknown_priority_renders_green(summarizer, segments, summary):
    summary["action_items"][0]["priority"] = "P0"
    summary["action_items"][1]["priority"] = ""
    out = summarizer.generate_meeting_minutes(segments, summary)
    assert "- 🟢 完成A区医疗物资搬迁" in out
    assert "- 🟢 启动紧急物资采购" in out


def test_one_dirty_segment_does_not_break_others(summarizer, segments, summary):
    segments = segments + [
        {"start": "bad", "text": "这条 start 是脏的。", "role": "物流方"},
        {"start": 40.0, "text": "这条是正常的。", "role": "仓储方"},
    ]
    out = summarizer.generate_meeting_minutes(segments, summary)
    assert "- [?s] 这条 start 是脏的。" in out
    assert "- [40.0s] 这条是正常的。" in out
