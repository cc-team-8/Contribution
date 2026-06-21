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


# ── 완료량(volume_score) 관련 테스트 ───────────────────────

# team_avg_completed_weight 를 안 주면(None) volume_score 는 None, score 는 기존 공식과 동일
def test_volume_none_when_no_team_avg_given():
    actions = [
        ActionItem(completed=True,  days_late=0,    difficulty=3),
        ActionItem(completed=False, days_late=None, difficulty=1),
    ]
    r = calc_task_contribution("김민준", actions)
    assert r.volume_score is None
    assert r.score == pytest.approx(0.75)  # 기존 공식과 동일 (completion 0.75, deadline 0.75)


# team_avg_completed_weight=0 (팀 전체가 0개 완료) 이면 비교 의미가 없으므로 volume 제외
def test_volume_excluded_when_team_avg_is_zero():
    actions = [ActionItem(completed=True, days_late=0, difficulty=2)]
    r = calc_task_contribution("김민준", actions, team_avg_completed_weight=0.0)
    assert r.volume_score is None


# 완료 난이도 가중 합이 팀 평균과 같으면 volume_score == 1.0
def test_volume_score_equals_team_average():
    actions = [ActionItem(completed=True, days_late=0, difficulty=2)]
    r = calc_task_contribution("김민준", actions, team_avg_completed_weight=2.0)
    assert r.volume_score == pytest.approx(1.0)


# 팀 평균보다 많이 완료해도 volume_score 는 1.0 에서 상한
def test_volume_score_capped_at_one():
    actions = [ActionItem(completed=True, days_late=0, difficulty=3)]
    r = calc_task_contribution("김민준", actions, team_avg_completed_weight=1.0)
    assert r.volume_score == pytest.approx(1.0)


# 팀 평균의 절반만 완료하면 volume_score == 0.5
def test_volume_score_half_of_average():
    actions = [ActionItem(completed=True, days_late=0, difficulty=1)]
    r = calc_task_contribution("김민준", actions, team_avg_completed_weight=2.0)
    assert r.volume_score == pytest.approx(0.5)


# completed_weight 가 완료한 액션의 난이도 합과 정확히 일치하는지
def test_completed_weight_sums_only_completed_difficulty():
    actions = [
        ActionItem(completed=True,  difficulty=3),
        ActionItem(completed=True,  difficulty=1),
        ActionItem(completed=False, difficulty=2),
    ]
    r = calc_task_contribution("김민준", actions, team_avg_completed_weight=4.0)
    assert r.completed_weight == 4  # 3 + 1, 미완료(2)는 제외


# 핵심 회귀 테스트: "적게 받아 비율만 채운 사람"이 "더 많이·어렵게 완료한 사람"보다
# task_score 자체에서 높게 나오던 역전 현상이 기본 설정(weight_volume_in_task=0.5)에서 해소되는지
def test_volume_fixes_ratio_inversion():
    # user1: 1개 배정, 1개 완료 (난이도 2) → 완료율 100%
    user1_actions = [ActionItem(completed=True, days_late=0, difficulty=2)]
    # user2: 5개 배정, 3개 완료 (난이도 2씩) → 완료율 60%, 하지만 절대 완료량은 3배
    user2_actions = (
        [ActionItem(completed=True, days_late=0, difficulty=2) for _ in range(3)]
        + [ActionItem(completed=False, difficulty=2) for _ in range(2)]
    )
    team_avg = (2 + 6) / 2  # completed_weight: user1=2, user2=6

    r1 = calc_task_contribution("user1", user1_actions, team_avg_completed_weight=team_avg)
    r2 = calc_task_contribution("user2", user2_actions, team_avg_completed_weight=team_avg)

    # 수정 전이었다면 r1.score(1.0) > r2.score(0.6) 로 역전됐었음
    assert r2.score >= r1.score


# weight_volume_in_task 를 0으로 주면(완료량 미반영) 기존 비율 전용 공식과 동일
def test_weight_volume_zero_matches_legacy_formula():
    actions = [
        ActionItem(completed=True,  days_late=0,    difficulty=3),
        ActionItem(completed=False, days_late=None, difficulty=1),
    ]
    cfg_no_volume = TeamSettings(weight_volume_in_task=0.0)
    r_with_avg = calc_task_contribution(
        "김민준", actions, cfg_no_volume, team_avg_completed_weight=10.0
    )
    r_legacy = calc_task_contribution("김민준", actions)  # team_avg_completed_weight=None
    assert r_with_avg.score == pytest.approx(r_legacy.score)