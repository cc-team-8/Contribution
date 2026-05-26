# Author: Garam Mo
# Last Modified: 2026/05/26 by Garam Mo
#
# 역할: 발언 비중 축 점수 계산 (참여 시간 보정 포함)
# 목적: 회의 내 실질적 발언 기여도를 독립적으로 측정

from typing import Optional
from engine.models import MemberMeetingData


def calc_speech_score(data: MemberMeetingData) -> Optional[float]:
    """
    함수명: calc_speech_score
    설명: 발언 비중 축 점수를 계산한다.
    입력:
     - data (MemberMeetingData): 팀원의 회의 데이터
    출력:
     - (float | None): 발언 비중 축 점수 (0~1). 전체 발언 0 일 경우 None
    """
    if data.total_chars_during <= 0:
        return None

    # 늦게 돌어오거나 일찍 나간 팀원이 불리하지 않도록 하기 위해 본인 참여 시간 내 글자수로 참여 시간을 계산.
    return min(1.0, data.own_chars / data.total_chars_during)  # 1.0 상한 적용
