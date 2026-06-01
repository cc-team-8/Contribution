# Author: Garam Mo
# Last Modified: 2026/06/01 by Garam Mo
#
# 역할: 발언 비중 축(axes/speech.py) 단위 테스트
# 목적: 글자수 상한·기대치 정규화·측정 불가 케이스 검증

import pytest
from engine import TeamSettings
from engine.axes.speech import calc_speech_score
from tests.fixtures import make_member


CFG = TeamSettings()


# 전체 발언 0 → 측정 불가 → None
def test_no_speech_returns_none():
    m = make_member(own_chars=0, total_chars=0)
    assert calc_speech_score(m, CFG) is None


# 본인 발언 0자, 다른 사람 발언 있음 → 0점
def test_zero_own_chars():
    m = make_member(own_chars=0, total_chars=500, team_size=4)
    assert calc_speech_score(m, CFG) == 0.0


# 4명 팀에서 기대치(25% = 250자/1000자) 딱 충족 → 만점
def test_meets_expected_share():
    m = make_member(own_chars=250, total_chars=1000, team_size=4)
    assert calc_speech_score(m, CFG) == pytest.approx(1.0)


# 4명 팀에서 기대치 절반(12.5%) 발언 → 0.5점
def test_half_expected_share():
    m = make_member(own_chars=125, total_chars=1000, team_size=4)
    assert calc_speech_score(m, CFG) == pytest.approx(0.5)


# 기대치 초과 발언 → 1.0 상한 고정
def test_capped_at_one():
    m = make_member(own_chars=800, total_chars=1000, team_size=4)
    assert calc_speech_score(m, CFG) == 1.0


# 혼자 발언한 경우 (1인 팀 기대치 100%) → 만점
# 혼자 발언한 경우 (1인 팀, utterance_count=2 → 상한 1000자 → own_chars=800 통과) → 만점
def test_sole_speaker():
    m = make_member(own_chars=800, total_chars=800, team_size=1, utterance_count=2)
    assert calc_speech_score(m, CFG) == 1.0


# 글자수 상한 적용: 1회 500자 상한, 발언 1회, 총 1000자 중 600자 발언
# → 상한 적용 후 500자로 캡 → 500/1000 = 50% → 4명 기대치 25% 대비 2배 → 1.0
def test_chars_limit_cap():
    cfg = TeamSettings(action_chars_limit=500)
    m   = make_member(own_chars=600, total_chars=1000, team_size=4, utterance_count=1)
    assert calc_speech_score(m, cfg) == pytest.approx(1.0)


# 상한을 늘리면 더 많은 글자수 인정
def test_chars_limit_larger_allows_more():
    cfg_tight = TeamSettings(action_chars_limit=100)
    cfg_loose = TeamSettings(action_chars_limit=1000)
    m = make_member(own_chars=500, total_chars=1000, team_size=4, utterance_count=1)
    assert calc_speech_score(m, cfg_tight) <= calc_speech_score(m, cfg_loose)