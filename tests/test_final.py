# Author: Garam Mo
# Last Modified: 2026/06/01 by Garam Mo
#
# 역할: 최종 종합 기여도(scores/final.py) 테스트
# 목적: 회의+태스크 합산·가중치 재분배·팀장 보정 케이스 검증

import pytest
from engine import TeamSettings
from engine.models import CumulativeScore, TaskScore
from engine.scores.final import calc_final_score


def make_cumulative(score: float, name: str = "김민준") -> CumulativeScore:
    """테스트용 CumulativeScore 생성 헬퍼"""
    return CumulativeScore(name=name, score=score, meeting_count=3, included_count=3, excluded_count=0)


def make_task(score: float | None, name: str = "김민준") -> TaskScore:
    """테스트용 TaskScore 생성 헬퍼"""
    return TaskScore(name=name, score=score, total_actions=3, completed_actions=2)


CFG = TeamSettings()  # weight_task_in_final=0.50


# 회의 0.6 + 태스크 0.8, 50:50 → 최종 0.7
def test_equal_weight_average():
    r = calc_final_score(make_cumulative(0.6), make_task(0.8), CFG)
    assert r.final == pytest.approx(0.7)


# 태스크 없음(None) → 가중치 재분배, 회의 점수 그대로
def test_task_none_uses_meeting_only():
    r = calc_final_score(make_cumulative(0.8), make_task(None), CFG)
    assert r.final == pytest.approx(0.8)
    assert "task" not in r.weights_used


# 회의도 태스크도 없으면 0점
def test_both_zero_returns_zero():
    r = calc_final_score(make_cumulative(0.0), make_task(None), CFG)
    # cumulative.score=0.0 은 None 이 아니라 0점 그대로
    assert r.final == pytest.approx(0.0)


# 가중치 커스텀: 태스크 70% 적용
def test_custom_task_weight():
    cfg = TeamSettings(weight_task_in_final=0.70)
    # 회의 0.4, 태스크 1.0 → 0.4×0.3 + 1.0×0.7 = 0.82
    r = calc_final_score(make_cumulative(0.4), make_task(1.0), cfg)
    assert r.final == pytest.approx(0.82)


# weights_used 합이 1.0
def test_weights_sum_to_one():
    r = calc_final_score(make_cumulative(0.6), make_task(0.8), CFG)
    assert sum(r.weights_used.values()) == pytest.approx(1.0)


# 팀장 보정: leader_bonus=0.2, final=0.6 → 0.6×1.2 = 0.72
def test_leader_bonus_multiply():
    cfg = TeamSettings(leader_bonus=0.2)
    r   = calc_final_score(make_cumulative(0.6), make_task(0.6), cfg, is_leader=True)
    # 먼저 final = (0.6+0.6)/2 = 0.6, 보정 후 0.6 × 1.2 = 0.72
    assert r.final == pytest.approx(0.72)
    assert r.leader_applied is True


# 팀장 보정 후 1.0 초과 → 1.0 상한 고정
def test_leader_bonus_capped_at_one():
    cfg = TeamSettings(leader_bonus=0.5)
    r   = calc_final_score(make_cumulative(0.9), make_task(0.9), cfg, is_leader=True)
    assert r.final <= 1.0


# leader_bonus=0 명시 시 보정 없음 → leader_applied=False
def test_no_leader_bonus():
    cfg = TeamSettings(leader_bonus=0.0)
    r = calc_final_score(make_cumulative(0.6), make_task(0.8), cfg, is_leader=True)
    assert r.leader_applied is False


# 비팀장 → leader_applied=False
def test_not_leader():
    cfg = TeamSettings(leader_bonus=0.1)
    r   = calc_final_score(make_cumulative(0.6), make_task(0.8), cfg, is_leader=False)
    assert r.leader_applied is False