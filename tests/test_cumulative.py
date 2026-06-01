# Author: Garam Mo
# Last Modified: 2026/06/01 by Garam Mo
#
# 역할: 회의 종합 기여도(scores/cumulative.py) 테스트
# 목적: 다중 회의 누적·결석 처리·필터링·가중 평균 케이스 검증

import pytest
from engine import TeamSettings
from engine.scores.cumulative import calc_cumulative_score
from tests.fixtures import make_meeting_score


CFG = TeamSettings()


# 회의가 없으면 0점
def test_no_meetings_returns_zero():
    r = calc_cumulative_score("김민준", [], CFG)
    assert r.score == 0.0
    assert r.included_count == 0


# 단일 회의 → 그 점수 그대로
def test_single_meeting():
    meetings = [make_meeting_score(contribution=0.8, total_sec=3600)]
    r = calc_cumulative_score("김민준", meetings, CFG)
    assert r.score == pytest.approx(0.8)
    assert r.included_count == 1


# 동일 시간 두 회의 → 단순 평균
def test_two_equal_meetings():
    meetings = [
        make_meeting_score(meeting_id="m1", contribution=0.6, total_sec=3600),
        make_meeting_score(meeting_id="m2", contribution=0.8, total_sec=3600),
    ]
    r = calc_cumulative_score("김민준", meetings, CFG)
    assert r.score == pytest.approx(0.7)


# 긴 회의에 더 큰 비중 → 가중 평균 검증
# 60분(0.6) + 30분(0.9) → (0.6×3600 + 0.9×1800) / 5400 = 3780/5400 = 0.7
def test_weighted_by_duration():
    meetings = [
        make_meeting_score(meeting_id="m1", contribution=0.6, total_sec=3600),
        make_meeting_score(meeting_id="m2", contribution=0.9, total_sec=1800),
    ]
    r = calc_cumulative_score("김민준", meetings, CFG)
    assert r.score == pytest.approx(0.7)


# 무단 결석 → 0점으로 누적에 포함
def test_unexcused_absent_included_as_zero():
    meetings = [
        make_meeting_score(meeting_id="m1", contribution=0.8, total_sec=3600),
        make_meeting_score(meeting_id="m2", contribution=0.0, total_sec=3600, absent=True, excused=False),
    ]
    r = calc_cumulative_score("김민준", meetings, CFG)
    # (0.8×3600 + 0.0×3600) / 7200 = 0.4
    assert r.score == pytest.approx(0.4)
    assert r.included_count == 2


# 사유 결석 → 누적에서 제외
def test_excused_absent_excluded():
    meetings = [
        make_meeting_score(meeting_id="m1", contribution=0.8, total_sec=3600),
        make_meeting_score(meeting_id="m2", contribution=0.0, total_sec=3600, absent=True, excused=True),
    ]
    r = calc_cumulative_score("김민준", meetings, CFG)
    assert r.score == pytest.approx(0.8)
    assert r.included_count == 1
    assert r.excluded_count == 1


# 비정규 회의 → 누적 제외
def test_unofficial_meeting_excluded():
    meetings = [
        make_meeting_score(meeting_id="m1", contribution=0.8, total_sec=3600),
        make_meeting_score(meeting_id="m2", contribution=0.2, total_sec=3600, is_official=False),
    ]
    r = calc_cumulative_score("김민준", meetings, CFG)
    assert r.score == pytest.approx(0.8)
    assert r.included_count == 1


# 최소 회의 시간(5분=300초) 미만 → 누적 제외
def test_short_meeting_excluded():
    meetings = [
        make_meeting_score(meeting_id="m1", contribution=0.8, total_sec=3600),
        make_meeting_score(meeting_id="m2", contribution=0.2, total_sec=200),  # 3분 20초
    ]
    r = calc_cumulative_score("김민준", meetings, CFG)
    assert r.score == pytest.approx(0.8)
    assert r.included_count == 1


# meeting_count는 전체 회의 수 (필터 전)
def test_meeting_count_includes_all():
    meetings = [
        make_meeting_score(meeting_id="m1", contribution=0.8, total_sec=3600),
        make_meeting_score(meeting_id="m2", contribution=0.2, total_sec=200),
    ]
    r = calc_cumulative_score("김민준", meetings, CFG)
    assert r.meeting_count == 2