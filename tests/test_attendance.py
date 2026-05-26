# Author: Garam Mo
# Last Modified: 2026/05/26 by Garam Mo
#
# 역할: 참석 축(attendance.py) 단위 테스트
# 목적: 지각 허용·초과·경계값·커스텀 grace 케이스 검증

import pytest
from engine import TeamSettings
from engine.axes.attendance import calc_attendance_score
from tests.fixtures import make_member


CFG = TeamSettings()  # 기본값: grace 10%

# 회의 총 시간이 0초인 경우
# -> 참석 측정 자체가 불가능한 상황
def test_zero_meeting_time_returns_none():
    m = make_member(total_sec=0, attend_sec=0)
    assert calc_attendance_score(m, CFG) is None

# 회의 시간 전부 참석 + 지각 없음
# -> 만점
def test_full_attend_no_late():
    m = make_member(total_sec=3600, attend_sec=3600, late_sec=0)
    assert calc_attendance_score(m, CFG) == pytest.approx(1.0)

# 회의 절반만 참석 + 지각 없음
# -> 출석 0.5, 정시 1.0 / 평균 = 0.75
def test_partial_attend():
    m = make_member(total_sec=3600, attend_sec=1800, late_sec=0)
    assert calc_attendance_score(m, CFG) == pytest.approx(0.75)

# 허용 지각(360초) 절반인 180초 지각
# -> 출석 1.0, 정시 0.5 / 평균 = 0.75 
def test_late_within_grace():
    m = make_member(total_sec=3600, attend_sec=3600, late_sec=180)
    assert calc_attendance_score(m, CFG) == pytest.approx(0.75)

# 허용 지각(360초)의 2배인 720초 지각
# -> 출석 1.0, 정시 0 / 평균 = 0.5
def test_late_exceeds_grace():
    m = make_member(total_sec=3600, attend_sec=3600, late_sec=720)
    assert calc_attendance_score(m, CFG) == pytest.approx(0.5)

# 허용 지각과 딱 같은 360초 지각
# -> 정시 점수가 정확히 0
def test_late_equals_grace():
    m = make_member(total_sec=3600, attend_sec=3600, late_sec=360)
    assert calc_attendance_score(m, CFG) == pytest.approx(0.5)

# grace_ratio=0 설정 시 허용 지각이 0초
# -> 1초라도 늦으면 정시 점수 즉시 0
def test_custom_grace_ratio():
    cfg = TeamSettings(punctuality_grace_ratio=0.0)
    on_time = make_member(total_sec=3600, attend_sec=3600, late_sec=0)
    late    = make_member(total_sec=3600, attend_sec=3600, late_sec=1)
    assert calc_attendance_score(on_time, cfg) == pytest.approx(1.0)
    assert calc_attendance_score(late,    cfg) == pytest.approx(0.5)
