# Author: Garam Mo
# Last Modified: 2026/05/26 by Garam Mo
#
# 역할: 발언 비중 축(speech.py) 단위 테스트
# 목적: 정상 비율·0 입력·상한 처리 케이스 검증

import pytest
from engine.axes.speech import calc_speech_score
from tests.fixtures import make_member

# 본인 글자수와 전체 글자수 모두 0
# -> 발언 측정 자체가 불가능한 상황
def test_no_speech_returns_none():
    m = make_member(own_chars=0, total_chars=0)
    assert calc_speech_score(m) is None

# 다른 사람 발언은 있지만 본인 발언이 0자
# -> 발언 비중 0점
def test_zero_own_chars():
    m = make_member(own_chars=0, total_chars=500)
    assert calc_speech_score(m) == 0.0
    
# 4명 팀에서 기대치(25%)만큼 발언 
# → 만점
def test_meets_expected_share():
    m = make_member(own_chars=250, total_chars=1000, team_size=4)
    assert calc_speech_score(m) == pytest.approx(1.0)
 
# 4명 팀에서 기대치(25%) 절반인 12.5% 발언 
# → 0.5점
def test_below_expected_share():
    m = make_member(own_chars=125, total_chars=1000, team_size=4)
    assert calc_speech_score(m) == pytest.approx(0.5)

# 본인 글자수가 전체보다 많은 이상값
# -> 1.0 상한으로 고정
def test_capped_at_one():
    """본인 글자수가 전체보다 많아도 1.0 상한"""
    m = make_member(own_chars=1500, total_chars=1000)
    assert calc_speech_score(m) == 1.0

# 혼자 모든 발언을 한 경우
# -> 발언 비중 1.0 만점
def test_sole_speaker():
    m = make_member(own_chars=800, total_chars=800)
    assert calc_speech_score(m) == 1.0
