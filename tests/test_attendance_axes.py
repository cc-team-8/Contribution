# Author: Garam Mo
# Last Modified: 2026/01/01 by Garam Mo
#
# 역할: 참석 축(axes/attendance.py) 단위 테스트
# 목적: 지각 허용·초과·경계값·커스텀 grace 케이스 검증

import pytest
from engine import TeamSettings
from engine.axes.attendance import calc_attendance_score
from tests.fixtures import make_member


CFG = TeamSettings()  # 기본값: grace 10%


# 회의 총 시간이 0초 → 참석 측정 자체가 불가능한 상황
def test_zero_meeting_time_returns_none():
    m = make_member(total_sec=0, attend_sec=0)
    assert calc_attendance_score(m, CFG) is None


# 전 회의 참석 + 지각 없음 → 만점
def test_full_attend_no_late():
    m = make_member(total_sec=3600, attend_sec=3600, late_sec=0)
    assert calc_attendance_score(m, CFG) == pytest.approx(1.0)


# 회의 절반만 참석 + 지각 없음 → 출석 0.5, 정시 1.0 → 평균 0.75
def test_partial_attend():
    m = make_member(total_sec=3600, attend_sec=1800, late_sec=0)
    assert calc_attendance_score(m, CFG) == pytest.approx(0.75)


# 허용 지각(360초) 절반인 180초 지각 → 정시 점수 0.5, 출석 1.0 → 평균 0.75
def test_late_within_grace():
    m = make_member(total_sec=3600, attend_sec=3600, late_sec=180)
    assert calc_attendance_score(m, CFG) == pytest.approx(0.75)


# 허용 지각(360초)의 2배인 720초 지각 → 정시 점수 0, 출석 1.0 → 평균 0.5
def test_late_exceeds_grace():
    m = make_member(total_sec=3600, attend_sec=3600, late_sec=720)
    assert calc_attendance_score(m, CFG) == pytest.approx(0.5)


# 허용 지각과 딱 같은 360초 지각 → 정시 점수 정확히 0.0 이 되는 경계값
def test_late_equals_grace():
    m = make_member(total_sec=3600, attend_sec=3600, late_sec=360)
    assert calc_attendance_score(m, CFG) == pytest.approx(0.5)


# grace_ratio=0 → 1초라도 지각하면 정시 점수 즉시 0
def test_custom_grace_ratio_zero():
    cfg     = TeamSettings(punctuality_grace_ratio=0.0)
    on_time = make_member(total_sec=3600, attend_sec=3600, late_sec=0)
    late    = make_member(total_sec=3600, attend_sec=3600, late_sec=1)
    assert calc_attendance_score(on_time, cfg) == pytest.approx(1.0)
    assert calc_attendance_score(late,    cfg) == pytest.approx(0.5)


# --- 신 방식(절대 시간 기준): late_threshold_sec 설정 시 ---

ABS_CFG = TeamSettings(late_threshold_sec=300, late_max_sec=600)  # 기준 5분, 최대 인정 10분


# 지각 기준(5분) 이내 → 지각 감점 없음(만점)
def test_absolute_within_threshold():
    m = make_member(total_sec=1800, attend_sec=1800, late_sec=200)
    assert calc_attendance_score(m, ABS_CFG) == pytest.approx(1.0)


# 지각 기준과 정확히 같은 300초 → 아직 만점 (경계값, 기준 "이하"는 안전)
def test_absolute_equals_threshold():
    m = make_member(total_sec=1800, attend_sec=1800, late_sec=300)
    assert calc_attendance_score(m, ABS_CFG) == pytest.approx(1.0)


# 기준(5분)~최대 인정(10분) 구간 중간(7.5분) → 정시 0.5, 출석 1.0 → 평균 0.75
def test_absolute_linear_midpoint():
    m = make_member(total_sec=1800, attend_sec=1800, late_sec=450)
    assert calc_attendance_score(m, ABS_CFG) == pytest.approx(0.75)


