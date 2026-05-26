# Author: Garam Mo
# Last Modified: 2026/05/26 by Garam Mo
#
# 역할: 태스크 완료 축(task.py) 단위 테스트
# 목적: 마감 점수 구간·완료율·측정 불가 케이스 검증

import pytest
from engine import ActionItem
from engine.axes.task import calc_task_score, _deadline_score
from tests.fixtures import make_member


# 완료된 액션의 days_late 값에 따라 스팩 점수표대로 점수가 나오는지 구간별 검증
@pytest.mark.parametrize("days_late,expected", [
    (-2,  100.0),
    (-1,  100.0),
    (0,   100.0),
    (1,    80.0),
    (3,    60.0),
    (4,    30.0),
    (7,    30.0),
    (8,     0.0),
    (100,   0.0),
])
def test_deadline_score_completed(days_late, expected):
    item = ActionItem(completed=True, days_late=days_late)
    assert _deadline_score(item) == expected

# 미완료 액션은 마감 전이어도 0점
def test_deadline_score_incomplete_is_zero():
    assert _deadline_score(ActionItem(completed=False, days_late=-1)) == 0.0

# 마감 정보가 없는 완료 액션 
# -> 만점 처리 
def test_deadline_score_no_deadline_info():
    """마감 정보 없으면 완료 시 만점"""
    assert _deadline_score(ActionItem(completed=True, days_late=None)) == 100.0


# 배정된 액션이 하나도 없는 팀원
# -> 태스크 축 측정 불가 = None 
def test_no_actions_returns_none():
    m = make_member(actions=[])
    assert calc_task_score(m) is None

# 모든 액션을 마감 전에 완료
# -> 완료율 1.0, 마감 준수율 1.0 / 태스크 만점
def test_all_perfect_returns_one():
    m = make_member(actions=[
        ActionItem(completed=True, days_late=-1),
        ActionItem(completed=True, days_late=0),
    ])
    assert calc_task_score(m) == 1.0

# 모든 액션 미완료
# -> 완료율 0, 마감 준수율 0 / 태스크 0점
def test_all_incomplete_returns_zero():
    m = make_member(actions=[
        ActionItem(completed=False),
        ActionItem(completed=False),
    ])
    assert calc_task_score(m) == 0.0

# 완료 1개, 미완료 1개
# -> 완료율 0.5, 마감 준수율 0.5 / 태스크 0.5
def test_mixed_actions():
    m = make_member(actions=[
        ActionItem(completed=True,  days_late=0),
        ActionItem(completed=False, days_late=None),
    ])
    assert calc_task_score(m) == pytest.approx(0.5)

# 단일 완료 액션의 day_late 별 태스크 점수
# -> 내부 배분 (50/50) 검증
@pytest.mark.parametrize("days_late,expected_task", [
    (-1, 1.0),
    (0,  1.0),
    (1,  0.5 + 0.5 * 0.8),
    (3,  0.5 + 0.5 * 0.6),
    (8,  0.5 + 0.5 * 0.0),
])
def test_single_action_task_score(days_late, expected_task):
    m = make_member(actions=[ActionItem(completed=True, days_late=days_late)])
    assert calc_task_score(m) == pytest.approx(expected_task)
