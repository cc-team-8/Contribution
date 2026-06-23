# Author: Garam Mo
# Last Modified: 2026/06/01 by Garam Mo
#
# 역할: 단일 회의 기여도(scores/meeting.py) 테스트
# 목적: 정상·결석·저참여·가중치 재분배·신뢰도 케이스 검증

import pytest
from engine import TeamSettings
from engine.scores.meeting import calc_meeting_score
from tests.fixtures import make_member


CFG = TeamSettings()


# 정상 참여 → 기여도가 0~1 범위
def test_normal_in_range():
    r = calc_meeting_score(make_member())
    assert 0.0 <= r.meeting_contribution <= 1.0


# 60분 회의 + 2축 측정 + 손실 없음 → 신뢰도 High
def test_reliability_high():
    r = calc_meeting_score(make_member(total_sec=3600, audio_loss=0.0))
    assert r.reliability.value == "High"


# 완전 결석 → 즉시 0점, absent=True
def test_absent_returns_zero():
    r = calc_meeting_score(make_member(absent=True))
    assert r.meeting_contribution == 0.0
    assert r.absent is True
    assert r.speech_score is None


# 발언 없음 → speech 축 제외, 가중치 재분배 후 합 1.0
def test_speech_excluded_weight_redistribution():
    r = calc_meeting_score(make_member(own_chars=0, total_chars=0))
    assert r.speech_score is None
    assert "speech" not in r.weights_used
    assert sum(r.weights_used.values()) == pytest.approx(1.0)


# 최소 참여 기준 미달(33%) → 저참여 플래그 + 발언 점수와 무관하게 즉시 0점
def test_low_attend_flag_and_penalty():
    full = calc_meeting_score(make_member(total_sec=3600, attend_sec=3600))
    low  = calc_meeting_score(make_member(total_sec=3600, attend_sec=1200))
    assert low.low_attend_flag is True
    assert low.meeting_contribution == 0.0
    assert low.meeting_contribution < full.meeting_contribution


# 최소 참여 기준 미달이어도 발언을 몰아서 해 speech_score가 만점이면 점수가
# 새지 않고 그대로 0점이어야 한다 (예전엔 speech 쪽에 점수가 새서 0.9까지 나왔던 버그)
def test_low_attend_overrides_high_speech_score():
    r = calc_meeting_score(make_member(
        total_sec=1800, attend_sec=360,  # 20% 출석, 기준(40%) 미달
        own_chars=500, utterance_count=5, total_chars=500, team_size=1,
    ))
    assert r.low_attend_flag is True
    assert r.meeting_contribution == 0.0
    assert r.weights_used == {}


# 출석 기준 충족(정확히 min_attend_ratio) → 0점 처리 안 되고 정상 계산
def test_attend_exactly_at_minimum_not_penalized():
    cfg = TeamSettings(min_attend_ratio=0.4)
    r = calc_meeting_score(
        make_member(total_sec=1800, attend_sec=720),  # 정확히 40%
        cfg,
    )
    assert r.low_attend_flag is False
    assert r.meeting_contribution > 0.0


# 10분 회의 → 신뢰도 Low
def test_reliability_short_meeting():
    r = calc_meeting_score(make_member(total_sec=600, attend_sec=600))
    assert r.reliability.value == "Low"


# 오디오 손실 25% → 신뢰도 Low
def test_reliability_high_audio_loss():
    r = calc_meeting_score(make_member(audio_loss=25.0))
    assert r.reliability.value == "Low"


# 비정규 회의 플래그가 결과에 그대로 전달되는지
def test_unofficial_meeting_flag_passed():
    r = calc_meeting_score(make_member(is_official=False))
    assert r.is_official is False


# 사유 결석 플래그가 결과에 그대로 전달되는지
def test_excused_absence_flag_passed():
    r = calc_meeting_score(make_member(absent=True, excused=True))
    assert r.excused_absence is True