# 최대 인정 시간(10분)과 정확히 같음 → 정시 점수 0 (경계값)
def test_absolute_equals_max():
    m = make_member(total_sec=1800, attend_sec=1800, late_sec=600)
    assert calc_attendance_score(m, ABS_CFG) == pytest.approx(0.5)


# 최대 인정 시간 초과 → 정시 점수 0 (그 이상 늦어도 더 깎이지 않고 0 유지)
def test_absolute_exceeds_max():
    m1 = make_member(total_sec=1800, attend_sec=1800, late_sec=700)
    m2 = make_member(total_sec=1800, attend_sec=1800, late_sec=3600)
    assert calc_attendance_score(m1, ABS_CFG) == pytest.approx(0.5)
    assert calc_attendance_score(m2, ABS_CFG) == pytest.approx(0.5)


# late_max_sec 미설정(상한 없음) → 기준 초과 시 0으로 뚝 떨어지지 않고
# 점근적으로 계속 감점(threshold 만큼 더 늦으면 절반, 그 두 배 늦으면 1/3 ...)
def test_absolute_no_max_uses_asymptotic_decay():
    cfg = TeamSettings(late_threshold_sec=300, late_max_sec=None)
    on_time = make_member(total_sec=1800, attend_sec=1800, late_sec=300)
    plus_1x = make_member(total_sec=1800, attend_sec=1800, late_sec=600)   # +threshold
    plus_2x = make_member(total_sec=1800, attend_sec=1800, late_sec=900)   # +2*threshold
    assert calc_attendance_score(on_time, cfg) == pytest.approx(1.0)
    assert calc_attendance_score(plus_1x, cfg) == pytest.approx((1.0 + 0.5) / 2)
    assert calc_attendance_score(plus_2x, cfg) == pytest.approx((1.0 + 1/3) / 2)
    # 아무리 늦어도 0 아래로 떨어지지 않음(점근적 감쇠이므로 양수 유지)
    very_late = make_member(total_sec=1800, attend_sec=1800, late_sec=999999)
    assert calc_attendance_score(very_late, cfg) > 0.5


# late_threshold_sec 미설정(None) → 구 방식(punctuality_grace_ratio)이 그대로 적용됨
# (late_threshold_sec 가 없으면 절대시간 기준 신 방식은 비활성)
def test_legacy_ratio_mode_when_threshold_unset():
    cfg = TeamSettings(punctuality_grace_ratio=0.1)  # late_threshold_sec 기본 None
    m = make_member(total_sec=3600, attend_sec=3600, late_sec=180)
    # 구 방식 그대로: grace_sec=360, late_sec=180 → punct_score=0.5 → 평균 0.75
    assert calc_attendance_score(m, cfg) == pytest.approx(0.75)


# --- 사유 지각(excused_late) ---

# excused_late=True → 신 방식이어도 지각 감점(정시 점수) 완전 면제 → 출석 비율과만 평균
def test_excused_late_waives_punct_score_absolute_mode():
    m = make_member(total_sec=1800, attend_sec=1800, late_sec=3600, excused_late=True)
    assert calc_attendance_score(m, ABS_CFG) == pytest.approx(1.0)


# excused_late=True → 구 방식(비율 기반)이어도 동일하게 면제됨
def test_excused_late_waives_punct_score_legacy_mode():
    cfg = TeamSettings(punctuality_grace_ratio=0.1)
    m = make_member(total_sec=3600, attend_sec=3600, late_sec=3000, excused_late=True)
    assert calc_attendance_score(m, cfg) == pytest.approx(1.0)


# excused_late=True 라도 실제 참여 시간이 줄어든 만큼 출석 비율(attend_ratio)은
# 그대로 반영된다 — 지각에 대한 "벌점"만 면제, "함께한 시간이 짧다"는 사실은 유지
def test_excused_late_does_not_waive_attend_ratio():
    m = make_member(total_sec=1800, attend_sec=900, late_sec=900, excused_late=True)
    # punct_score=1.0(면제), attend_ratio=0.5 → 평균 0.75
    assert calc_attendance_score(m, ABS_CFG) == pytest.approx(0.75)