# Author: Garam Mo
# Last Modified: 2026/06/01 by Garam Mo
#
# 역할: 참석 축 점수 계산 (출석 비율 + 정시 점수)
# 목적: 회의 참여 성실도를 독립적으로 측정

from typing import Optional
from engine.models import MemberMeetingData, TeamSettings


def calc_attendance_score(
    data: MemberMeetingData,
    cfg:  TeamSettings = None,
) -> Optional[float]:
    """
    함수명: calc_attendance_score
    설명: 참석 축 점수를 계산한다. 출석 비율과 정시 점수의 평균으로 산출한다.
    입력:
     - data (MemberMeetingData): 팀원의 회의 데이터
     - cfg  (TeamSettings):      팀 설정 (허용 지각 비율 참조)
    출력:
     - (float | None): 참석 축 점수 (0~1). 회의 총 시간 0 일 경우 None
    """
    # cfg를 넘지기 않으면 기본값 빠르게 호출
    if cfg is None:
        cfg = TeamSettings()
        
    if data.meeting_total_sec <= 0:
        return None

    # 출석 비율: 실제 참여 시간 / 회의 총 시간 (1.0 상한 적용)
    attend_ratio = min(1.0, data.actual_attend_sec / data.meeting_total_sec)

    # 허용 지각 한도 (초)
    grace_sec = data.meeting_total_sec * cfg.punctuality_grace_ratio

    if grace_sec <= 0:
        # grace_ratio = 0 설정 시 0 나누기 방지 → 1초라도 지각하면 바로 0점
        punct_score = 1.0 if data.late_sec == 0 else 0.0
    else:
        # 지각이 한도에 가까울수록 선형 감소, 한도 초과 시 0.0 고정
        punct_score = max(0.0, 1.0 - data.late_sec / grace_sec)

    return (attend_ratio + punct_score) / 2.0
