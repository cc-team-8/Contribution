# Author: Garam Mo
# Last Modified: 2026/05/26 by Garam Mo
#
# 역할: 종합 점수 산출(composite.py) 통합 테스트
# 목적: 가중치 재분배·저참여 하향·신뢰도 라벨·커스텀 설정 케이스 검증

import pytest
from engine import ActionItem, TeamSettings, calc_contribution
from tests.fixtures import make_member


# 기본 입력에서 종합 점수가 0~1 범위 안에 있는지 검증
def test_composite_in_range():
    assert 0.0 <= calc_contribution(make_member()).composite <= 1.0

# 60분 회의 + 3축 전부 측정 + 오디오 손실 없음
# -> 신뢰도 High
def test_reliability_high():
    r = calc_contribution(make_member(total_sec=3600, audio_loss=0.0))
    assert r.reliability.value == "High"

# 정상 참여 팀원(100% 출석)은 저참여 플래그가 붙지 않아야 한다.
def test_no_low_attend_flag_on_full_member():
    assert not calc_contribution(make_member()).low_attend_flag


# 액션이 없어 태스크 축이 None
# -> weights_used에서 제외되고 나머지 합이 1.0
def test_task_axis_excluded_when_no_actions():
    r = calc_contribution(make_member(actions=[]))
    assert r.task_score is None
    assert "task" not in r.weights_used
    assert sum(r.weights_used.values()) == pytest.approx(1.0)

# 발언이 없어 발언 축이 None
# -> weighted_used에서 제외되고 나머지 합이 1.0
def test_speech_axis_excluded_when_no_speech():
    r = calc_contribution(make_member(own_chars=0, total_chars=0))
    assert r.speech_score is None
    assert "speech" not in r.weights_used
    assert sum(r.weights_used.values()) == pytest.approx(1.0)

# 3축 모두 측정 불가
# -> 종합 점수 0점
def test_all_axes_unmeasurable_gives_zero():
    r = calc_contribution(make_member(
        total_sec=0, attend_sec=0,
        own_chars=0, total_chars=0,
        actions=[],
    ))
    assert r.composite == 0.0


# 33% 참여(기준 40% 미달)
# -> 저참여 플래그 True
def test_low_attend_flag_triggered():
    r = calc_contribution(make_member(total_sec=3600, attend_sec=1200))
    assert r.low_attend_flag  # 1200/3600 = 33% < 40%

# 태스크·발언이 동일한 조건에서 참여 시간이 짧은 쪽이 점수가 낮아야 함
def test_low_attend_reduces_score():
    full = calc_contribution(make_member(total_sec=3600, attend_sec=3600))
    low  = calc_contribution(make_member(total_sec=3600, attend_sec=1200))
    assert low.composite < full.composite

# 팀 설정으로 최소 참여 기준을 60%로 올렸을 때 50% 참여자에게 플래그 부여
def test_custom_min_attend_ratio():
    cfg = TeamSettings(min_attend_ratio=0.6)
    r = calc_contribution(
        make_member(total_sec=3600, attend_sec=1800),  # 50% < 60%
        cfg,
    )
    assert r.low_attend_flag


# 태스크 완벽 + 발언 5% 조건에서 태스크 중심 팀이 발언 중심 팀보다 점수 높음
def test_task_heavy_cfg_beats_speech_heavy():
    member = make_member(
        own_chars=50, total_chars=1000,
        actions=[ActionItem(completed=True, days_late=-1)],
    )
    cfg_task   = TeamSettings(weight_task=0.8, weight_speech=0.1, weight_attend=0.1)
    cfg_speech = TeamSettings(weight_task=0.1, weight_speech=0.8, weight_attend=0.1)
    assert calc_contribution(member, cfg_task).composite > \
           calc_contribution(member, cfg_speech).composite


# 회의 길이에 따른 신뢰도 등급 분기 검증
# 10분->Low, 20분->Medium, 60분->High
@pytest.mark.parametrize("total_sec,expected_label", [
    (600,  "Low"),    # 10분 < 15분
    (1200, "Medium"), # 20분 (15~30분)
    (3600, "High"),   # 60분
])
def test_reliability_by_meeting_length(total_sec, expected_label):
    r = calc_contribution(make_member(total_sec=total_sec, attend_sec=total_sec))
    assert r.reliability.value == expected_label

# 오디오 손실 25% (기준 20% 초과)
# -> 신뢰도 Low
def test_reliability_audio_loss_high():
    r = calc_contribution(make_member(audio_loss=25.0))
    assert r.reliability.value == "Low"

# 오디오 손실 10% (5% 초과, 20% 미만)
# -> High 조건 미달로 Medium
def test_reliability_medium_on_partial_loss():
    r = calc_contribution(make_member(audio_loss=10.0))
    assert r.reliability.value == "Medium"
