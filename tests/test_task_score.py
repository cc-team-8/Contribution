# Author: Garam Mo
# Last Modified: 2026/06/01 by Garam Mo
#
# 역할: 태스크 기여도(scores/task_score.py) 테스트
# 목적: 전체 기간 액션 목록 기반 계산·난이도 가중치·모드별 케이스 검증

import pytest
from engine import ActionItem, TeamSettings, MemberMeetingData
from engine.scores.task_score import calc_task_contribution, collect_actions
from tests.fixtures import make_member


# 액션이 없으면 score=None
def test_no_actions_score_is_none():
    r = calc_task_contribution("김민준", [])
    assert r.score is None
    assert r.total_actions == 0


# 모두 마감 전 완료 (difficulty=2) → 완료율 1.0, 마감 준수율 1.0 → 1.0
def test_all_perfect():
    actions = [
        ActionItem(completed=True, days_late=-1, difficulty=2),
        ActionItem(completed=True, days_late=-2, difficulty=2),
    ]
    r = calc_task_contribution("김민준", actions)
    assert r.score == pytest.approx(1.0)
    assert r.completed_actions == 2


# 모두 미완료 → 0점
def test_all_incomplete():
    actions = [
        ActionItem(completed=False, difficulty=2),
        ActionItem(completed=False, difficulty=2),
    ]
    r = calc_task_contribution("김민준", actions)
    assert r.score == pytest.approx(0.0)


# 어려운 액션(3) 완료 + 쉬운 액션(1) 미완료
# total_weight=4, completion=3/4=0.75
# deadline = (100×3 + 0×1)/4/100 = 300/4/100 = 0.75
# score = 0.75×0.5 + 0.75×0.5 = 0.75
def test_difficulty_weighting():
    actions = [
        ActionItem(completed=True,  days_late=0,    difficulty=3),
        ActionItem(completed=False, days_late=None, difficulty=1),
    ]
    r = calc_task_contribution("김민준", actions)
    assert r.score == pytest.approx(0.75)


# deadline_mode strict → normal 보다 점수 낮음 (1일 초과 액션 기준)
def test_strict_mode_lower_than_normal():
    actions = [ActionItem(completed=True, days_late=1, difficulty=2)]
    cfg_strict = TeamSettings(deadline_mode="strict")
    cfg_normal = TeamSettings(deadline_mode="normal")
    r_s = calc_task_contribution("a", actions, cfg_strict)
    r_n = calc_task_contribution("a", actions, cfg_normal)
    assert r_s.score < r_n.score


# lenient 모드 → normal 보다 점수 높음 (1일 초과 완료 액션)
def test_lenient_mode_higher_than_normal():
    actions = [ActionItem(completed=True, days_late=1, difficulty=2)]
    cfg_lenient = TeamSettings(deadline_mode="lenient")
    cfg_normal  = TeamSettings(deadline_mode="normal")
    r_l = calc_task_contribution("a", actions, cfg_lenient)
    r_n = calc_task_contribution("a", actions, cfg_normal)
    assert r_l.score > r_n.score


# completed_actions 카운트 정확한지
def test_completed_count():
    actions = [
        ActionItem(completed=True),
        ActionItem(completed=True),
        ActionItem(completed=False),
    ]
    r = calc_task_contribution("a", actions)
    assert r.total_actions == 3
    assert r.completed_actions == 2


# ── collect_actions ───────────────────────────────────────

# 회의가 없으면 빈 리스트
def test_collect_actions_no_meetings():
    result = collect_actions([])
    assert result == []


# 회의에 액션이 없으면 빈 리스트
def test_collect_actions_empty_actions():
    meetings = [make_member(), make_member()]
    assert collect_actions(meetings) == []


# 여러 회의의 액션을 하나로 합침
def test_collect_actions_multiple_meetings():
    m1 = make_member(actions=[
        ActionItem(completed=True,  days_late=-1, difficulty=2),
        ActionItem(completed=False, days_late=None, difficulty=1),
    ])
    m2 = make_member(actions=[
        ActionItem(completed=True, days_late=0, difficulty=3),
    ])
    result = collect_actions([m1, m2])
    assert len(result) == 3


# collect_actions 결과를 calc_task_contribution 에 그대로 넘길 수 있는지
def test_collect_actions_feeds_into_task_contribution():
    m1 = make_member(actions=[ActionItem(completed=True,  days_late=-1, difficulty=2)])
    m2 = make_member(actions=[ActionItem(completed=True,  days_late=0,  difficulty=2)])
    m3 = make_member(actions=[ActionItem(completed=False, days_late=None, difficulty=2)])
    actions = collect_actions([m1, m2, m3])
    r = calc_task_contribution("김민준", actions)
    assert r.total_actions == 3
    assert r.completed_actions == 2