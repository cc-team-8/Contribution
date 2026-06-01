# Author: Garam Mo
# Last Modified: 2026/06/01 by Garam Mo
#
# 역할: 태스크 완료 축(axes/task.py) 단위 테스트
# 목적: 마감 점수 구간·모드·난이도 가중치·측정 불가 케이스 검증

import pytest
from engine import ActionItem, TeamSettings
from engine.axes.task import _deadline_score
from tests.fixtures import make_member, make_action


# ── _deadline_score — normal 모드 ────────────────────────

# normal 모드에서 마감 전은 항상 100점
def test_deadline_before_due_normal():
    assert _deadline_score(make_action(days_late=-2), "normal") == 100.0

# normal 모드: 당일(d=0) → 100점
def test_deadline_same_day_normal():
    assert _deadline_score(make_action(days_late=0), "normal") == 100.0

# normal 모드: 1일 이내 초과 → 60점
@pytest.mark.parametrize("days_late", [0.5, 1.0])
def test_deadline_1day_normal(days_late):
    assert _deadline_score(make_action(days_late=days_late), "normal") == 60.0

# normal 모드: 3일 이내 초과 → 30점
@pytest.mark.parametrize("days_late", [1.5, 3.0])
def test_deadline_3day_normal(days_late):
    assert _deadline_score(make_action(days_late=days_late), "normal") == 30.0

# normal 모드: 3일 초과 → 10점
@pytest.mark.parametrize("days_late", [3.1, 7.0, 30.0])
def test_deadline_over_3day_normal(days_late):
    assert _deadline_score(make_action(days_late=days_late), "normal") == 10.0

# 미완료 액션은 모드와 관계없이 0점
def test_deadline_incomplete_always_zero():
    for mode in ("strict", "normal", "lenient"):
        assert _deadline_score(make_action(completed=False, days_late=-1), mode) == 0.0

# 마감 정보 없는 완료 액션 → 만점
def test_deadline_no_info_completed():
    assert _deadline_score(make_action(days_late=None), "normal") == 100.0


# ── _deadline_score — strict / lenient 비교 ──────────────

# strict 모드가 normal 보다 1일 초과 점수가 낮아야 함 (당일은 둘 다 100점)
def test_strict_harsher_than_normal_same_day():
    strict = _deadline_score(make_action(days_late=1), "strict")
    normal = _deadline_score(make_action(days_late=1), "normal")
    assert strict < normal

# lenient 모드가 normal 보다 1일 초과 점수가 높아야 함
def test_lenient_easier_than_normal_1day():
    lenient = _deadline_score(make_action(days_late=1), "lenient")
    normal  = _deadline_score(make_action(days_late=1), "normal")
    assert lenient > normal


# ── calc_task_score ───────────────────────────────────────

# calc_task_score 는 axes 레벨 함수 - MemberMeetingData 에 actions 없어
# 태스크 기여도 테스트는 test_task_score.py 에서 전담
# 여기서는 _deadline_score 의 모드별 동작만 확인
def test_deadline_mode_comparison():
    # 1일 초과 기준 strict < normal < lenient (당일은 모두 100점)
    item = ActionItem(completed=True, days_late=1, difficulty=2)
    s = _deadline_score(item, "strict")
    n = _deadline_score(item, "normal")
    l = _deadline_score(item, "lenient")
    assert s < n <= l