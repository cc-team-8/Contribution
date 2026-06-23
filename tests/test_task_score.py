# Author: Garam Mo
# Last Modified: 2026/06/21 by Garam Mo
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


# ── volume_score 제거 이후 동작 검증 ────────────────────────
#
# 과거에는 "팀 평균 완료 난이도 가중 합"과 비교하는 volume_score 축이 있어서,
# 본인이 평균만큼만 채우면(배정된 걸 다 끝내지 않았어도) 그 축이 만점이 되어
# 전체 점수가 부풀려지는 문제가 있었다. 지금은 completion_ratio(완료율)와
# deadline_avg(마감 준수율) 두 축만 50:50으로 합산하므로, 배정된 태스크를 전부
# 완료하고 마감도 다 지켜야만 1.0(100%)이 나온다.

# team_avg_completed_weight를 줘도 더 이상 영향이 없다 (계산에서 완전히 제외됨)
def test_team_avg_completed_weight_is_ignored():
    actions = [
        ActionItem(completed=True,  days_late=0,    difficulty=3),
        ActionItem(completed=False, days_late=None, difficulty=1),
    ]
    r_with_avg = calc_task_contribution("김민준", actions, team_avg_completed_weight=100.0)
    r_no_avg   = calc_task_contribution("김민준", actions)  # team_avg_completed_weight=None
    assert r_with_avg.score == pytest.approx(r_no_avg.score)
    assert r_with_avg.volume_score is None
    assert r_no_avg.volume_score is None


# 핵심 회귀 테스트: 배정된 태스크 일부만 완료(설사 팀 평균보다 많이 완료했어도)면
# 100%가 나오면 안 된다. team_avg_completed_weight를 본인의 완료량보다 낮게 줘도
# (과거 방식이었다면 만점이 됐을 상황) 여전히 100% 미달이어야 한다.
def test_partial_completion_never_hits_full_score_even_above_team_average():
    # 2개 배정, 1개만 완료(난이도2) — 평균(가정 1.0)보다 많이 완료했어도 다 끝낸 게 아님
    actions = [
        ActionItem(completed=True,  days_late=0, difficulty=2),
        ActionItem(completed=False, days_late=None, difficulty=3),
    ]
    r = calc_task_contribution("김민준", actions, team_avg_completed_weight=1.0)
    assert r.score < 1.0
    assert r.score == pytest.approx(0.4)  # completion=2/5=0.4, deadline도 2/5=0.4


# 배정된 태스크를 전부 완료 + 전부 마감 준수해야만 정확히 1.0
def test_full_completion_and_deadline_compliance_yields_full_score():
    actions = [
        ActionItem(completed=True, days_late=-1, difficulty=2),
        ActionItem(completed=True, days_late=0,  difficulty=3),
    ]
    r = calc_task_contribution("김민준", actions)
    assert r.score == pytest.approx(1.0)


# 전부 완료했지만 마감을 일부 어기면(완료는 했음) 100% 미달
def test_full_completion_but_late_yields_below_full_score():
    actions = [
        ActionItem(completed=True, days_late=2, difficulty=2),  # normal 모드 1~3일 초과 → 40점
        ActionItem(completed=True, days_late=0, difficulty=3),
    ]
    r = calc_task_contribution("김민준", actions)
    assert r.score < 1.0
    # completion=5/5=1.0(전부 완료), deadline=(40*2+100*3)/5/100=0.76 → score=(1.0+0.76)/2=0.88
    assert r.score == pytest.approx(0.88)


# 난이도가 높고 개수가 많은 태스크를 완료할수록(완료율 동일해도 절대량 비교 X,
# 다만 완료율 자체가 난이도 가중이므로) 어려운 태스크 완료가 completion_ratio에
# 더 크게 기여한다 — "난이도가 높을수록 완료 시 점수가 더 오른다"는 성질 확인.
def test_harder_task_contributes_more_to_completion_ratio():
    # 동일하게 "총 2개 중 1개 완료"인 상황에서, 완료한 쪽이 고난도냐 저난도냐로 비교
    hard_done = [
        ActionItem(completed=True,  days_late=0, difficulty=3),
        ActionItem(completed=False, days_late=None, difficulty=1),
    ]
    easy_done = [
        ActionItem(completed=True,  days_late=0, difficulty=1),
        ActionItem(completed=False, days_late=None, difficulty=3),
    ]
    r_hard = calc_task_contribution("a", hard_done)
    r_easy = calc_task_contribution("b", easy_done)
    assert r_hard.score > r_easy.score


# completed_weight 가 완료한 액션의 난이도 합과 정확히 일치하는지 (volume 제거와 무관하게 유지)
def test_completed_weight_sums_only_completed_difficulty():
    actions = [
        ActionItem(completed=True,  difficulty=3),
        ActionItem(completed=True,  difficulty=1),
        ActionItem(completed=False, difficulty=2),
    ]
    r = calc_task_contribution("김민준", actions)
    assert r.completed_weight == 4  # 3 + 1, 미완료(2)는 제외